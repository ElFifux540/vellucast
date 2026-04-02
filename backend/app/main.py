from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .auth import (
    create_token,
    get_current_user,
    rate_limit_auth,
    rate_limit_guest,
    require_admin,
)
from .config import CORS_ORIGINS, validate_security_settings
from .file_browser import browse_media_directory
from .scanner import scan_media_folder
from .streaming import router as streaming_router
from .upload import store_uploaded_media
from .optimizer import start_optimizer_worker, stop_optimizer_worker
from .db import (
    authenticate_user,
    admin_reset_password,
    create_content,
    create_share_link,
    create_user,
    delete_content,
    get_content,
    get_all_app_settings,
    get_media_folder_settings,
    init_db,
    list_users,
    list_audit_logs,
    list_contents,
    list_share_links,
    update_media_folder_settings,
    toggle_content_do_not_optimize,
    update_transcoding_settings,
    update_user_password,
    update_user_profile,
    update_content,
    revoke_share_link,
    use_share_link,
    validate_share_link,
)


app = FastAPI(title="Vellucast")

app.include_router(streaming_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in CORS_ORIGINS if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Range", "Accept-Ranges", "Content-Length"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    return response

@app.on_event("startup")
async def on_startup() -> None:
    validate_security_settings()
    await init_db()
    start_optimizer_worker()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await stop_optimizer_worker()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/shares")
async def create_share(payload: dict, user: dict = Depends(require_admin)) -> dict:
    payload["created_by"] = payload.get("created_by") or user.get("sub")
    result = await create_share_link(payload)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/shares/{token}")
async def get_share(token: str) -> dict:
    share = await validate_share_link(token)
    if not share:
        raise HTTPException(status_code=404, detail="Lien invalide ou expire")
    return share


@app.post("/shares/{token}/use")
async def use_share(token: str, request: Request, payload: dict | None = None) -> dict:
    payload = payload or {}
    result = await use_share_link(
        token=token,
        access_code=payload.get("access_code"),
        used_by=payload.get("used_by"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/guest/{token}")
async def guest_access(token: str, request: Request, payload: dict | None = None) -> dict:
    payload = payload or {}
    result = await use_share_link(
        token=token,
        access_code=payload.get("access_code"),
        used_by=payload.get("used_by", "guest"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["error"])

    content = await get_content(result["content_id"])
    if not content:
        raise HTTPException(status_code=404, detail="Contenu introuvable")

    return {
        "ok": True,
        "content": content,
        "used_at": result["used_at"],
    }


@app.post("/auth/login")
async def login(payload: dict, request: Request) -> dict:
    username = payload.get("username")
    password = payload.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="username et password requis")

    rate_limit_auth(request.client.host if request.client else None)

    user = await authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    token = create_token(user["username"], user["role"])
    return {"ok": True, "user": user, "token": token}


@app.post("/auth/guest")
async def guest_login(payload: dict, request: Request) -> dict:
    token = payload.get("token")
    access_code = payload.get("access_code")
    if not token:
        raise HTTPException(status_code=400, detail="token requis")

    rate_limit_guest(request.client.host if request.client else None)

    result = await use_share_link(
        token=token,
        access_code=access_code,
        used_by="guest",
        ip_address=None,
        user_agent=None,
    )
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["error"])

    content = await get_content(result["content_id"])
    if not content:
        raise HTTPException(status_code=404, detail="Contenu introuvable")

    return {"ok": True, "content": content, "used_at": result["used_at"]}


@app.post("/auth/change-password")
async def change_password(payload: dict, user: dict = Depends(get_current_user)) -> dict:
    current_password = payload.get("current_password")
    new_password = payload.get("new_password")
    if not current_password or not new_password:
        raise HTTPException(status_code=400, detail="current_password et new_password requis")

    verified = await authenticate_user(user.get("sub"), current_password)
    if not verified:
        raise HTTPException(status_code=401, detail="Mot de passe actuel invalide")

    result = await update_user_password(user.get("sub"), new_password)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"ok": True}


@app.post("/contents")
async def create_content_item(payload: dict, user: dict = Depends(require_admin)) -> dict:
    payload["created_by"] = payload.get("created_by") or user.get("sub")
    result = await create_content(payload)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/admin/users")
async def admin_create_user(payload: dict, user: dict = Depends(require_admin)) -> dict:
    payload["created_by"] = payload.get("created_by") or user.get("sub")
    result = await create_user(payload)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/admin/users")
async def admin_list_users(user: dict = Depends(require_admin)) -> list[dict]:
    return await list_users()


@app.patch("/admin/users")
async def admin_update_user(payload: dict, user: dict = Depends(require_admin)) -> dict:
    username = payload.get("username")
    if not username:
        raise HTTPException(status_code=400, detail="username requis")

    result = await update_user_profile(
        username=username,
        new_username=payload.get("new_username"),
        role=payload.get("role"),
        must_change_password=payload.get("must_change_password"),
    )
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/admin/users/reset-password")
async def admin_reset_user_password(payload: dict, user: dict = Depends(require_admin)) -> dict:
    username = payload.get("username")
    new_password = payload.get("new_password")
    if not username or not new_password:
        raise HTTPException(status_code=400, detail="username et new_password requis")

    result = await admin_reset_password(
        username=username,
        new_password=new_password,
        must_change_password=bool(payload.get("must_change_password", True)),
    )
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/admin/shares")
async def admin_list_shares(user: dict = Depends(require_admin)) -> list[dict]:
    return await list_share_links()


@app.delete("/admin/shares/{token}")
async def admin_revoke_share(token: str, user: dict = Depends(require_admin)) -> dict:
    return await revoke_share_link(token, user.get("sub"))


@app.post("/admin/media/scan")
async def admin_scan_media(user: dict = Depends(require_admin)) -> dict:
    result = await scan_media_folder(created_by=user.get("sub"))
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Scan impossible"))
    return result


@app.get("/api/files/browse")
async def api_files_browse(
    path: str | None = Query(None, description="Chemin absolu du dossier à lister (défaut: racine MEDIA_FOLDER)"),
    user: dict = Depends(require_admin),
) -> dict:
    _ = user
    try:
        return browse_media_directory(path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None


@app.get("/api/settings")
async def api_get_settings(user: dict = Depends(require_admin)) -> dict:
    _ = user
    return await get_all_app_settings()


_TRANSCODE_PAYLOAD_KEYS = frozenset(
    {
        "stream_transcode_enabled",
        "stream_transcode_preset",
        "auto_optimize_enabled",
        "ffmpeg_params",
        "optimize_schedule_type",
        "optimize_start_time",
        "optimize_end_time",
        # Anciens noms (compatibilité PUT)
        "transcode_stream_enabled",
        "transcode_stream_quality",
        "auto_optimize_ffmpeg_args",
        "auto_optimize_trigger",
        "auto_optimize_schedule_start",
        "auto_optimize_schedule_end",
    },
)


@app.put("/api/settings")
async def api_put_settings(payload: dict, user: dict = Depends(require_admin)) -> dict:
    actor = user.get("sub")
    if "movies_folder" in payload or "series_folder" in payload:
        current = await get_media_folder_settings()
        m = str(payload.get("movies_folder", current["movies_folder"]))
        s = str(payload.get("series_folder", current["series_folder"]))
        await update_media_folder_settings(m, s, updated_by=actor)
    if any(k in payload for k in _TRANSCODE_PAYLOAD_KEYS):
        await update_transcoding_settings(payload, updated_by=actor)
    return await get_all_app_settings()


@app.post("/api/upload")
async def upload_media(
    file: UploadFile = File(...),
    media_type: str = Form(...),  # "movie" ou "episode"
    library_path: str | None = Form(None),
    series_name: str | None = Form(None),
    season_number: int | None = Form(None),
    user: dict = Depends(require_admin),
) -> dict:
    try:
        result = await store_uploaded_media(
            upload_file=file,
            media_type=media_type,
            library_path=library_path,
            series_name=series_name,
            season_number=season_number,
            created_by=user.get("sub"),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    return result


@app.get("/contents")
async def get_contents(user: dict = Depends(get_current_user)) -> list[dict]:
    return await list_contents()


@app.get("/contents/{content_id}")
async def get_content_item(content_id: str, user: dict = Depends(get_current_user)) -> dict:
    content = await get_content(content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Contenu introuvable")
    return content


async def _admin_update_content(content_id: str, payload: dict, user: dict) -> dict:
    payload = dict(payload)
    payload["updated_by"] = user.get("sub")
    result = await update_content(content_id, payload)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.patch("/contents/{content_id}")
async def update_content_item(
    content_id: str,
    payload: dict,
    user: dict = Depends(require_admin),
) -> dict:
    return await _admin_update_content(content_id, payload, user)


@app.put("/contents/{content_id}")
async def update_content_item_put(
    content_id: str,
    payload: dict,
    user: dict = Depends(require_admin),
) -> dict:
    """Alias REST (même corps que PATCH) pour mises à jour partielles ex. flags."""
    return await _admin_update_content(content_id, payload, user)


@app.post("/api/contents/{content_id}/toggle-optimize")
async def api_toggle_content_optimize(
    content_id: str,
    user: dict = Depends(require_admin),
) -> dict:
    """Inverse le flag do_not_optimize (menu contextuel)."""
    result = await toggle_content_do_not_optimize(content_id, updated_by=user.get("sub"))
    if not result["ok"]:
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Mise à jour impossible"),
        )
    return result


@app.delete("/contents/{content_id}")
async def delete_content_item(content_id: str, user: dict = Depends(require_admin)) -> dict:
    return await delete_content(content_id, user.get("sub"))


@app.get("/audit-logs")
async def get_audit_logs(limit: int = 100, user: dict = Depends(require_admin)) -> list[dict]:
    return await list_audit_logs(limit)
