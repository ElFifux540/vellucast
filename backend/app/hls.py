"""
Transcodage HLS à la volée pour le streaming web.

Le streaming direct (streaming.py) sert le fichier brut via HTTP Range : parfait
quand le navigateur sait lire le codec (MP4 H.264/AAC). Mais une grande partie des
fichiers d'une médiathèque auto-hébergée sont des MKV en H.265/HEVC, AC3, etc., que
les navigateurs ne savent pas décoder nativement.

Ce module comble ce manque : lorsque ``stream_transcode_enabled`` est actif et que
le média n'est pas lisible directement, FFmpeg transcode/remuxe en direct vers du
HLS (segments .ts + playlist .m3u8) consommable par hls.js côté client.

Architecture :
  * Une « session » = un dossier temporaire + un processus FFmpeg produisant des
    segments HLS au fil de l'eau (``-hls_playlist_type event``).
  * Les sessions sont mises en cache par (content_id, profil) et réutilisées.
  * Un « reaper » périodique ferme FFmpeg et supprime le dossier après inactivité.

Limite connue (assumée pour ce TFE) : le seek au-delà des segments déjà produits
attend leur génération (transcodage séquentiel). Le découpage VOD par plages serait
l'évolution naturelle (cf. accélération matérielle GPU au chapitre Évolutions).
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import tempfile
import time
from pathlib import Path

from .transcoder import FFMPEG, FFPROBE, _ensure_path_allowed

logger = logging.getLogger(__name__)

# Codecs lisibles nativement par les navigateurs (lecture directe possible).
BROWSER_VIDEO_CODECS = {"h264", "avc", "avc1"}
BROWSER_AUDIO_CODECS = {"aac", "mp3"}
BROWSER_CONTAINERS = {".mp4", ".m4v", ".mov"}

HLS_SEGMENT_SECONDS = 6  # durée d'un segment HLS
SESSION_IDLE_TIMEOUT_SEC = 120          # session fermée après 2 min sans accès
REAPER_INTERVAL_SEC = 30
PLAYLIST_WAIT_TIMEOUT_SEC = 30          # délai max d'apparition de la 1re playlist
PLAYLIST_POLL_INTERVAL_SEC = 0.25

# Profils de qualité indexés sur stream_transcode_preset ("1".."5").
# (preset x264, crf, hauteur max). Plus le numéro est haut, meilleure est la qualité.
_QUALITY_PROFILES: dict[str, tuple[str, int, int | None]] = {
    "1": ("ultrafast", 28, 480),
    "2": ("veryfast", 26, 720),
    "3": ("fast", 23, 1080),     # défaut
    "4": ("medium", 21, 1080),
    "5": ("slow", 20, None),     # qualité source (pas de downscale)
}


def _profile_for_preset(preset: str | int | None) -> tuple[str, int, int | None]:
    return _QUALITY_PROFILES.get(str(preset).strip(), _QUALITY_PROFILES["3"])


class HLSSession:
    """Une session de transcodage HLS (un dossier temporaire + un process FFmpeg)."""

    def __init__(self, content_id: str, src_path: str, preset: str) -> None:
        self.content_id = content_id
        self.src_path = src_path
        self.preset = str(preset)
        self.dir = tempfile.mkdtemp(prefix=f"vellucast_hls_{content_id}_")
        self.playlist_path = os.path.join(self.dir, "index.m3u8")
        self.proc: asyncio.subprocess.Process | None = None
        self.last_access = time.monotonic()
        self._start_lock = asyncio.Lock()

    def touch(self) -> None:
        self.last_access = time.monotonic()

    @property
    def is_idle(self) -> bool:
        return (time.monotonic() - self.last_access) > SESSION_IDLE_TIMEOUT_SEC

    def _build_cmd(self) -> list[str]:
        x264_preset, crf, max_height = _profile_for_preset(self.preset)
        cmd = [
            FFMPEG,
            "-hide_banner",
            "-loglevel", "error",
            "-y",
            "-i", self.src_path,
            "-map", "0:v:0",
            "-map", "0:a:0?",
            "-c:v", "libx264",
            "-preset", x264_preset,
            "-crf", str(crf),
            "-profile:v", "high",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "128k",
            "-ac", "2",
        ]
        # Downscale conditionnel (n'agrandit jamais : min(ih, hauteur)).
        if max_height is not None:
            cmd += ["-vf", f"scale=-2:'min({max_height},ih)'"]
        cmd += [
            "-f", "hls",
            "-hls_time", str(HLS_SEGMENT_SECONDS),
            "-hls_playlist_type", "event",
            "-hls_flags", "independent_segments+temp_file",
            "-hls_segment_filename", os.path.join(self.dir, "seg%05d.ts"),
            "-start_number", "0",
            self.playlist_path,
        ]
        return cmd

    async def ensure_started(self) -> None:
        """Démarre FFmpeg (idempotent) et attend l'apparition de la 1re playlist."""
        async with self._start_lock:
            if self.proc is None or self.proc.returncode is not None:
                if self.proc is None:
                    cmd = self._build_cmd()
                    logger.info("HLS start content=%s preset=%s", self.content_id, self.preset)
                    self.proc = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    asyncio.create_task(self._log_stderr())

        # Attend que la playlist existe et contienne au moins un segment.
        waited = 0.0
        while waited < PLAYLIST_WAIT_TIMEOUT_SEC:
            if os.path.isfile(self.playlist_path) and os.path.getsize(self.playlist_path) > 0:
                return
            if self.proc and self.proc.returncode not in (None, 0):
                raise RuntimeError("FFmpeg s'est arrêté avant de produire la playlist HLS")
            await asyncio.sleep(PLAYLIST_POLL_INTERVAL_SEC)
            waited += PLAYLIST_POLL_INTERVAL_SEC
        raise TimeoutError("Délai dépassé en attendant la playlist HLS")

    async def _log_stderr(self) -> None:
        if not self.proc or self.proc.stderr is None:
            return
        chunks: list[bytes] = []
        while True:
            line = await self.proc.stderr.readline()
            if not line:
                break
            chunks.append(line)
        await self.proc.wait()
        if self.proc.returncode not in (0, None):
            err = b"".join(chunks).decode(errors="replace")[:1000]
            logger.warning("HLS FFmpeg content=%s rc=%s: %s",
                           self.content_id, self.proc.returncode, err)

    def read_playlist(self) -> str:
        with open(self.playlist_path, "r", encoding="utf-8") as f:
            return f.read()

    def segment_path(self, name: str) -> str | None:
        """Chemin absolu d'un segment, après contrôle anti-traversée de répertoire."""
        candidate = os.path.normpath(os.path.join(self.dir, name))
        if os.path.commonpath([candidate, self.dir]) != os.path.normpath(self.dir):
            return None
        if not os.path.isfile(candidate):
            return None
        return candidate

    async def terminate(self) -> None:
        if self.proc and self.proc.returncode is None:
            try:
                self.proc.terminate()
                try:
                    await asyncio.wait_for(self.proc.wait(), timeout=5)
                except asyncio.TimeoutError:
                    self.proc.kill()
            except ProcessLookupError:
                pass
        shutil.rmtree(self.dir, ignore_errors=True)


