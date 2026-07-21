def test_auth_global_endpoint(client):
    response = client.get("/api/auth/")

    assert response.status_code == 200
    assert response.json == {
        "message": "Welcome to your awesome auth endpoint",
        "success": True,
    }
