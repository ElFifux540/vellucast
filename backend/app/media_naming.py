"""Nommage physique des fichiers vidéo ({id}-{stem_nettoye}.mp4|.mkv)."""

from __future__ import annotations

import re
from pathlib import Path

from .content_validation import VIDEO_EXTENSIONS


def clean_original_stem_for_filename(stem: str) -> str:
    """Nettoie le nom de fichier (sans extension) pour un usage sur disque."""
    s = (stem or "").strip()
    s = re.sub(r"[^\w\s.-]", "", s, flags=re.UNICODE)
    s = re.sub(r"\s+", "-", s).strip("-._")
    if len(s) > 120:
        s = s[:120].rstrip("-._")
    return s if s else "media"


def physical_video_filename(short_id: str, original_stem: str, original_suffix: str) -> str:
    """
    Nom de fichier : {id_court}-{nom_original_nettoye}.{mp4|mkv}
    L'extension suit le type réel (.mp4 ou .mkv).
    """
    clean = clean_original_stem_for_filename(original_stem)
    ext = (original_suffix or "").lower()
    if ext not in VIDEO_EXTENSIONS:
        ext = ".mp4"
    return f"{short_id}-{clean}{ext}"
