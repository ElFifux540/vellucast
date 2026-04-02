"""
Worker d'optimisation média en arrière-plan (FFmpeg → MP4, archivage de l'original).

Planification selon app_settings (auto_optimize_enabled, optimize_schedule_type, plages horaires).
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import shlex
import shutil
from datetime import datetime, time
from pathlib import Path
from typing import Any

from .config import ARCHIVES_FOLDER, MEDIA_FOLDER
from .content_validation import VIDEO_EXTENSIONS
from .db import (
    get_media_folder_settings,
    get_transcoding_settings,
    list_optimizable_contents,
    log_audit,
    update_content,
)
from .transcoder import FFMPEG, _ensure_path_allowed

logger = logging.getLogger(__name__)

# Intervalle entre deux cycles du worker (secondes)
OPTIMIZER_POLL_INTERVAL_SEC = 45

# Compteur de lectures actives par chemin absolu normalisé (streaming HTTP)
_media_read_refcount: dict[str, int] = {}

_worker_task: asyncio.Task[None] | None = None


def _norm_path(p: str) -> str:
    return os.path.normpath(os.path.abspath(p))


def media_file_read_begin(path: str) -> None:
    """Appelé lorsque le streaming commence à lire un fichier média."""
    key = _norm_path(path)
    _media_read_refcount[key] = _media_read_refcount.get(key, 0) + 1


def media_file_read_end(path: str) -> None:
    """Appelé lorsque la lecture streaming d'un fichier se termine."""
    key = _norm_path(path)
    n = _media_read_refcount.get(key, 0) - 1
    if n <= 0:
        _media_read_refcount.pop(key, None)
    else:
        _media_read_refcount[key] = n


def is_media_file_busy(path: str) -> bool:
    """Indique si le fichier est en cours de lecture par le service de streaming."""
    return _norm_path(path) in _media_read_refcount


def _archives_root() -> Path | None:
    """Racine des archives : ARCHIVES_FOLDER ou MEDIA_FOLDER/archives."""
    if ARCHIVES_FOLDER:
        return Path(os.path.normpath(os.path.abspath(ARCHIVES_FOLDER)))
    if MEDIA_FOLDER and str(MEDIA_FOLDER).strip():
        return Path(os.path.normpath(os.path.abspath(MEDIA_FOLDER))) / "archives"
    return None


def _any_archived_file_with_id(archives_root: Path, content_id: str) -> bool:
    """Vérifie si un fichier nommé {id}-... existe déjà sous archives (déjà traité)."""
    if not archives_root.is_dir():
        return False
    prefix = f"{content_id}-"
    try:
        for p in archives_root.rglob("*"):
            if p.is_file() and p.name.startswith(prefix):
                return True
    except OSError as e:
        logger.warning("scan archives: %s", e)
    return False


def _compute_archive_path_for_original(
    media_abs: str,
    archives_root: Path,
    movies_folder: str,
    series_folder: str,
) -> Path:
    """
    Chemin de destination de l'original dans les archives (même nom de fichier, arborescence miroir).
    """
    p = Path(media_abs).resolve()
    mf = (movies_folder or "").strip()
    sf = (series_folder or "").strip()

    if mf:
        mf_p = Path(os.path.normpath(os.path.abspath(mf)))
        try:
            rel = p.relative_to(mf_p)
            return archives_root / "movies" / rel
        except ValueError:
            pass

    if sf:
        sf_p = Path(os.path.normpath(os.path.abspath(sf)))
        try:
            rel = p.relative_to(sf_p)
            return archives_root / "series" / rel
        except ValueError:
            pass

    if MEDIA_FOLDER and str(MEDIA_FOLDER).strip():
        root = Path(os.path.normpath(os.path.abspath(MEDIA_FOLDER)))
        try:
            rel = p.relative_to(root)
            return archives_root / rel
        except ValueError:
            pass

    return archives_root / "misc" / p.name


def _parse_hhmm(s: str) -> time | None:
    s = (s or "").strip()
    m = re.match(r"^(\d{1,2}):(\d{2})$", s)
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    if 0 <= h <= 23 and 0 <= mi <= 59:
        return time(h, mi)
    return None


