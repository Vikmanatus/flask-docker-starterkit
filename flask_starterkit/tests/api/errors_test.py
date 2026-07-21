"""Errors must leave as JSON, not as Werkzeug's HTML error page."""


def test_unknown_route_returns_json_404(client):
    response = client.get("/definitely-not-a-route")

    assert response.status_code == 404
    assert response.is_json
    assert response.json["success"] is False
    assert response.json["error"]["code"] == 404


def test_wrong_method_returns_json_405(client):
    response = client.post("/health")

    assert response.status_code == 405
    assert response.is_json
    assert response.json["error"]["code"] == 405


def test_unhandled_exception_is_reported_as_json_when_not_propagating(app):
    @app.route("/boom")
    def boom():
        raise RuntimeError("kaboom")

    # Production behaviour: the traceback is logged, the client gets a clean 500.
    # Tests propagate by default, so opt out explicitly for this one case.
    app.config["PROPAGATE_EXCEPTIONS"] = False
    app.testing = False
    app.debug = False

    response = app.test_client().get("/boom")

    assert response.status_code == 500
    assert response.is_json
    assert response.json["success"] is False
    # The internal message must not leak to the client.
    assert "kaboom" not in response.get_data(as_text=True)
