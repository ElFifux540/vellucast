"""
Service de stockage pour l'upload de médias.

Objectifs:
- Ecrire les fichiers par chunks (ne pas saturer la RAM)
- Créer la structure de dossiers (films vs épisodes)
- Insérer le nouveau média dans `contents`
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Final

from fastapi import UploadFile

from .config import MEDIA_FOLDER
from .content_ids import generate_unique_content_id
from .db import create_content, get_media_folder_settings
from .media_naming import physical_video_filename


CHUNK_SIZE_BYTES: Final[int] = 1024 * 1024  # 1 MiB


def _clean_path_segment(segment: str) -> str:
    """
    Nettoie un segment de chemin pour éviter les séparateurs et séquences dangereuses.
    """
    segment = (segment or "").strip()
    segment = segment.replace("\\", " ").replace("/", " ")
    segment = segment.replace("..", ".")
    segment = re.sub(r"\s+", " ", segment)
    # Retire les caractères qui posent souvent problème dans les systèmes de fichiers
    segment = re.sub(r"[^a-zA-Z0-9 _().-]", "", segment)
    return segment.strip() or "Sans titre"


def _normalize_abs_path(path: str) -> str:
    return os.path.normpath(os.path.abspath(path))


def _ensure_path_under_media_root(requested_root: str) -> str:
    """Valide que le chemin absolu reste sous MEDIA_FOLDER si celui-ci est défini."""
    if MEDIA_FOLDER and MEDIA_FOLDER.strip():
        allowed_root = _normalize_abs_path(MEDIA_FOLDER)
        try:
            Path(requested_root).resolve().relative_to(Path(allowed_root).resolve())
        except ValueError:
            raise ValueError("library_path invalide (hors du dossier MEDIA_FOLDER)")
    return requested_root


async def _resolve_library_base(media_type: str, library_path: str | None) -> str:
    """
    Détermine le dossier racine de stockage.

    Priorité :
    1) `library_path` explicite (upload)
    2) Dossiers configurés en base (films / séries)
    3) `MEDIA_FOLDER` (env)
    """
    if library_path and library_path.strip():
        requested_root = _normalize_abs_path(library_path)
        return _ensure_path_under_media_root(requested_root)

    settings = await get_media_folder_settings()
    if media_type == "movie":
        configured = (settings.get("movies_folder") or "").strip()
    else:
        configured = (settings.get("series_folder") or "").strip()

    if configured:
        requested_root = _normalize_abs_path(configured)
        return _ensure_path_under_media_root(requested_root)

    if MEDIA_FOLDER and MEDIA_FOLDER.strip():
        return _normalize_abs_path(MEDIA_FOLDER)

    raise ValueError(
        "Aucun dossier de destination : configurez MEDIA_FOLDER ou les dossiers dans les paramètres",
    )


def _filename_stem_and_suffix(upload_file: UploadFile) -> tuple[str, str]:
    raw = (upload_file.filename or "").strip()
    suffix = Path(raw).suffix.lower()
    stem = Path(raw).stem
    if not suffix:
        suffix = ".mp4"
    elif suffix not in (".mp4", ".mkv"):
        suffix = ".mp4"
    return stem, suffix


def _filename_to_title(filename: str) -> str:
    # Logique simple et cohérente avec le scanner (sans dépendre des internes).
    stem = Path(filename).stem
    s = stem.replace("_", " ").replace(".", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s if s else "Sans titre"


async def _write_upload_file_by_chunks(upload_file: UploadFile, dst_path: str) -> None:
    """
    Ecrit le fichier uploadé sur disque en mémoire bornée (lecture par chunks).
    """
    dst_tmp = f"{dst_path}.part"

    with open(dst_tmp, "wb") as f:
        while True:
            chunk = await upload_file.read(CHUNK_SIZE_BYTES)
            if not chunk:
                break
            f.write(chunk)

    os.replace(dst_tmp, dst_path)


async def store_uploaded_media(
    *,
    upload_file: UploadFile,
    media_type: str,
    library_path: str | None,
    series_name: str | None,
    season_number: int | None,
    created_by: str | None,
) -> dict:
    """
    Stocke un média et insère une entrée dans la table `contents`.
    """
    mt = (media_type or "").strip().lower()
    if mt not in {"movie", "episode"}:
        raise ValueError("type de média invalide (attendu: movie ou episode)")

    base_dir = await _resolve_library_base(mt, library_path)
    Path(base_dir).mkdir(parents=True, exist_ok=True)

    series_segment = _clean_path_segment(series_name or "")
    if mt == "episode":
        if not series_name or not series_name.strip():
            raise ValueError("series_name requis pour un épisode")
        if season_number is None:
            raise ValueError("season_number requis pour un épisode")
        if int(season_number) < 0:
            raise ValueError("season_number invalide")

    stem, suffix = _filename_stem_and_suffix(upload_file)
    content_id = await generate_unique_content_id()
    final_name = physical_video_filename(content_id, stem, suffix)

    if mt == "movie":
        target_dir = Path(base_dir)
        title = _filename_to_title(stem)
    else:
        target_dir = Path(base_dir) / series_segment / f"Season {int(season_number)}"
        title = f"{series_segment} - Saison {int(season_number)} - {_filename_to_title(stem)}"

    target_dir.mkdir(parents=True, exist_ok=True)

    dst_path = _normalize_abs_path(str(target_dir / final_name))

    await _write_upload_file_by_chunks(upload_file, dst_path)

    payload = {
        "id": content_id,
        "title": title,
        "media_path": dst_path,
        "created_by": created_by,
    }

    result = await create_content(payload)
    if not result.get("ok"):
        return {"ok": False, "error": result.get("error", "Insertion DB échouée")}

    return result

