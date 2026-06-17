import os


def _get_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


APP_ENV = os.environ.get("APP_ENV", "dev")
APP_SECRET = os.environ.get("APP_SECRET", "dev-secret-change")
TOKEN_TTL_MINUTES = _get_int("TOKEN_TTL_MINUTES", 60)
PASSWORD_MIN_LENGTH = _get_int("PASSWORD_MIN_LENGTH", 10)
PASSWORD_ITERATIONS = _get_int("PASSWORD_ITERATIONS", 120000)
AUTH_RATE_LIMIT_WINDOW_SECONDS = _get_int("AUTH_RATE_LIMIT_WINDOW_SECONDS", 60)
AUTH_RATE_LIMIT_MAX_ATTEMPTS = _get_int("AUTH_RATE_LIMIT_MAX_ATTEMPTS", 5)
GUEST_RATE_LIMIT_MAX_ATTEMPTS = _get_int("GUEST_RATE_LIMIT_MAX_ATTEMPTS", 10)
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
# Dossier racine à scanner pour les médias (chemin absolu ou relatif)
MEDIA_FOLDER = os.environ.get("MEDIA_FOLDER", "")
# Racine des archives (originaux déplacés après optimisation). Vide = MEDIA_FOLDER/archives
ARCHIVES_FOLDER = os.environ.get("ARCHIVES_FOLDER", "").strip()
# Intégration Overseerr (recherche / découverte externe). Surchargés par app_settings si définis.
OVERSEERR_URL = os.environ.get("OVERSEERR_URL", "").strip().rstrip("/")
OVERSEERR_API_KEY = os.environ.get("OVERSEERR_API_KEY", "").strip()
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123456!")
USER_USERNAME = os.environ.get("USER_USERNAME", "user")
USER_PASSWORD = os.environ.get("USER_PASSWORD", "user123456!")


def validate_security_settings() -> None:
    if APP_ENV == "dev":
        return

    if len(APP_SECRET) < 32 or APP_SECRET == "dev-secret-change":
        raise RuntimeError("APP_SECRET insuffisant en production")

    if PASSWORD_MIN_LENGTH < 10:
        raise RuntimeError("PASSWORD_MIN_LENGTH trop faible")

    if PASSWORD_ITERATIONS < 100000:
        raise RuntimeError("PASSWORD_ITERATIONS trop faible")

    if ADMIN_PASSWORD == "admin123" or USER_PASSWORD == "user123":
        raise RuntimeError("Mots de passe par defaut interdits en production")
