"""Génération d'identifiants courts uniques pour la table contents."""

from __future__ import annotations

import secrets
import string

from .db import content_id_exists

ALPHABET = string.ascii_letters + string.digits
SHORT_ID_LENGTH = 8
_MAX_ATTEMPTS = 96


async def generate_unique_content_id() -> str:
    """Génère un id alphanumérique court (8 caractères), unique en base."""
    for _ in range(_MAX_ATTEMPTS):
        cid = "".join(secrets.choice(ALPHABET) for _ in range(SHORT_ID_LENGTH))
        if not await content_id_exists(cid):
            return cid
    raise RuntimeError("Impossible de générer un identifiant de contenu unique")
