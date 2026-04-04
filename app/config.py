from dataclasses import asdict, dataclass
import os


def _env_bool(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class Settings:
    ENV: str
    TESTING: bool
    SECRET_KEY: str
    DATABASE_NAME: str
    DATABASE_HOST: str
    DATABASE_PORT: int
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_MAX_CONNECTIONS: int
    DATABASE_STALE_TIMEOUT: int
    DATABASE_POOL_TIMEOUT: int
    HEALTH_DB_TIMEOUT_MS: int
    SHORT_CODE_LENGTH: int
    SHORT_CODE_ATTEMPTS: int
    CLICK_EVENT_WORKERS: int

    def as_dict(self):
        return asdict(self)


def load_settings(overrides=None):
    settings = Settings(
        ENV=os.getenv("FLASK_ENV", "production"),
        TESTING=_env_bool("TESTING", False),
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-key"),
        DATABASE_NAME=os.getenv("DATABASE_NAME", "hackathon_db"),
        DATABASE_HOST=os.getenv("DATABASE_HOST", "localhost"),
        DATABASE_PORT=int(os.getenv("DATABASE_PORT", "5432")),
        DATABASE_USER=os.getenv("DATABASE_USER", "postgres"),
        DATABASE_PASSWORD=os.getenv("DATABASE_PASSWORD", "postgres"),
        DATABASE_MAX_CONNECTIONS=int(os.getenv("DATABASE_MAX_CONNECTIONS", "12")),
        DATABASE_STALE_TIMEOUT=int(os.getenv("DATABASE_STALE_TIMEOUT", "300")),
        DATABASE_POOL_TIMEOUT=int(os.getenv("DATABASE_POOL_TIMEOUT", "5")),
        HEALTH_DB_TIMEOUT_MS=int(os.getenv("HEALTH_DB_TIMEOUT_MS", "1000")),
        SHORT_CODE_LENGTH=int(os.getenv("SHORT_CODE_LENGTH", "6")),
        SHORT_CODE_ATTEMPTS=int(os.getenv("SHORT_CODE_ATTEMPTS", "10")),
        CLICK_EVENT_WORKERS=int(os.getenv("CLICK_EVENT_WORKERS", "2")),
    )
    if overrides:
        allowed = set(Settings.__dataclass_fields__)
        for key, value in overrides.items():
            if key in allowed:
                setattr(settings, key, value)
    return settings
