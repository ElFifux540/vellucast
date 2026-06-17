"""
Recherche de fichiers et de contenus pour l'API Vellucast.

Trois portées (« scopes ») complémentaires :
  * library : recherche dans la base indexée (table contents) — voir db.search_contents.
  * disk    : recherche récursive de fichiers vidéo sous MEDIA_FOLDER (ce module).
  * external: découverte via API tierce (Overseerr/TMDb) — voir overseerr.py.

La recherche disque est exécutée dans un thread pool (asyncio.to_thread) car le
parcours de l'arborescence est une opération bloquante d'E/S.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from .config import MEDIA_FOLDER
from .content_validation import VIDEO_EXTENSIONS

# Garde-fou : nombre maximum de fichiers inspectés pour éviter de bloquer le serveur
# sur une arborescence gigantesque, et nombre maximum de résultats renvoyés.
MAX_FILES_SCANNED = 200_000
DEFAULT_DISK_LIMIT = 100
MAX_DISK_LIMIT = 500

# Dossiers ignorés pendant le parcours (générés par la plateforme).
_IGNORED_DIRS = {"archives", ".git", "__pycache__", "node_modules"}


def _media_root() -> str:
    if not MEDIA_FOLDER or not str(MEDIA_FOLDER).strip():
        raise ValueError("MEDIA_FOLDER non configuré")
    root = os.path.normpath(os.path.abspath(MEDIA_FOLDER))
    if not os.path.isdir(root):
        raise ValueError(f"Dossier média introuvable: {root}")
    return root


def _walk_for_matches(root: str, needle: str, limit: int) -> tuple[list[dict], bool, int]:
    """
    Parcours récursif synchrone. Retourne (résultats, tronqué?, fichiers_scannés).

    Un fichier correspond si sa requête (insensible à la casse) apparaît dans le nom
    de fichier OU dans le chemin relatif (utile pour chercher par nom de série/dossier).
    """
    results: list[dict] = []
    scanned = 0
    truncated = False
    needle_l = needle.lower()
    root_path = Path(root)

    for current_dir, dirnames, filenames in os.walk(root):
        # Élague les dossiers ignorés et masqués (modification en place de dirnames).
        dirnames[:] = [
            d for d in dirnames
            if d not in _IGNORED_DIRS and not d.startswith(".")
        ]

        for name in filenames:
            scanned += 1
            if scanned > MAX_FILES_SCANNED:
                return results, True, scanned

            if Path(name).suffix.lower() not in VIDEO_EXTENSIONS:
                continue

            abs_path = os.path.join(current_dir, name)
            try:
                rel_path = str(Path(abs_path).relative_to(root_path))
            except ValueError:
                rel_path = name

            haystack = rel_path.lower()
            if needle_l and needle_l not in haystack:
                continue

            try:
                size = os.path.getsize(abs_path)
            except OSError:
                size = None

            results.append(
                {
                    "name": name,
                    "path": os.path.normpath(abs_path),
                    "relative_path": rel_path,
                    "extension": Path(name).suffix.lower(),
                    "size_bytes": size,
                }
            )

            if len(results) >= limit:
                truncated = True
                return results, truncated, scanned

    return results, truncated, scanned


async def search_disk_files(query: str | None, *, limit: int = DEFAULT_DISK_LIMIT) -> dict:
    """
    Recherche récursive de fichiers vidéo (.mp4/.mkv) par nom sous MEDIA_FOLDER.

    Args:
        query: Sous-chaîne recherchée (nom de fichier ou chemin). Vide = lister tout
               (dans la limite). Insensible à la casse.
        limit: Nombre maximum de résultats (borné par MAX_DISK_LIMIT).

    Returns:
        ``{items, count, truncated, scanned, query, root}``.
    """
    try:
        limit = max(1, min(MAX_DISK_LIMIT, int(limit)))
    except (TypeError, ValueError):
        limit = DEFAULT_DISK_LIMIT

    root = _media_root()
    needle = (query or "").strip()

    items, truncated, scanned = await asyncio.to_thread(
        _walk_for_matches, root, needle, limit
    )
    items.sort(key=lambda x: x["relative_path"].lower())

    return {
        "items": items,
        "count": len(items),
        "truncated": truncated,
        "scanned": scanned,
        "query": needle,
        "root": root,
    }