class _HLSManager:
    """Cache de sessions HLS + reaper d'inactivité."""

    def __init__(self) -> None:
        self._sessions: dict[str, HLSSession] = {}
        self._lock = asyncio.Lock()
        self._reaper: asyncio.Task | None = None

    @staticmethod
    def _key(content_id: str, preset: str) -> str:
        return f"{content_id}::{preset}"

    async def get_session(self, content_id: str, src_path: str, preset: str) -> HLSSession:
        key = self._key(content_id, str(preset))
        async with self._lock:
            session = self._sessions.get(key)
            if session is None:
                session = HLSSession(content_id, src_path, str(preset))
                self._sessions[key] = session
        session.touch()
        await session.ensure_started()
        return session

    async def start_reaper(self) -> None:
        if self._reaper is None:
            self._reaper = asyncio.create_task(self._reap_loop())

    async def _reap_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(REAPER_INTERVAL_SEC)
                async with self._lock:
                    idle = [k for k, s in self._sessions.items() if s.is_idle]
                    for k in idle:
                        session = self._sessions.pop(k)
                        logger.info("HLS reap idle session %s", k)
                        await session.terminate()
        except asyncio.CancelledError:
            pass

    async def shutdown(self) -> None:
        if self._reaper:
            self._reaper.cancel()
            self._reaper = None
        async with self._lock:
            for session in self._sessions.values():
                await session.terminate()
            self._sessions.clear()