def _now_in_schedule_window(
    start_t: time,
    end_t: time,
    *,
    now_local: datetime | None = None,
) -> bool:
    """True si l'heure courante est dans [start, end] (local), avec gestion du passage minuit."""
    now = now_local or datetime.now()
    t = now.time()
    if start_t <= end_t:
        return start_t <= t <= end_t
    return t >= start_t or t <= end_t


def _should_run_optimizer_now(settings: dict[str, str]) -> bool:
    """Respecte auto_optimize_enabled et la fenêtre horaire si optimize_schedule_type == scheduled."""
    if settings.get("auto_optimize_enabled") != "1":
        return False

    sched = (settings.get("optimize_schedule_type") or "upload").strip().lower()
    if sched != "scheduled":
        return True

    st = _parse_hhmm(settings.get("optimize_start_time") or "02:00")
    et = _parse_hhmm(settings.get("optimize_end_time") or "06:00")
    if st is None or et is None:
        return True
    return _now_in_schedule_window(st, et)


def _split_ffmpeg_extra(params: str) -> list[str]:
    """Découpe les arguments FFmpeg additionnels (paramètres admin)."""
    raw = (params or "").strip()
    if not raw:
        return []
    return shlex.split(raw, posix=os.name != "nt")


async def _run_ffmpeg_to_tmp(
    src: str,
    tmp_dst: str,
    ffmpeg_extra: list[str],
) -> tuple[bool, str]:
    """Exécute FFmpeg vers un fichier temporaire .tmp.mp4."""
    if ffmpeg_extra:
        cmd: list[str] = [
            FFMPEG,
            "-hide_banner",
            "-nostats",
            "-loglevel",
            "error",
            "-y",
            "-i",
            src,
            *ffmpeg_extra,
            tmp_dst,
        ]
    else:
        cmd = [
            FFMPEG,
            "-hide_banner",
            "-nostats",
            "-loglevel",
            "error",
            "-y",
            "-i",
            src,
            "-c:v",
            "libx264",
            "-preset",
            "medium",
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
            tmp_dst,
        ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError:
        return False, "Exécutable ffmpeg introuvable (PATH)"

    _, err = await proc.communicate()
    err_t = (err or b"").decode(errors="replace").strip()

    if proc.returncode != 0:
        return False, err_t or f"FFmpeg code {proc.returncode}"

    if not os.path.isfile(tmp_dst) or os.path.getsize(tmp_dst) == 0:
        return False, "Sortie FFmpeg absente ou vide"

    return True, ""


async def _optimize_one_content(row: dict[str, Any], settings: dict[str, str]) -> str:
    """
    Traite une ligne contents : FFmpeg, pause si lecture, archive, remplace, MAJ DB.
    Retourne 'next' pour essayer un autre contenu dans le cycle, 'stop' pour arrêter le cycle.
    """
    content_id = (row.get("id") or "").strip()
    media_path = row.get("media_path")
    if not content_id or not media_path:
        return "next"

    src = _norm_path(str(media_path))
    if not os.path.isfile(src):
        logger.warning("optimisation: fichier absent %s", src)
        return "next"

    try:
        _ensure_path_allowed(src)
    except ValueError as e:
        logger.warning("optimisation: chemin refusé %s (%s)", src, e)
        return "next"

    ext = Path(src).suffix.lower()
    if ext not in VIDEO_EXTENSIONS:
        return "next"

    archives_root = _archives_root()
    if archives_root is None:
        logger.warning("optimisation: ARCHIVES_FOLDER / MEDIA_FOLDER non défini, abandon")
        return "stop"

    if _any_archived_file_with_id(archives_root, content_id):
        logger.debug("optimisation: déjà archivé (id=%s), ignoré", content_id)
        return "next"

    folders = await get_media_folder_settings()
    archive_dest = _compute_archive_path_for_original(
        src,
        archives_root,
        folders.get("movies_folder") or "",
        folders.get("series_folder") or "",
    )

    src_dir = Path(src).parent
    stem = Path(src).stem
    tmp_path = src_dir / f"{stem}.tmp.mp4"
    ready_marker = src_dir / f"{stem}.tmp.mp4.ready"
    final_mp4 = src_dir / f"{stem}.mp4"

    ffmpeg_extra = _split_ffmpeg_extra(settings.get("ffmpeg_params") or "")

    if not tmp_path.is_file() or not ready_marker.is_file():
        if tmp_path.is_file():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        if ready_marker.is_file():
            try:
                ready_marker.unlink()
            except OSError:
                pass

        ok, err_msg = await _run_ffmpeg_to_tmp(src, str(tmp_path), ffmpeg_extra)
        if not ok:
            logger.error("optimisation FFmpeg échouée id=%s: %s", content_id, err_msg[:1500])
            try:
                if tmp_path.is_file():
                    tmp_path.unlink()
            except OSError:
                pass
            return "stop"

        try:
            ready_marker.write_text("ok", encoding="ascii")
        except OSError as e:
            logger.error("optimisation: écriture marqueur %s", e)
            try:
                if tmp_path.is_file():
                    tmp_path.unlink()
            except OSError:
                pass
            return "stop"
    else:
        logger.info("optimisation: reprise (tmp existant) id=%s", content_id)

    if is_media_file_busy(src):
        logger.info("optimisation: fichier en lecture, reporté id=%s", content_id)
        return "stop"

    archive_dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.move(src, archive_dest)
    except OSError as e:
        logger.error("optimisation: déplacement archive échoué id=%s: %s", content_id, e)
        return "stop"

    try:
        os.replace(str(tmp_path), str(final_mp4))
    except OSError as e:
        logger.error("optimisation: remplacement final échoué id=%s: %s — tentative restauration", content_id, e)
        try:
            shutil.move(str(archive_dest), src)
        except OSError:
            logger.critical("optimisation: restauration manuelle requise id=%s", content_id)
        return "stop"

    try:
        if ready_marker.is_file():
            ready_marker.unlink()
    except OSError:
        pass

    new_path = _norm_path(str(final_mp4))
    res = await update_content(
        content_id,
        {"media_path": new_path, "updated_by": "optimizer"},
    )
    if not res.get("ok"):
        logger.error("optimisation: MAJ DB échouée id=%s", content_id)
        return "stop"

    await log_audit(
        action="content_optimized",
        actor="optimizer",
        entity_type="content",
        entity_id=content_id,
        details={
            "archive_path": str(archive_dest),
            "new_media_path": new_path,
        },
    )
    logger.info("optimisation terminée id=%s -> %s", content_id, new_path)
    return "stop"


async def _optimizer_cycle() -> None:
    """Un passage : charge les réglages et traite au plus un contenu."""
    settings = await get_transcoding_settings()
    if not _should_run_optimizer_now(settings):
        return

    rows = await list_optimizable_contents()
    for row in rows:
        try:
            outcome = await _optimize_one_content(row, settings)
        except Exception:
            logger.exception("optimisation: erreur inattendue id=%s", row.get("id"))
            break
        if outcome == "next":
            continue
        break


async def _optimizer_loop() -> None:
    """Boucle asyncio (sans APScheduler)."""
    logger.info("Worker d'optimisation démarré (intervalle %ss)", OPTIMIZER_POLL_INTERVAL_SEC)
    while True:
        try:
            await _optimizer_cycle()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("optimisation: cycle worker")
        await asyncio.sleep(OPTIMIZER_POLL_INTERVAL_SEC)


def start_optimizer_worker() -> None:
    """Lance la tâche de fond (idempotent)."""
    global _worker_task
    if _worker_task is not None and not _worker_task.done():
        return
    _worker_task = asyncio.create_task(_optimizer_loop(), name="vellucast-optimizer")


async def stop_optimizer_worker() -> None:
    """Arrête proprement le worker (annulation)."""
    global _worker_task
    if _worker_task is None or _worker_task.done():
        return
    _worker_task.cancel()
    try:
        await _worker_task
    except asyncio.CancelledError:
        pass
    _worker_task = None
    logger.info("Worker d'optimisation arrêté")
