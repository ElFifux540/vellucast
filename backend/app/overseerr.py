"""
Recherche / découverte de contenus via l'API Overseerr (qui agrège TMDb & TVmaze).

Conformément au rapport, Overseerr agit comme « source de vérité » pour les
métadonnées et les requêtes de contenu. Ce module interroge l'endpoint public
``/api/v1/search`` d'une instance Overseerr et normalise les résultats pour le
frontend (titre, année, type, affiche, synopsis).

La configuration (URL + clé API) provient de la base (app_settings), avec repli
sur les variables d'environnement. Aucune dépendance externe : on utilise
``urllib`` de la stdlib, exécuté dans un thread pour rester non bloquant.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from . import config
from .db import get_overseerr_settings

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SEC = 10  # secondes
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"  # affiche
TMDB_BACKDROP_BASE = "https://image.tmdb.org/t/p/w1280"  # bannière


class OverseerrNotConfigured(Exception):
    """Levée quand l'URL ou la clé API Overseerr n'est pas renseignée."""


class OverseerrError(Exception):
    """Erreur réseau ou HTTP lors de l'appel à Overseerr."""


async def _resolve_credentials() -> tuple[str, str]:
    """URL + clé API : la base (app_settings) prime sur les variables d'environnement."""
    settings = await get_overseerr_settings()
    url = (settings.get("overseerr_url") or config.OVERSEERR_URL or "").strip().rstrip("/")
    api_key = (settings.get("overseerr_api_key") or config.OVERSEERR_API_KEY or "").strip()
    if not url or not api_key:
        raise OverseerrNotConfigured(
            "Overseerr non configuré (URL et clé API requises dans les réglages)."
        )
    return url, api_key


def _normalize_result(item: dict) -> dict:
    """Aplati un résultat Overseerr en une structure stable pour le frontend."""
    media_type = item.get("mediaType")
    # Films : title/releaseDate ; séries : name/firstAirDate.
    title = item.get("title") or item.get("name") or item.get("originalName") or "Sans titre"
    date = item.get("releaseDate") or item.get("firstAirDate") or ""
    year = date[:4] if date else None

    poster_path = item.get("posterPath")
    poster = f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None

    backdrop_path = item.get("backdropPath")
    backdrop = f"{TMDB_BACKDROP_BASE}{backdrop_path}" if backdrop_path else None

    media_info = item.get("mediaInfo") or {}
    status = media_info.get("status")  # 1..5 : inconnu/en attente/traitement/partiel/disponible

    return {
        "id": item.get("id"),
        "tmdb_id": item.get("id"),
        "media_type": media_type,
        "title": title,
        "year": year,
        "overview": item.get("overview") or "",
        "poster_url": poster,
        "backdrop_url": backdrop,
        "vote_average": item.get("voteAverage"),
        "availability_status": status,
    }


def _extract_overseerr_message(body: bytes) -> str:
    """Extrait le message d'erreur renvoyé par Overseerr (JSON {message|error}) sinon texte brut."""
    text = body.decode("utf-8", errors="replace").strip()
    if not text:
        return ""
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return str(data.get("message") or data.get("error") or text)[:300]
    except ValueError:
        pass
    return text[:300]


def _fetch_sync(url: str, api_key: str, query: str, page: int) -> dict:
    # Overseerr exige un percent-encoding (%20) ; urlencode utilise '+' par défaut pour
    # l'espace, ce qui déclenche « query must be url encoded ». On force donc quote().
    params = urllib.parse.urlencode(
        {"query": query, "page": page, "language": "fr"},
        quote_via=urllib.parse.quote,
    )
    endpoint = f"{url}/api/v1/search?{params}"
    req = urllib.request.Request(
        endpoint,
        headers={
            "X-Api-Key": api_key,
            "Accept": "application/json",
            "User-Agent": "Vellucast/1.0",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SEC) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        # On lit le corps de la réponse : Overseerr y détaille la vraie cause du 4xx/5xx.
        try:
            detail = _extract_overseerr_message(e.read())
        except Exception:  # noqa: BLE001
            detail = ""
        hint = ""
        if e.code in (401, 403):
            hint = " (clé API invalide ?)"
        elif e.code == 404:
            hint = " (URL Overseerr incorrecte ? ne pas inclure /api/v1)"
        msg = f"Overseerr a répondu {e.code}{hint}"
        if detail:
            msg += f" : {detail}"
        raise OverseerrError(msg) from e
    except urllib.error.URLError as e:
        raise OverseerrError(f"Connexion à Overseerr impossible: {e.reason}") from e
    except TimeoutError as e:
        raise OverseerrError("Délai d'attente Overseerr dépassé") from e

    try:
        return json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        raise OverseerrError("Réponse Overseerr illisible") from e


async def search_external(query: str, *, page: int = 1) -> dict:
    """
    Recherche un film / une série via Overseerr.

    Returns:
        ``{items, page, total_pages, total_results, query}``.

    Raises:
        OverseerrNotConfigured: configuration absente.
        OverseerrError: échec réseau / HTTP.
    """
    import asyncio

    q = (query or "").strip()
    if not q:
        return {"items": [], "page": 1, "total_pages": 0, "total_results": 0, "query": q}

    try:
        page = max(1, int(page))
    except (TypeError, ValueError):
        page = 1

    url, api_key = await _resolve_credentials()
    data = await asyncio.to_thread(_fetch_sync, url, api_key, q, page)

    raw_results = data.get("results") or []
    # On ne conserve que films et séries (on ignore les personnes, etc.).
    items = [
        _normalize_result(it)
        for it in raw_results
        if it.get("mediaType") in ("movie", "tv")
    ]

    return {
        "items": items,
        "page": data.get("page", page),
        "total_pages": data.get("totalPages", 0),
        "total_results": data.get("totalResults", len(items)),
        "query": q,
    }
