import os
from dotenv import load_dotenv

load_dotenv()


def _to_bool(value):
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


class Config:
    SECRET_KEY = os.getenv("SESSION_SECRET") or os.getenv("SECRET_KEY", "change_me")
    SESSION_TYPE = os.getenv("SESSION_TYPE", "filesystem")
    SESSION_PERMANENT = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    _env = (os.getenv("FLASK_ENV") or os.getenv("NODE_ENV") or "").lower()
    SESSION_COOKIE_SECURE = _to_bool(
        os.getenv("SESSION_COOKIE_SECURE", "true" if _env == "production" else "false")
    )

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "online_exam_system")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_SSL = _to_bool(os.getenv("DB_SSL", "false"))
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
    DATABASE_URL = os.getenv("DATABASE_URL", "")

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
