import pytest

from flask_starterkit.main.config import create_app
from flask_starterkit.main.config.settings import (
    ConfigError,
    DevelopmentConfig,
    ProductionConfig,
    get_config,
)


def test_get_config_defaults_to_development(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    assert get_config().ENV_NAME == "development"


def test_get_config_reads_app_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "x" * 32)
    assert get_config().ENV_NAME == "production"


def test_unknown_env_is_rejected():
    with pytest.raises(ConfigError, match="Unknown APP_ENV"):
        get_config("staging-typo")


def test_development_generates_an_ephemeral_secret(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    assert DevelopmentConfig().SECRET_KEY


def test_production_refuses_to_boot_without_a_secret(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "")

    with pytest.raises(ConfigError, match="SECRET_KEY must be set"):
        create_app(ProductionConfig())


def test_production_rejects_a_short_secret(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "too-short")

    with pytest.raises(ConfigError, match="at least 32 characters"):
        create_app(ProductionConfig())


def test_production_accepts_a_strong_secret(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "x" * 32)

    app = create_app(ProductionConfig())

    assert app.config["ENV_NAME"] == "production"
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True


def test_proxy_fix_is_off_by_default(monkeypatch):
    monkeypatch.delenv("TRUST_PROXY_HOPS", raising=False)
    app = create_app("testing")
    assert app.config["TRUST_PROXY_HOPS"] == 0


def test_proxy_fix_wraps_wsgi_app_when_enabled(monkeypatch):
    monkeypatch.setenv("TRUST_PROXY_HOPS", "1")
    app = create_app("testing")
    assert app.wsgi_app.__class__.__name__ == "ProxyFix"


def test_non_integer_proxy_hops_is_rejected(monkeypatch):
    monkeypatch.setenv("TRUST_PROXY_HOPS", "yes-please")

    with pytest.raises(ConfigError, match="must be an integer"):
        get_config("testing")
