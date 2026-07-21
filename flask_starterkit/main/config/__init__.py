"""The application factory."""

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from flask_starterkit.main.config.settings import BaseConfig, ConfigError, get_config
from flask_starterkit.main.errors import register_error_handlers
from flask_starterkit.main.logging_config import configure_logging
from flask_starterkit.main.routes import auth, health, home

__all__ = ["BaseConfig", "ConfigError", "create_app", "get_config"]


def create_app(config: BaseConfig | str | None = None) -> Flask:
    """Build a configured Flask application.

    Args:
        config: A config object, the name of one ("testing", "production", ...),
            or None to resolve from $APP_ENV. Tests should pass this explicitly
            rather than mutating the environment.

    Returns:
        Flask: The configured instance of the flask application.
    """
    if config is None or isinstance(config, str):
        config = get_config(config)

    # Fail before the app exists rather than serving traffic with, say, no
    # SECRET_KEY and finding out when sessions silently break.
    config.validate()

    app_instance = Flask(__name__)
    app_instance.config.from_object(config)

    configure_logging(app_instance)
    register_error_handlers(app_instance)

    hops = app_instance.config.get("TRUST_PROXY_HOPS", 0)
    if hops:
        app_instance.wsgi_app = ProxyFix(
            app_instance.wsgi_app, x_for=hops, x_proto=hops, x_host=hops, x_prefix=hops
        )

    app_instance.register_blueprint(home.home_routes)
    app_instance.register_blueprint(health.health_routes)
    app_instance.register_blueprint(auth.auth_routes, url_prefix="/api/auth")

    app_instance.logger.info(
        "Application ready", extra={"env": config.ENV_NAME, "proxy_hops": hops}
    )
    return app_instance
