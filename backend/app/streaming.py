"""Streaming vidéo avec support HTTP Range (206) et lecture par chunks."""

from __future__ import annotations

import asyncio
import mimetypes
import os
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.responses import Response, StreamingResponse

from .auth import verify_token
from .config import MEDIA_FOLDER
from .db import get_content
from .optimizer import media_file_read_begin, media_file_read_end

router = APIRouter(prefix="/api", tags=["stream"])

CHUNK_SIZE = 64 * 1024


def get_stream_user(request: Request) -> dict:
    """
    Auth pour le lecteur HTML5 : Accepte Authorization Bearer ou ?token= (pas d'en-tête sur <video>).
    """
    auth_header = request.headers.get("authorization", "")
    token: str | None = None
    if auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    if not token:
        token = request.query_params.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Jeton manquant")
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Jeton invalide ou expire")
    return payload


def _read_file_chunk(path: str, position: int, size: int) -> bytes:
    with open(path, "rb") as f:
        f.seek(position)
        return f.read(size)


async def _async_iter_range(path: str, start: int, end: int):
    """Lit [start, end] inclus par morceaux (async via thread pool)."""
    remaining = end - start + 1
    pos = start
    while remaining > 0:
        to_read = min(CHUNK_SIZE, remaining)
        chunk = await asyncio.to_thread(_read_file_chunk, path, pos, to_read)
        if not chunk:
            break
        yield chunk
        got = len(chunk)
        pos += got
        remaining -= got


def _parse_range_header(range_header: str | None, file_size: int) -> tuple[int, int] | None:
    """
    Retourne (start, end) inclus pour une plage unique, ou None = tout le fichier.
    Lève ValueError si la plage est invalide.
    """
    if not range_header or file_size == 0:
        return None
    if not range_header.strip().lower().startswith("bytes="):
        return None

    match = re.match(
        r"^\s*bytes=(\d*)-(\d*)\s*$",
        range_header.strip(),
        re.IGNORECASE,
    )
    if not match:
        return None

    start_s, end_s = match.group(1), match.group(2)

    if start_s == "" and end_s != "":
        suffix = int(end_s)
        if suffix <= 0:
            raise ValueError("invalid")
        start = max(0, file_size - suffix)
        end = file_size - 1
    elif start_s != "" and end_s == "":
        start = int(start_s)
        end = file_size - 1
    elif start_s != "" and end_s != "":
        start = int(start_s)
        end = int(end_s)
    else:
        return None

    if start < 0 or start >= file_size:
        raise ValueError("invalid")
    end = min(end, file_size - 1)
    if start > end:
        raise ValueError("invalid")
    return start, end


def _mime_for_path(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    if mime:
        return mime
    ext = Path(path).suffix.lower()
    if ext == ".mp4":
        return "video/mp4"
    if ext == ".mkv":
        return "video/x-matroska"
    return "application/octet-stream"


def _ensure_path_allowed(abs_path: str) -> None:
    """Empêche la lecture hors du dossier média si MEDIA_FOLDER est défini."""
    if not MEDIA_FOLDER or not MEDIA_FOLDER.strip():
        return
    try:
        root = Path(MEDIA_FOLDER).resolve()
        target = Path(abs_path).resolve()
        target.relative_to(root)
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Acces au fichier refuse (hors dossier media)",
        ) from None


@router.get("/stream/{content_id}")
async def stream_content(
    content_id: str,
    request: Request,
    user: dict = Depends(get_stream_user),
):
    _ = user
    row = await get_content(content_id)
    if not row:
        raise HTTPException(status_code=404, detail="Contenu introuvable")

    media_path = row["media_path"]
    abs_path = os.path.normpath(os.path.abspath(media_path))

    if not os.path.isfile(abs_path):
        raise HTTPException(status_code=404, detail="Fichier media introuvable sur le disque")

    _ensure_path_allowed(abs_path)

    file_size = await asyncio.to_thread(lambda: os.path.getsize(abs_path))
    mime = _mime_for_path(abs_path)

    range_header = request.headers.get("range")

    if file_size == 0:
        return Response(
            status_code=200,
            media_type=mime,
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": "0",
            },
        )

    try:
        parsed = _parse_range_header(range_header, file_size)
    except ValueError:
        return Response(
            status_code=416,
            headers={
                "Content-Range": f"bytes */{file_size}",
            },
        )

    if parsed is None:
        async def full_body():
            media_file_read_begin(abs_path)
            try:
                remaining = file_size
                pos = 0
                while remaining > 0:
                    to_read = min(CHUNK_SIZE, remaining)
                    chunk = await asyncio.to_thread(_read_file_chunk, abs_path, pos, to_read)
                    if not chunk:
                        break
                    yield chunk
                    pos += len(chunk)
                    remaining -= len(chunk)
            finally:
                media_file_read_end(abs_path)

        return StreamingResponse(
            full_body(),
            status_code=200,
            media_type=mime,
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size),
            },
        )

    start, end = parsed
    chunk_len = end - start + 1

    async def partial_body():
        media_file_read_begin(abs_path)
        try:
            async for chunk in _async_iter_range(abs_path, start, end):
                yield chunk
        finally:
            media_file_read_end(abs_path)

    return StreamingResponse(
        partial_body(),
        status_code=206,
        media_type=mime,
        headers={
            "Accept-Ranges": "bytes",
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Content-Length": str(chunk_len),
        },
    )