manager = _HLSManager()


async def probe_codecs(media_path: str) -> dict:
    """Retourne {video_codec, audio_codec, container} via ffprobe (valeurs ou None)."""
    proc = await asyncio.create_subprocess_exec(
        FFPROBE,
        "-v", "error",
        "-show_entries", "stream=codec_type,codec_name",
        "-of", "default=noprint_wrappers=1",
        media_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, _ = await proc.communicate()
    video_codec: str | None = None
    audio_codec: str | None = None
    current_type: str | None = None
    for line in out.decode(errors="replace").splitlines():
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if key == "codec_type":
            current_type = value
        elif key == "codec_name":
            if current_type == "video" and video_codec is None:
                video_codec = value
            elif current_type == "audio" and audio_codec is None:
                audio_codec = value
    return {
        "video_codec": video_codec,
        "audio_codec": audio_codec,
        "container": Path(media_path).suffix.lower(),
    }


async def decide_playback(media_path: str, *, transcode_enabled: bool) -> dict:
    """
    Décide entre lecture directe et HLS.

    Returns un dict ``{mode, reason, video_codec, audio_codec, container}`` où
    ``mode`` vaut ``"direct"`` ou ``"hls"``.
    """
    _ensure_path_allowed(media_path)
    container = Path(media_path).suffix.lower()

    # Transcodage désactivé : lecture brute directe, inutile de sonder (pas de ffprobe).
    if not transcode_enabled:
        return {
            "mode": "direct",
            "reason": "Transcodage désactivé (lecture brute)",
            "video_codec": None,
            "audio_codec": None,
            "container": container,
        }

    # Sonde des codecs ; si ffprobe est absent/échoue, on retombe sur la lecture directe
    # plutôt que de renvoyer une erreur 500.
    try:
        info = await probe_codecs(media_path)
    except (FileNotFoundError, NotImplementedError, OSError) as e:
        logger.warning("ffprobe indisponible (%s) — lecture directe par défaut", e)
        return {
            "mode": "direct",
            "reason": "Analyse codec indisponible (lecture directe)",
            "video_codec": None,
            "audio_codec": None,
            "container": container,
        }

    container_ok = info["container"] in BROWSER_CONTAINERS
    video_ok = (info["video_codec"] or "").lower() in BROWSER_VIDEO_CODECS
    audio_ok = info["audio_codec"] is None or (info["audio_codec"] or "").lower() in BROWSER_AUDIO_CODECS
    directly_playable = container_ok and video_ok and audio_ok

    if directly_playable:
        mode, reason = "direct", "Codec compatible navigateur"
    else:
        reason_bits = []
        if not container_ok:
            reason_bits.append(f"conteneur {info['container']}")
        if not video_ok:
            reason_bits.append(f"vidéo {info['video_codec']}")
        if not audio_ok:
            reason_bits.append(f"audio {info['audio_codec']}")
        mode = "hls"
        reason = "Transcodage requis : " + ", ".join(reason_bits)

    return {"mode": mode, "reason": reason, **info}
