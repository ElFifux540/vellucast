"""
Service de transcodage MKV → MP4 (H.264 / AAC) pour diffusion web.
Lecture non bloquante des sorties FFmpeg (progression via -progress pipe:1).
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
from pathlib import Path
from typing import Any, Awaitable, Callable

from .config import MEDIA_FOLDER
from .db import get_content

logger = logging.getLogger(__name__)

# FFmpeg écrit les paires clé=valeur de progression sur stdout avec -progress pipe:1
# (out_time_ms est en microsecondes malgré le nom — voir doc FFmpeg « progress »).
FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = shutil.which("ffprobe") or "ffprobe"


def _ensure_path_allowed(abs_path: str) -> None:
    """Empêche la lecture/écriture hors du dossier média si MEDIA_FOLDER est défini."""
    if not MEDIA_FOLDER or not MEDIA_FOLDER.strip():
        return
    try:
        root = Path(MEDIA_FOLDER).resolve()
        target = Path(abs_path).resolve()
        target.relative_to(root)
    except ValueError as e:
        raise ValueError("Accès au fichier refusé (hors dossier média)") from e


async def _probe_duration_seconds(media_path: str) -> float | None:
    """Durée totale en secondes (ffprobe), ou None si indisponible."""
    proc = await asyncio.create_subprocess_exec(
        FFPROBE,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        media_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    if proc.returncode != 0:
        logger.warning("ffprobe échec: %s", err.decode(errors="replace")[:500])
        return None
    try:
        return float(out.decode().strip())
    except ValueError:
        return None


async def _drain_stderr_to_list(
    stream: asyncio.StreamReader | None,
    bucket: list[str],
) -> None:
    """Consomme stderr en continu pour éviter le blocage du tampon."""
    if stream is None:
        return
    while True:
        chunk = await stream.read(4096)
        if not chunk:
            break
        bucket.append(chunk.decode(errors="replace"))


async def _read_progress_stdout(
    stream: asyncio.StreamReader | None,
    duration_sec: float | None,
    on_progress: Callable[[dict[str, Any]], Awaitable[None]] | None,
) -> None:
    """Lit les lignes key=value envoyées par FFmpeg sur stdout (-progress pipe:1)."""
    if stream is None:
        return

    state: dict[str, str] = {}

    while True:
        line_b = await stream.readline()
        if not line_b:
            break
        line = line_b.decode(errors="replace").strip()
        if not line or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        state[key] = value

        if key == "out_time_ms":
            payload = _build_progress_payload(state, duration_sec)
            if on_progress and payload is not None:
                await on_progress(payload)

        if key == "progress" and value == "end":
            break


def _build_progress_payload(
    state: dict[str, str],
    duration_sec: float | None,
) -> dict[str, Any] | None:
    """Construit un dict de progression pour le callback (pourcentage, temps, vitesse)."""
    out_us = state.get("out_time_ms")
    if out_us is None:
        return None
    try:
        out_time_us = int(out_us)
    except ValueError:
        return None

    # out_time_ms = microsecondes (doc FFmpeg « progress »)
    current_sec = out_time_us / 1_000_000.0

    total_sec = duration_sec
    if total_sec is None or total_sec <= 0:
        raw_d = state.get("duration")
        if raw_d:
            try:
                total_sec = float(raw_d)
            except ValueError:
                total_sec = None

    percent: float | None = None
    if total_sec and total_sec > 0:
        percent = min(100.0, max(0.0, (current_sec / total_sec) * 100.0))

    speed = state.get("speed")

    return {
        "out_time_us": out_time_us,
        "current_sec": current_sec,
        "duration_sec": total_sec,
        "percent": percent,
        "speed": speed,
        "raw": dict(state),
    }


async def transcode_mkv_to_web_mp4(
    content_id: str,
    *,
    output_path: str | None = None,
    on_progress: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
) -> dict[str, Any]:
    """
    Transcode le média du contenu (MKV attendu) vers MP4 H.264/AAC, optimisé pour le web.

    - preset fast, faststart, yuv420p pour compatibilité lecteurs.
    - Progression : lecture asynchrone de stdout (-progress pipe:1) et stderr en parallèle.

    Args:
        content_id: Identifiant dans la table ``contents``.
        output_path: Chemin de sortie MP4 (défaut : même dossier que la source, même nom .mp4).
        on_progress: Coroutine appelée avec un dict (percent, current_sec, duration_sec, speed, …).

    Returns:
        ``{ok, output_path?, error?, returncode?}``
    """
    row = await get_content(content_id)
    if not row:
        return {"ok": False, "error": "Contenu introuvable"}

    media_path = row.get("media_path")
    if not media_path:
        return {"ok": False, "error": "Chemin média absent"}

    src = os.path.normpath(os.path.abspath(media_path))
    if not os.path.isfile(src):
        return {"ok": False, "error": "Fichier source introuvable sur le disque"}

    try:
        _ensure_path_allowed(src)
    except ValueError as e:
        return {"ok": False, "error": str(e)}

    if Path(src).suffix.lower() != ".mkv":
        return {"ok": False, "error": "Seuls les fichiers .mkv sont acceptés pour ce transcodage"}

    if output_path is None:
        dst = str(Path(src).with_suffix(".mp4"))
    else:
        dst = os.path.normpath(os.path.abspath(output_path))

    try:
        _ensure_path_allowed(dst)
    except ValueError as e:
        return {"ok": False, "error": str(e)}

    duration_sec = await _probe_duration_seconds(src)

    # -progress pipe:1 : progression machine sur stdout ; -nostats : moins de bruit sur stderr
    cmd = [
        FFMPEG,
        "-hide_banner",
        "-nostats",
        "-loglevel",
        "error",
        "-progress",
        "pipe:1",
        "-y",
        "-i",
        src,
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
        "-profile:v",
        "high",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        "-f",
        "mp4",
        dst,
    ]

    stderr_chunks: list[str] = []

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError:
        return {"ok": False, "error": "Exécutable ffmpeg introuvable (PATH)"}

    assert proc.stdout is not None
    assert proc.stderr is not None

    progress_task = asyncio.create_task(
        _read_progress_stdout(proc.stdout, duration_sec, on_progress),
    )
    stderr_task = asyncio.create_task(_drain_stderr_to_list(proc.stderr, stderr_chunks))

    await asyncio.gather(progress_task, stderr_task)
    returncode = await proc.wait()

    err_text = "".join(stderr_chunks).strip()

    if returncode != 0:
        logger.error("FFmpeg échec rc=%s: %s", returncode, err_text[:2000])
        return {
            "ok": False,
            "error": err_text or f"FFmpeg a échoué (code {returncode})",
            "returncode": returncode,
        }

    if not os.path.isfile(dst):
        return {"ok": False, "error": "Fichier de sortie absent après transcodage"}

    return {"ok": True, "output_path": dst, "content_id": content_id}
