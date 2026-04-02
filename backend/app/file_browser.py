"""Exploration des dossiers médias côté serveur (liste non récursive)."""

from __future__ import annotations

import os
from pathlib import Path

from .config import MEDIA_FOLDER
from .content_validation import VIDEO_EXTENSIONS


def _normalize_abs(path: str) -> str:
    return os.path.normpath(os.path.abspath(path))


def _ensure_under_media_root(abs_path: str) -> None:
    if not MEDIA_FOLDER or not str(MEDIA_FOLDER).strip():
        raise ValueError("MEDIA_FOLDER non configuré")
    root = Path(MEDIA_FOLDER).resolve()
    target = Path(abs_path).resolve()
    target.relative_to(root)


def browse_media_directory(path: str | None) -> dict:
    """
    Liste le contenu d'un dossier sous MEDIA_FOLDER (non récursif).
    Dossiers : tous. Fichiers : uniquement .mp4 / .mkv.
    """
    if not MEDIA_FOLDER or not str(MEDIA_FOLDER).strip():
        raise ValueError("MEDIA_FOLDER non configuré")

    root = _normalize_abs(MEDIA_FOLDER)
    if not os.path.isdir(root):
        raise ValueError(f"Dossier média introuvable: {root}")

    if path and str(path).strip():
        target = _normalize_abs(path.strip())
    else:
        target = root

    _ensure_under_media_root(target)

    if not os.path.isdir(target):
        raise ValueError("Le chemin doit être un dossier existant")

    items: list[dict] = []
    with os.scandir(target) as it:
        for entry in it:
            name = entry.name
            if name.startswith("."):
                continue
            if entry.is_dir(follow_symlinks=False):
                items.append({"name": name, "type": "directory"})
            elif entry.is_file(follow_symlinks=False):
                ext = Path(name).suffix.lower()
                if ext in VIDEO_EXTENSIONS:
                    items.append(
                        {
                            "name": name,
                            "type": "file",
                            "extension": ext,
                        }
                    )

    def sort_key(x: dict) -> tuple[int, str]:
        # Dossiers d'abord, puis fichiers ; ordre alphabétique
        is_dir = 0 if x["type"] == "directory" else 1
        return (is_dir, x["name"].lower())

    items.sort(key=sort_key)

    parent = str(Path(target).parent)
    if Path(target).resolve() == Path(root).resolve():
        parent = None
    else:
        try:
            Path(parent).resolve().relative_to(Path(root).resolve())
        except ValueError:
            parent = None

    return {
        "path": target,
        "parent": parent,
        "items": items,
    }
