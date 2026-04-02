"""Validation des champs contenus (chemins média, titres)."""

from __future__ import annotations

import os
from pathlib import Path

from .config import MEDIA_FOLDER

VIDEO_EXTENSIONS = {".mp4", ".mkv"}


def validate_media_path_for_content(media_path: str) -> tuple[bool, str | None]:
    """
    Valide un chemin de fichier média pour création / mise à jour.
    Retourne (True, None) ou (False, message d'erreur en français).
    """
    raw = (media_path or "").strip()
    if not raw:
        return False, "Le chemin média ne peut pas être vide"

    p = os.path.normpath(os.path.abspath(raw))

    if not os.path.isfile(p):
        return False, "Le chemin média doit pointer vers un fichier existant"

    ext = Path(p).suffix.lower()
    if ext not in VIDEO_EXTENSIONS:
        return False, "Le fichier média doit être au format .mp4 ou .mkv"

    if MEDIA_FOLDER and str(MEDIA_FOLDER).strip():
        try:
            Path(p).resolve().relative_to(Path(MEDIA_FOLDER).resolve())
        except ValueError:
            return False, "Le chemin média est invalide (hors du dossier média autorisé)"

    return True, None
