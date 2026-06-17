"""Streaming vidéo : HTTP Range (206) + transcodage HLS à la volée (TFE)."""

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
from .db import get_content, get_transcoding_settings
from .hls import decide_playback, manager
from .optimizer import media_file_read_begin, media_file_read_end

router = APIRouter(prefix="/api", tags=["stream"])

CHUNK_SIZE = 64 * 1024  # taille de lecture par bloc


async def _resolve_media_abs_path(content_id: str) -> str:
    """Récupère le chemin absolu du média d'un contenu (404/403 sinon)."""
    row = await get_content(content_id)
    if not row:
        raise HTTPException(status_code=404, detail="Contenu introuvable")
    media_path = row["media_path"]
    abs_path = os.path.normpath(os.path.abspath(media_path))
    if not os.path.isfile(abs_path):
        raise HTTPException(status_code=404, detail="Fichier media introuvable sur le disque")
    _ensure_path_allowed(abs_path)
    return abs_path


def _authorize_guest(user: dict, content_id: str) -> None:
    """Un jeton invité ne peut lire que les contenus inclus dans son lien de partage (claim cids)."""
    if user.get("role") == "guest":
        allowed = user.get("cids") or []
        if content_id not in allowed:
            raise HTTPException(status_code=403, detail="Contenu non autorisé pour ce lien")


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
    _authorize_guest(user, content_id)
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


async def _stream_preset() -> tuple[bool, str]:
    """(transcodage_actif, preset) depuis app_settings."""
    settings = await get_transcoding_settings()
    enabled = str(settings.get("stream_transcode_enabled", "0")).strip() in ("1", "true", "on")
    preset = str(settings.get("stream_transcode_preset", "3")).strip() or "3"
    return enabled, preset


@router.get("/stream/{content_id}/info")
async def stream_info(
    content_id: str,
    user: dict = Depends(get_stream_user),
) -> dict:
    """
    Indique au client le mode de lecture recommandé : ``direct`` ou ``hls``.

    Le frontend appelle cet endpoint avant de choisir entre la balise <video> brute
    et le lecteur hls.js.
    """
    _authorize_guest(user, content_id)
    abs_path = await _resolve_media_abs_path(content_id)
    enabled, _preset = await _stream_preset()
    try:
        decision = await decide_playback(abs_path, transcode_enabled=enabled)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e)) from None
    return {"content_id": content_id, "transcode_enabled": enabled, **decision}


@router.get("/stream/{content_id}/hls/index.m3u8")
async def stream_hls_playlist(
    content_id: str,
    user: dict = Depends(get_stream_user),
):
    """Démarre (ou réutilise) une session HLS et renvoie la playlist .m3u8."""
    _authorize_guest(user, content_id)
    abs_path = await _resolve_media_abs_path(content_id)
    enabled, preset = await _stream_preset()
    if not enabled:
        raise HTTPException(status_code=409, detail="Transcodage à la volée désactivé")

    try:
        session = await manager.get_session(content_id, abs_path, preset)
        playlist = await asyncio.to_thread(session.read_playlist)
    except (RuntimeError, TimeoutError) as e:
        raise HTTPException(status_code=503, detail=f"Transcodage HLS indisponible: {e}") from None

    return Response(
        content=playlist,
        media_type="application/vnd.apple.mpegurl",
        headers={"Cache-Control": "no-cache"},
    )


@router.get("/stream/{content_id}/hls/{segment}")
async def stream_hls_segment(
    content_id: str,
    segment: str,
    user: dict = Depends(get_stream_user),
):
    """Sert un segment .ts produit par la session HLS du contenu."""
    _authorize_guest(user, content_id)
    if not segment.endswith(".ts"):
        raise HTTPException(status_code=404, detail="Segment invalide")

    abs_path = await _resolve_media_abs_path(content_id)
    enabled, preset = await _stream_preset()
    if not enabled:
        raise HTTPException(status_code=409, detail="Transcodage à la volée désactivé")

    session = await manager.get_session(content_id, abs_path, preset)
    seg_path = session.segment_path(segment)
    if seg_path is None:
        # Segment pas encore produit : le client réessaiera.
        raise HTTPException(status_code=404, detail="Segment indisponible (en cours de production)")

    data = await asyncio.to_thread(lambda: open(seg_path, "rb").read())
    return Response(
        content=data,
        media_type="video/mp2t",
        headers={"Cache-Control": "no-cache"},
    )
