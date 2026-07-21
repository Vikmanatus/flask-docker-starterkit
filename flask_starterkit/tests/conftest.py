"""Shared fixtures.

Tests build the app with an explicit config rather than relying on $APP_ENV, so
a stray environment variable in a shell or CI runner cannot change what is
under test.
"""

import pytest

from flask_starterkit.main.config import create_app


@pytest.fixture
def app():
    return create_app("testing")


@pytest.fixture
def client(app):
    return app.test_client()
