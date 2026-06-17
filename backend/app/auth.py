import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request

from .config import (
    APP_SECRET,
    AUTH_RATE_LIMIT_MAX_ATTEMPTS,
    AUTH_RATE_LIMIT_WINDOW_SECONDS,
    GUEST_RATE_LIMIT_MAX_ATTEMPTS,
    TOKEN_TTL_MINUTES,
)


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_token(
    username: str,
    role: str,
    ttl_minutes: int = TOKEN_TTL_MINUTES,
    extra: dict | None = None,
) -> str:
    payload = {
        "sub": username,
        "role": role,
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)).timestamp()),
    }
    if extra:
        # Claims additionnels (ex. cids = contenus autorisés pour un jeton invité).
        payload.update(extra)
    payload_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    payload_b64 = _b64encode(payload_json)
    signature = hmac.new(
        APP_SECRET.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload_b64}.{signature}"


def verify_token(token: str) -> dict | None:
    try:
        payload_b64, signature = token.split(".", 1)
    except ValueError:
        return None

    expected = hmac.new(
        APP_SECRET.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return None

    try:
        payload = json.loads(_b64decode(payload_b64))
    except json.JSONDecodeError:
        return None

    if payload.get("exp") is None or int(payload["exp"]) < int(datetime.now(timezone.utc).timestamp()):
        return None

    return payload


def get_current_user(request: Request) -> dict:
    auth_header = request.headers.get("authorization", "")
    if not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Jeton manquant")

    token = auth_header.split(" ", 1)[1].strip()
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Jeton invalide ou expire")

    return payload


def require_admin(request: Request) -> dict:
    payload = get_current_user(request)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acces admin requis")
    return payload


_RATE_BUCKETS: dict[str, list[float]] = {}


def rate_limit(key: str, max_attempts: int, window_seconds: int) -> None:
    now = time.time()
    bucket = _RATE_BUCKETS.get(key, [])
    bucket = [t for t in bucket if now - t < window_seconds]
    if len(bucket) >= max_attempts:
        raise HTTPException(status_code=429, detail="Trop de tentatives, reessayez plus tard")
    bucket.append(now)
    _RATE_BUCKETS[key] = bucket


def rate_limit_auth(ip_address: str | None) -> None:
    key = f"auth:{ip_address or 'unknown'}"
    rate_limit(key, AUTH_RATE_LIMIT_MAX_ATTEMPTS, AUTH_RATE_LIMIT_WINDOW_SECONDS)


def rate_limit_guest(ip_address: str | None) -> None:
    key = f"guest:{ip_address or 'unknown'}"
    rate_limit(key, GUEST_RATE_LIMIT_MAX_ATTEMPTS, AUTH_RATE_LIMIT_WINDOW_SECONDS)
