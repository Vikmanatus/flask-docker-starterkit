"""Per-environment configuration objects.

Config is read from the environment at *instantiation* time, not at import
time. That is deliberate: it means `create_app()` sees whatever `load_dotenv()`
put in the environment regardless of module import order, and it lets tests
build a config with a patched environment without reimporting anything.
"""

import os
import secrets

# Values that count as "true" in an environment variable.
_TRUTHY = {"1", "true", "yes", "on"}


class ConfigError(RuntimeError):
    """Raised when the environment is missing configuration required to boot."""


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in _TRUTHY


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from exc


class BaseConfig:
    """Settings shared by every environment.

    Only UPPERCASE attributes are picked up by `Flask.config.from_object`.
    """

    ENV_NAME = "base"
    DEBUG = False
    TESTING = False

    def __init__(self) -> None:
        self.SECRET_KEY = os.getenv("SECRET_KEY", "")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
        self.LOG_FORMAT = os.getenv("LOG_FORMAT", "plain").lower()

        # Number of reverse-proxy hops to trust for X-Forwarded-* headers.
        # 0 disables ProxyFix entirely. Only raise this when the app really is
        # behind that many proxies -- otherwise clients can spoof their own IP
        # and scheme by sending the headers directly.
        self.TRUST_PROXY_HOPS = _env_int("TRUST_PROXY_HOPS", 0)

        # Example of a non-sensitive value that ships with the kit.
        self.YOUR_AWESOME_CONFIG_ENV = "your awesome non sensitive value"

    def validate(self) -> None:
        """Fail fast on an unusable configuration. Overridden per environment."""


class DevelopmentConfig(BaseConfig):
    ENV_NAME = "development"
    DEBUG = True

    def __init__(self) -> None:
        super().__init__()
        if not self.SECRET_KEY:
            # Ephemeral, so sessions work locally without inventing a value that
            # someone might later paste into production. It changes on restart,
            # which logs every session out -- that is the intended nudge.
            self.SECRET_KEY = secrets.token_urlsafe(32)


class TestingConfig(BaseConfig):
    ENV_NAME = "testing"
    TESTING = True

    def __init__(self) -> None:
        super().__init__()
        self.SECRET_KEY = self.SECRET_KEY or "testing-secret-not-for-real-use"
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING").upper()


class ProductionConfig(BaseConfig):
    ENV_NAME = "production"

    def __init__(self) -> None:
        super().__init__()
        self.LOG_FORMAT = os.getenv("LOG_FORMAT", "json").lower()
        self.SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", True)
        self.SESSION_COOKIE_HTTPONLY = True
        self.SESSION_COOKIE_SAMESITE = "Lax"
        self.PREFERRED_URL_SCHEME = "https"

    def validate(self) -> None:
        if not self.SECRET_KEY:
            raise ConfigError(
                "SECRET_KEY must be set when APP_ENV=production. "
                "Generate one with: python -c 'import secrets;"
                "print(secrets.token_urlsafe(32))'"
            )
        if len(self.SECRET_KEY) < 32:
            raise ConfigError("SECRET_KEY must be at least 32 characters long.")


_CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None) -> BaseConfig:
    """Build the config object for `name`, defaulting to $APP_ENV."""
    resolved = (name or os.getenv("APP_ENV") or "development").strip().lower()
    try:
        return _CONFIGS[resolved]()
    except KeyError:
        known = ", ".join(sorted(_CONFIGS))
        raise ConfigError(f"Unknown APP_ENV {resolved!r}. Expected one of: {known}") from None
