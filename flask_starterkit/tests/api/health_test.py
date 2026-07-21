def test_health_reports_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["environment"] == "testing"


def test_home_route(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json == {"message": "Hello World !", "success": True}
