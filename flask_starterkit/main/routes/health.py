"""Liveness endpoint for orchestrators, load balancers and the Docker HEALTHCHECK.

Deliberately does no I/O: it answers "is this process able to serve requests",
not "are its dependencies up". Once you add a database, add a separate
readiness endpoint for that -- conflating the two makes a slow dependency look
like a dead app and gets healthy containers killed.
"""

from flask import Blueprint, current_app

health_routes = Blueprint("health_routes", __name__)


@health_routes.route("/health")
def health():
    return {
        "status": "ok",
        "environment": current_app.config.get("ENV_NAME", "unknown"),
    }
