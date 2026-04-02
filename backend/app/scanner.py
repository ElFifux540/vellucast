"""Scan du dossier médias et import dans la table contents."""

from __future__ import annotations

import asyncio
import os
import re
from pathlib import Path

from .config import MEDIA_FOLDER
from .content_ids import generate_unique_content_id
from .db import create_content, get_content_by_media_path, log_audit
from .media_naming import physical_video_filename

VIDEO_EXTENSIONS = {".mp4", ".mkv"}


def _normalize_media_path(path: str) -> str:
    return os.path.normpath(os.path.abspath(path))


def _filename_to_title(filename: str) -> str:
    stem = Path(filename).stem
    s = stem.replace("_", " ").replace(".", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s if s else "Sans titre"


def _collect_video_files(root: str) -> list[str]:
    """Parcourt récursivement le dossier (appel synchrone, exécuté dans un thread)."""
    found: list[str] = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            ext = Path(name).suffix.lower()
            if ext in VIDEO_EXTENSIONS:
                found.append(os.path.join(dirpath, name))
    return sorted(found)


async def scan_media_folder(created_by: str | None) -> dict:
    """
    Scanne MEDIA_FOLDER pour les fichiers .mp4 / .mkv et crée une entrée contents
    par fichier absent de la base (déduplication par chemin absolu normalisé).
    """
    if not MEDIA_FOLDER or not MEDIA_FOLDER.strip():
        return {"ok": False, "error": "MEDIA_FOLDER non configure"}

    root = _normalize_media_path(MEDIA_FOLDER)
    if not os.path.isdir(root):
        return {"ok": False, "error": f"Dossier media introuvable: {root}"}

    paths = await asyncio.to_thread(_collect_video_files, root)
    added: list[dict] = []
    skipped: list[str] = []

    for raw_path in paths:
        abs_path = _normalize_media_path(raw_path)
        existing = await get_content_by_media_path(abs_path)
        if existing:
            skipped.append(abs_path)
            continue

        basename = os.path.basename(raw_path)
        stem = Path(basename).stem
        ext = Path(basename).suffix.lower()
        content_id = await generate_unique_content_id()
        final_name = physical_video_filename(content_id, stem, ext)
        parent_dir = os.path.dirname(abs_path)
        new_abs_path = _normalize_media_path(os.path.join(parent_dir, final_name))

        if new_abs_path != abs_path:
            if os.path.exists(new_abs_path):
                return {
                    "ok": False,
                    "error": f"Fichier cible deja present: {new_abs_path}",
                    "partial_added": len(added),
                }
            await asyncio.to_thread(os.rename, abs_path, new_abs_path)

        title = _filename_to_title(basename)
        payload = {
            "id": content_id,
            "title": title,
            "media_path": new_abs_path,
            "created_by": created_by or "media_scan",
        }
        result = await create_content(payload)
        if not result["ok"]:
            return {"ok": False, "error": result.get("error", "echec insertion"), "partial_added": len(added)}
        added.append({"id": content_id, "title": title, "media_path": new_abs_path})

    await log_audit(
        action="media_scan_completed",
        actor=created_by,
        entity_type="scanner",
        entity_id=root,
        details={
            "added_count": len(added),
            "skipped_count": len(skipped),
            "files_seen": len(paths),
        },
    )

    return {
        "ok": True,
        "root": root,
        "files_seen": len(paths),
        "added_count": len(added),
        "skipped_count": len(skipped),
        "added": added,
    }
