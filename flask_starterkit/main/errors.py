"""JSON error handlers.

An API that answers 404 with Werkzeug's HTML error page is a bad surprise for
whoever is consuming it, so every error leaves as JSON in the same envelope the
successful routes use.
"""

from flask import jsonify
from werkzeug.exceptions import HTTPException


def _envelope(code: int, name: str, message: str):
    return jsonify(
        {
            "success": False,
            "error": {"code": code, "name": name, "message": message},
        }
    )


def register_error_handlers(app) -> None:
    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        return _envelope(error.code, error.name, error.description), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error: Exception):
        # Registering a handler for Exception means Flask stops re-raising
        # unhandled errors -- including in tests, where that would silently turn
        # a real bug into a passing 500 assertion. Re-raise when the app is
        # configured to propagate so debugging still works.
        if app.config.get("PROPAGATE_EXCEPTIONS") or app.testing or app.debug:
            raise error

        app.logger.exception("Unhandled exception while serving request")
        return _envelope(
            500,
            "Internal Server Error",
            "The server encountered an internal error and was unable to complete your request.",
        ), 500
