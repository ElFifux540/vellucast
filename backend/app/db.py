import hashlib
import json
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import aiosqlite
from contextlib import asynccontextmanager

from pathlib import Path

from .content_validation import validate_media_path_for_content
from .config import (
    ADMIN_PASSWORD,
    ADMIN_USERNAME,
    MEDIA_FOLDER,
    PASSWORD_ITERATIONS,
    PASSWORD_MIN_LENGTH,
    USER_PASSWORD,
    USER_USERNAME,
)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "app.db")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _hash_password_legacy(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def _hash_password(password: str, salt: bytes, iterations: int) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return digest.hex()


@asynccontextmanager
async def _connect() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    try:
        await db.execute("PRAGMA foreign_keys = ON")
        yield db
    finally:
        await db.close()


async def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with _connect() as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                password_iterations INTEGER NOT NULL DEFAULT 0,
                must_change_password INTEGER NOT NULL DEFAULT 0,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        await _ensure_user_columns(db)
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS contents (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                media_path TEXT NOT NULL,
                created_by TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        await _ensure_columns(db)
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS share_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT UNIQUE NOT NULL,
                content_id TEXT NOT NULL,
                created_by TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                max_uses INTEGER,
                used_count INTEGER NOT NULL DEFAULT 0,
                access_code_hash TEXT,
                FOREIGN KEY (content_id) REFERENCES contents (id)
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS share_link_usages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                share_id INTEGER NOT NULL,
                used_at TEXT NOT NULL,
                used_by_ip TEXT,
                used_by_user_agent TEXT,
                used_by TEXT,
                FOREIGN KEY (share_id) REFERENCES share_links (id)
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                action TEXT NOT NULL,
                actor TEXT,
                entity_type TEXT,
                entity_id TEXT,
                ip_address TEXT,
                user_agent TEXT,
                details TEXT
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        for _key in ("movies_folder", "series_folder"):
            await db.execute(
                "INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)",
                (_key, ""),
            )
        await _ensure_app_settings_transcoding_keys(db)
        await db.commit()

    await seed_default_users()


async def create_content(payload: dict) -> dict:
    content_id = (payload.get("id") or "").strip()
    title = payload.get("title")
    media_path = payload.get("media_path")

    if not content_id:
        return {"ok": False, "error": "id requis"}

    title_str = (title if isinstance(title, str) else str(title or "")).strip()
    if not title_str:
        return {"ok": False, "error": "Le titre ne peut pas être vide"}

    if media_path is None or not str(media_path).strip():
        return {"ok": False, "error": "Le chemin média ne peut pas être vide"}

    mp_raw = str(media_path).strip()
    ok_path, err_path = validate_media_path_for_content(mp_raw)
    if not ok_path:
        return {"ok": False, "error": err_path or "Chemin média invalide"}
    media_path_norm = os.path.normpath(os.path.abspath(mp_raw))

    created_at = _now_utc().isoformat()

    async with _connect() as db:
        await db.execute(
            """
            INSERT INTO contents (id, title, media_path, created_by, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                content_id,
                title_str,
                media_path_norm,
                payload.get("created_by"),
                created_at,
            ),
        )
        await db.commit()

    await log_audit(
        action="content_created",
        actor=payload.get("created_by"),
        entity_type="content",
        entity_id=content_id,
        details={"title": title_str},
    )

    return {"ok": True, "id": content_id, "title": title_str, "media_path": media_path_norm}


async def create_user(payload: dict) -> dict:
    username = payload.get("username")
    password = payload.get("password")
    role = payload.get("role", "user")
    must_change_password = bool(payload.get("must_change_password"))

    if not username or not password:
        return {"ok": False, "error": "username et password requis"}

    if len(password) < PASSWORD_MIN_LENGTH or password.lower() == username.lower():
        return {"ok": False, "error": "mot de passe trop faible"}

    salt = secrets.token_bytes(16)
    password_hash = _hash_password(password, salt, PASSWORD_ITERATIONS)
    created_at = _now_utc().isoformat()

    async with _connect() as db:
        try:
            await db.execute(
                """
                INSERT INTO users (username, password_hash, salt, password_iterations, must_change_password, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    username,
                    password_hash,
                    salt.hex(),
                    PASSWORD_ITERATIONS,
                    1 if must_change_password else 0,
                    role,
                    created_at,
                ),
            )
            await db.commit()
        except aiosqlite.IntegrityError:
            return {"ok": False, "error": "username deja utilise"}

    await log_audit(
        action="user_created",
        actor=payload.get("created_by"),
        entity_type="user",
        entity_id=username,
        details={"role": role},
    )

    return {
        "ok": True,
        "username": username,
        "role": role,
        "must_change_password": must_change_password,
    }


async def seed_default_users() -> None:
    admin_username = ADMIN_USERNAME
    admin_password = ADMIN_PASSWORD
    user_username = USER_USERNAME
    user_password = USER_PASSWORD

    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT COUNT(*) AS count FROM users") as cursor:
            row = await cursor.fetchone()
            if row and row["count"] > 0:
                return

    await _create_user_internal(admin_username, admin_password, "admin", must_change_password=True)
    await _create_user_internal(user_username, user_password, "user", must_change_password=False)

    await log_audit(
        action="users_seeded",
        actor="system",
        entity_type="user",
        entity_id=f"{admin_username},{user_username}",
        details={"admin": admin_username, "user": user_username},
    )


async def _ensure_columns(db: aiosqlite.Connection) -> None:
    """Migration : colonnes manquantes sur la table `contents` (ex. do_not_optimize, défaut faux)."""
    columns: list[str] = []
    async with db.execute("PRAGMA table_info(contents)") as cursor:
        rows = await cursor.fetchall()
        columns = [row[1] for row in rows]

    if "do_not_optimize" not in columns:
        await db.execute(
            "ALTER TABLE contents ADD COLUMN do_not_optimize INTEGER NOT NULL DEFAULT 0"
        )


TRANSCODE_SETTING_DEFAULTS: dict[str, str] = {
    "stream_transcode_enabled": "0",
    "stream_transcode_preset": "3",
    "auto_optimize_enabled": "0",
    "ffmpeg_params": "",
    "optimize_schedule_type": "upload",
    "optimize_start_time": "02:00",
    "optimize_end_time": "06:00",
}

# Anciennes clés (compatibilité lecture / migration logique)
LEGACY_TRANSCODE_KEYS: dict[str, str] = {
    "stream_transcode_enabled": "transcode_stream_enabled",
    "stream_transcode_preset": "transcode_stream_quality",
    "ffmpeg_params": "auto_optimize_ffmpeg_args",
    "optimize_schedule_type": "auto_optimize_trigger",
    "optimize_start_time": "auto_optimize_schedule_start",
    "optimize_end_time": "auto_optimize_schedule_end",
}


async def _ensure_app_settings_transcoding_keys(db: aiosqlite.Connection) -> None:
    """Insère les clés de transcodage avec valeurs par défaut si absentes."""
    for key, val in TRANSCODE_SETTING_DEFAULTS.items():
        await db.execute(
            "INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)",
            (key, val),
        )


async def toggle_content_do_not_optimize(content_id: str, *, updated_by: str | None) -> dict:
    """Inverse le booléen do_not_optimize (SQLite 0/1) pour un contenu."""
    content = await get_content(content_id)
    if not content:
        return {"ok": False, "error": "Contenu introuvable"}
    current = bool(content.get("do_not_optimize"))
    new_val = not current
    res = await update_content(
        content_id,
        {"do_not_optimize": new_val, "updated_by": updated_by},
    )
    if not res.get("ok"):
        return res
    return {"ok": True, "id": content_id, "do_not_optimize": new_val}


async def _ensure_user_columns(db: aiosqlite.Connection) -> None:
    columns = []
    async with db.execute("PRAGMA table_info(users)") as cursor:
        rows = await cursor.fetchall()
        columns = [row[1] for row in rows]

    if "password_iterations" not in columns:
        await db.execute("ALTER TABLE users ADD COLUMN password_iterations INTEGER NOT NULL DEFAULT 0")

    if "must_change_password" not in columns:
        await db.execute("ALTER TABLE users ADD COLUMN must_change_password INTEGER NOT NULL DEFAULT 0")


async def _create_user_internal(username: str, password: str, role: str, must_change_password: bool) -> None:
    if len(password) < PASSWORD_MIN_LENGTH or password.lower() == username.lower():
        return

    salt = secrets.token_bytes(16)
    password_hash = _hash_password(password, salt, PASSWORD_ITERATIONS)
    created_at = _now_utc().isoformat()

    async with _connect() as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO users (username, password_hash, salt, password_iterations, must_change_password, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username,
                password_hash,
                salt.hex(),
                PASSWORD_ITERATIONS,
                1 if must_change_password else 0,
                role,
                created_at,
            ),
        )
        await db.commit()


async def authenticate_user(username: str, password: str) -> dict | None:
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            user = dict(row)

    password_iterations = int(user.get("password_iterations") or 0)
    if password_iterations > 0:
        expected = _hash_password(password, bytes.fromhex(user["salt"]), password_iterations)
        if expected != user["password_hash"]:
            return None
    else:
        expected = _hash_password_legacy(password, user["salt"])
        if expected != user["password_hash"]:
            return None
        await _upgrade_password_hash(user["username"], password)

    return {
        "username": user["username"],
        "role": user["role"],
        "created_at": user["created_at"],
        "must_change_password": bool(user.get("must_change_password")),
    }


async def update_user_password(username: str, new_password: str) -> dict:
    if len(new_password) < PASSWORD_MIN_LENGTH:
        return {"ok": False, "error": "mot de passe trop faible"}

    salt = secrets.token_bytes(16)
    password_hash = _hash_password(new_password, salt, PASSWORD_ITERATIONS)

    async with _connect() as db:
        await db.execute(
            """
            UPDATE users
            SET password_hash = ?, salt = ?, password_iterations = ?, must_change_password = 0
            WHERE username = ?
            """,
            (password_hash, salt.hex(), PASSWORD_ITERATIONS, username),
        )
        await db.commit()

    await log_audit(
        action="password_changed",
        actor=username,
        entity_type="user",
        entity_id=username,
    )

    return {"ok": True}


async def list_users() -> list[dict]:
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT username, role, created_at, must_change_password
            FROM users
            ORDER BY created_at DESC
            """
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def update_user_profile(
    username: str,
    new_username: str | None,
    role: str | None,
    must_change_password: bool | None,
) -> dict:
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT username FROM users WHERE username = ?",
            (username,),
        ) as cursor:
            existing = await cursor.fetchone()
            if not existing:
                return {"ok": False, "error": "user introuvable"}

        if new_username and new_username != username:
            async with db.execute(
                "SELECT username FROM users WHERE username = ?",
                (new_username,),
            ) as cursor:
                if await cursor.fetchone():
                    return {"ok": False, "error": "nouveau username deja utilise"}

        updates = []
        params: list[Any] = []
        if new_username and new_username != username:
            updates.append("username = ?")
            params.append(new_username)
        if role:
            updates.append("role = ?")
            params.append(role)
        if must_change_password is not None:
            updates.append("must_change_password = ?")
            params.append(1 if must_change_password else 0)

        if not updates:
            return {"ok": True}

        params.append(username)
        await db.execute(
            f"UPDATE users SET {', '.join(updates)} WHERE username = ?",
            params,
        )
        await db.commit()

    await log_audit(
        action="user_updated",
        actor="admin",
        entity_type="user",
        entity_id=new_username or username,
        details={"updated_fields": updates},
    )

    return {"ok": True}


async def admin_reset_password(
    username: str,
    new_password: str,
    must_change_password: bool = True,
) -> dict:
    if len(new_password) < PASSWORD_MIN_LENGTH:
        return {"ok": False, "error": "mot de passe trop faible"}

    salt = secrets.token_bytes(16)
    password_hash = _hash_password(new_password, salt, PASSWORD_ITERATIONS)

    async with _connect() as db:
        await db.execute(
            """
            UPDATE users
            SET password_hash = ?, salt = ?, password_iterations = ?, must_change_password = ?
            WHERE username = ?
            """,
            (
                password_hash,
                salt.hex(),
                PASSWORD_ITERATIONS,
                1 if must_change_password else 0,
                username,
            ),
        )
        await db.commit()

    await log_audit(
        action="password_reset",
        actor="admin",
        entity_type="user",
        entity_id=username,
    )

    return {"ok": True}


async def _upgrade_password_hash(username: str, password: str) -> None:
    salt = secrets.token_bytes(16)
    password_hash = _hash_password(password, salt, PASSWORD_ITERATIONS)

    async with _connect() as db:
        await db.execute(
            """
            UPDATE users
            SET password_hash = ?, salt = ?, password_iterations = ?
            WHERE username = ?
            """,
            (password_hash, salt.hex(), PASSWORD_ITERATIONS, username),
        )
        await db.commit()


async def content_id_exists(content_id: str) -> bool:
    """Indique si un identifiant est déjà utilisé dans contents."""
    async with _connect() as db:
        async with db.execute(
            "SELECT 1 FROM contents WHERE id = ? LIMIT 1",
            (content_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return row is not None


async def get_content(content_id: str) -> dict | None:
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM contents WHERE id = ?",
            (content_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_content_by_media_path(media_path: str) -> dict | None:
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM contents WHERE media_path = ? LIMIT 1",
            (media_path,),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def list_contents() -> list[dict]:
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM contents ORDER BY created_at DESC") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def list_optimizable_contents() -> list[dict]:
    """Contenus éligibles à l'optimisation automatique (do_not_optimize = 0)."""
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM contents WHERE do_not_optimize = 0 ORDER BY created_at ASC",
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def update_content(content_id: str, payload: dict) -> dict:
    title = payload.get("title")
    media_path = payload.get("media_path")
    do_not_optimize = payload.get("do_not_optimize")

    if title is None and media_path is None and do_not_optimize is None:
        return {"ok": False, "error": "aucune modification fournie"}

    updates = []
    params: list[Any] = []

    if title is not None:
        title_str = (title if isinstance(title, str) else str(title)).strip()
        if not title_str:
            return {"ok": False, "error": "Le titre ne peut pas être vide"}
        updates.append("title = ?")
        params.append(title_str)

    if media_path is not None:
        mp_raw = str(media_path).strip()
        if not mp_raw:
            return {"ok": False, "error": "Le chemin média ne peut pas être vide"}
        ok_path, err_path = validate_media_path_for_content(mp_raw)
        if not ok_path:
            return {"ok": False, "error": err_path or "Chemin média invalide"}
        media_path_norm = os.path.normpath(os.path.abspath(mp_raw))
        updates.append("media_path = ?")
        params.append(media_path_norm)

    if do_not_optimize is not None:
        flag = 1 if bool(do_not_optimize) else 0
        updates.append("do_not_optimize = ?")
        params.append(flag)

    if not updates:
        return {"ok": False, "error": "aucune modification fournie"}

    params.append(content_id)

    async with _connect() as db:
        await db.execute(
            f"UPDATE contents SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        await db.commit()

    await log_audit(
        action="content_updated",
        actor=payload.get("updated_by"),
        entity_type="content",
        entity_id=content_id,
        details={"fields": updates},
    )

    return {"ok": True}


async def delete_content(content_id: str, deleted_by: str | None) -> dict:
    async with _connect() as db:
        await db.execute("DELETE FROM contents WHERE id = ?", (content_id,))
        await db.commit()

    await log_audit(
        action="content_deleted",
        actor=deleted_by,
        entity_type="content",
        entity_id=content_id,
    )

    return {"ok": True}


async def create_share_link(payload: dict) -> dict:
    content_id = payload.get("content_id")
    if not content_id:
        return {"ok": False, "error": "content_id requis"}

    content = await get_content(content_id)
    if not content:
        return {"ok": False, "error": "contenu introuvable"}

    token = secrets.token_urlsafe(24)
    created_at = _now_utc()

    expires_in_minutes = payload.get("expires_in_minutes")
    expires_in_value = payload.get("expires_in_value")
    expires_in_unit = payload.get("expires_in_unit")
    expires_at = None
    if expires_in_value is not None and expires_in_unit:
        value = int(expires_in_value)
        unit = str(expires_in_unit).lower()
        if value <= 0:
            expires_at = None
        else:
            if unit == "minutes":
                expires_in_minutes = value
            elif unit == "hours":
                expires_in_minutes = value * 60
            elif unit == "days":
                expires_in_minutes = value * 60 * 24
            elif unit == "weeks":
                expires_in_minutes = value * 60 * 24 * 7
            elif unit == "months":
                expires_in_minutes = value * 60 * 24 * 30
            elif unit == "years":
                expires_in_minutes = value * 60 * 24 * 365
    if expires_in_minutes is not None:
        minutes = int(expires_in_minutes)
        if minutes > 0:
            expires_at = created_at + timedelta(minutes=minutes)

    max_uses = payload.get("max_uses")
    if max_uses in (0, "0"):
        max_uses = None
    access_code = payload.get("access_code")
    access_code_hash = _hash_code(access_code) if access_code else None

    async with _connect() as db:
        await db.execute(
            """
            INSERT INTO share_links (
                token, content_id, created_by, created_at, expires_at,
                max_uses, access_code_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                token,
                content_id,
                payload.get("created_by"),
                created_at.isoformat(),
                expires_at.isoformat() if expires_at else None,
                int(max_uses) if max_uses is not None else None,
                access_code_hash,
            ),
        )
        await db.commit()

    await log_audit(
        action="share_link_created",
        actor=payload.get("created_by"),
        entity_type="share_link",
        entity_id=token,
        details={
            "content_id": content_id,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "max_uses": max_uses,
            "has_access_code": bool(access_code),
        },
    )

    return {
        "ok": True,
        "token": token,
        "content_id": content_id,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "max_uses": max_uses,
    }


async def list_share_links() -> list[dict]:
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT token, content_id, created_by, created_at, expires_at,
                   max_uses, used_count, access_code_hash
            FROM share_links
            ORDER BY created_at DESC
            """
        ) as cursor:
            rows = await cursor.fetchall()

    shares = []
    for row in rows:
        share = dict(row)
        expired = _is_expired(share.get("expires_at"))
        max_uses = share.get("max_uses")
        is_valid = not expired and (max_uses is None or share.get("used_count", 0) < max_uses)
        shares.append(
            {
                "token": share["token"],
                "content_id": share["content_id"],
                "created_by": share.get("created_by"),
                "created_at": share["created_at"],
                "expires_at": share.get("expires_at"),
                "max_uses": max_uses,
                "used_count": share.get("used_count"),
                "requires_code": bool(share.get("access_code_hash")),
                "is_valid": is_valid,
            }
        )
    return shares


async def revoke_share_link(token: str, revoked_by: str | None) -> dict:
    async with _connect() as db:
        await db.execute(
            """
            DELETE FROM share_link_usages
            WHERE share_id IN (SELECT id FROM share_links WHERE token = ?)
            """,
            (token,),
        )
        await db.execute("DELETE FROM share_links WHERE token = ?", (token,))
        await db.commit()

    await log_audit(
        action="share_link_revoked",
        actor=revoked_by,
        entity_type="share_link",
        entity_id=token,
    )

    return {"ok": True}


async def _get_share_by_token(token: str) -> dict | None:
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM share_links WHERE token = ?",
            (token,),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


def _is_expired(expires_at: str | None) -> bool:
    if not expires_at:
        return False
    return _now_utc() > datetime.fromisoformat(expires_at)


async def validate_share_link(token: str) -> dict | None:
    share = await _get_share_by_token(token)
    if not share:
        return None
    if _is_expired(share.get("expires_at")):
        return None
    max_uses = share.get("max_uses")
    if max_uses is not None and share.get("used_count", 0) >= max_uses:
        return None
    return {
        "token": share["token"],
        "content_id": share["content_id"],
        "created_by": share.get("created_by"),
        "created_at": share["created_at"],
        "expires_at": share.get("expires_at"),
        "max_uses": share.get("max_uses"),
        "used_count": share.get("used_count"),
        "requires_code": bool(share.get("access_code_hash")),
    }


async def use_share_link(
    token: str,
    access_code: str | None,
    used_by: str | None,
    ip_address: str | None,
    user_agent: str | None,
) -> dict[str, Any]:
    share = await _get_share_by_token(token)
    if not share:
        return {"ok": False, "error": "Lien invalide"}
    if _is_expired(share.get("expires_at")):
        return {"ok": False, "error": "Lien expire"}
    max_uses = share.get("max_uses")
    if max_uses is not None and share.get("used_count", 0) >= max_uses:
        return {"ok": False, "error": "Lien deja utilise"}

    access_code_hash = share.get("access_code_hash")
    if access_code_hash and _hash_code(access_code or "") != access_code_hash:
        return {"ok": False, "error": "Code d'acces invalide"}

    used_at = _now_utc().isoformat()

    async with _connect() as db:
        await db.execute(
            """
            INSERT INTO share_link_usages (
                share_id, used_at, used_by_ip, used_by_user_agent, used_by
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                share["id"],
                used_at,
                ip_address,
                user_agent,
                used_by,
            ),
        )
        await db.execute(
            "UPDATE share_links SET used_count = used_count + 1 WHERE id = ?",
            (share["id"],),
        )
        await db.commit()

    await log_audit(
        action="share_link_used",
        actor=used_by,
        entity_type="share_link",
        entity_id=token,
        ip_address=ip_address,
        user_agent=user_agent,
        details={"content_id": share["content_id"]},
    )

    return {
        "ok": True,
        "content_id": share["content_id"],
        "used_at": used_at,
    }


def _validate_folder_under_media_root(abs_path: str) -> None:
    """Vérifie que le chemin reste sous MEDIA_FOLDER si celui-ci est défini."""
    if not MEDIA_FOLDER or not str(MEDIA_FOLDER).strip():
        return
    root = Path(MEDIA_FOLDER).resolve()
    target = Path(abs_path).resolve()
    try:
        target.relative_to(root)
    except ValueError as e:
        raise ValueError("Chemin hors du dossier média autorisé (MEDIA_FOLDER)") from e


async def get_media_folder_settings() -> dict[str, str]:
    """Lit les dossiers de base films / séries depuis app_settings."""
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT key, value FROM app_settings WHERE key IN ('movies_folder', 'series_folder')",
        ) as cursor:
            rows = await cursor.fetchall()
    out: dict[str, str] = {"movies_folder": "", "series_folder": ""}
    for row in rows:
        out[row["key"]] = (row["value"] or "").strip()
    return out


async def update_media_folder_settings(
    movies_folder: str,
    series_folder: str,
    *,
    updated_by: str | None,
) -> dict:
    """Met à jour les chemins (validés si MEDIA_FOLDER est défini)."""
    m = (movies_folder or "").strip()
    s = (series_folder or "").strip()

    for label, raw in (("movies_folder", m), ("series_folder", s)):
        if not raw:
            continue
        abs_p = os.path.normpath(os.path.abspath(raw))
        _validate_folder_under_media_root(abs_p)

    async with _connect() as db:
        await db.execute(
            "INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)",
            ("movies_folder", m),
        )
        await db.execute(
            "INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)",
            ("series_folder", s),
        )
        await db.commit()

    await log_audit(
        action="media_folders_updated",
        actor=updated_by,
        entity_type="app_settings",
        entity_id="media_folders",
        details={"movies_folder": m, "series_folder": s},
    )

    return {"ok": True, "movies_folder": m, "series_folder": s}


_TIME_RE = re.compile(r"^\d{2}:\d{2}$")


def _legacy_trigger_to_schedule_type(v: Any) -> str:
    """Convertit l'ancienne valeur auto_optimize_trigger vers optimize_schedule_type."""
    s = (str(v) if v is not None else "").strip().lower()
    if s == "scheduled":
        return "scheduled"
    return "upload"


def _schedule_type_setting(v: Any) -> str:
    """Normalise upload | scheduled (accepte aussi les anciennes valeurs on_upload, etc.)."""
    s = (str(v) if v is not None else "").strip().lower()
    if s == "scheduled":
        return "scheduled"
    return "upload"


def _coerce_transcode_payload(payload: dict) -> dict:
    """Normalise les anciens noms de champs API vers les clés app_settings actuelles."""
    p = dict(payload)
    if "stream_transcode_enabled" not in p and "transcode_stream_enabled" in p:
        p["stream_transcode_enabled"] = p.pop("transcode_stream_enabled")
    if "stream_transcode_preset" not in p and "transcode_stream_quality" in p:
        p["stream_transcode_preset"] = p.pop("transcode_stream_quality")
    if "ffmpeg_params" not in p and "auto_optimize_ffmpeg_args" in p:
        p["ffmpeg_params"] = p.pop("auto_optimize_ffmpeg_args")
    if "optimize_schedule_type" not in p and "auto_optimize_trigger" in p:
        p["optimize_schedule_type"] = _legacy_trigger_to_schedule_type(
            p.pop("auto_optimize_trigger"),
        )
    if "optimize_start_time" not in p and "auto_optimize_schedule_start" in p:
        p["optimize_start_time"] = p.pop("auto_optimize_schedule_start")
    if "optimize_end_time" not in p and "auto_optimize_schedule_end" in p:
        p["optimize_end_time"] = p.pop("auto_optimize_schedule_end")
    return p


async def get_transcoding_settings() -> dict[str, str]:
    """Lit les paramètres de transcodage / optimisation (app_settings)."""
    out = dict(TRANSCODE_SETTING_DEFAULTS)
    all_keys = list(
        set(TRANSCODE_SETTING_DEFAULTS.keys()) | set(LEGACY_TRANSCODE_KEYS.values()),
    )
    placeholders = ",".join("?" * len(all_keys))
    db_map: dict[str, str] = {}
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            f"SELECT key, value FROM app_settings WHERE key IN ({placeholders})",
            all_keys,
        ) as cursor:
            rows = await cursor.fetchall()
    for row in rows:
        db_map[row["key"]] = (row["value"] or "").strip()

    for new_k, defv in TRANSCODE_SETTING_DEFAULTS.items():
        val = db_map.get(new_k, "").strip()
        if val:
            out[new_k] = (
                _schedule_type_setting(val) if new_k == "optimize_schedule_type" else val
            )
            continue
        leg = LEGACY_TRANSCODE_KEYS.get(new_k)
        if leg:
            lv = db_map.get(leg, "").strip()
            if lv:
                if new_k == "optimize_schedule_type":
                    out[new_k] = _legacy_trigger_to_schedule_type(lv)
                else:
                    out[new_k] = lv
                continue
        out[new_k] = defv
    return out


async def get_all_app_settings() -> dict[str, str]:
    """Dossiers médias + transcodage pour l'API admin."""
    folders = await get_media_folder_settings()
    trans = await get_transcoding_settings()
    return {**folders, **trans}


def _bool_to_setting(v: Any) -> str:
    if v is True:
        return "1"
    if v is False:
        return "0"
    s = str(v).strip().lower()
    if s in ("1", "true", "yes", "on"):
        return "1"
    return "0"


def _preset_setting(v: Any) -> str:
    try:
        n = int(v)
        return str(max(1, min(5, n)))
    except (TypeError, ValueError):
        return TRANSCODE_SETTING_DEFAULTS["stream_transcode_preset"]


def _time_setting(v: Any, fallback: str) -> str:
    s = (str(v) if v is not None else "").strip()
    if _TIME_RE.match(s):
        return s
    return fallback


def _ffmpeg_args_setting(v: Any) -> str:
    s = (v if isinstance(v, str) else str(v or "")).strip()
    return s[:4000]


async def update_transcoding_settings(payload: dict, *, updated_by: str | None) -> dict[str, str]:
    """Met à jour uniquement les clés présentes dans payload (valeurs normalisées)."""
    payload = _coerce_transcode_payload(payload)
    current = await get_transcoding_settings()
    new_vals = dict(current)

    if "stream_transcode_enabled" in payload:
        new_vals["stream_transcode_enabled"] = _bool_to_setting(
            payload["stream_transcode_enabled"],
        )
    if "stream_transcode_preset" in payload:
        new_vals["stream_transcode_preset"] = _preset_setting(payload["stream_transcode_preset"])
    if "auto_optimize_enabled" in payload:
        new_vals["auto_optimize_enabled"] = _bool_to_setting(payload["auto_optimize_enabled"])
    if "ffmpeg_params" in payload:
        new_vals["ffmpeg_params"] = _ffmpeg_args_setting(payload["ffmpeg_params"])
    if "optimize_schedule_type" in payload:
        new_vals["optimize_schedule_type"] = _schedule_type_setting(
            payload["optimize_schedule_type"],
        )
    if "optimize_start_time" in payload:
        new_vals["optimize_start_time"] = _time_setting(
            payload["optimize_start_time"],
            current["optimize_start_time"],
        )
    if "optimize_end_time" in payload:
        new_vals["optimize_end_time"] = _time_setting(
            payload["optimize_end_time"],
            current["optimize_end_time"],
        )

    if not any(k in payload for k in TRANSCODE_SETTING_DEFAULTS):
        return current

    async with _connect() as db:
        for k, val in new_vals.items():
            if k not in TRANSCODE_SETTING_DEFAULTS:
                continue
            await db.execute(
                "INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)",
                (k, val),
            )
        await db.commit()

    await log_audit(
        action="transcoding_settings_updated",
        actor=updated_by,
        entity_type="app_settings",
        entity_id="transcoding",
        details={k: new_vals[k] for k in TRANSCODE_SETTING_DEFAULTS},
    )

    return new_vals


async def log_audit(
    action: str,
    actor: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    details: dict | None = None,
) -> None:
    payload = json.dumps(details or {}, ensure_ascii=True)
    created_at = _now_utc().isoformat()

    async with _connect() as db:
        await db.execute(
            """
            INSERT INTO audit_logs (
                created_at, action, actor, entity_type, entity_id,
                ip_address, user_agent, details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                action,
                actor,
                entity_type,
                entity_id,
                ip_address,
                user_agent,
                payload,
            ),
        )
        await db.commit()


async def list_audit_logs(limit: int = 100) -> list[dict]:
    safe_limit = max(1, min(limit, 500))
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?",
            (safe_limit,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

