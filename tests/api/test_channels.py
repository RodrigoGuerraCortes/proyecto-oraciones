from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_get_channels_returns_list():
    response = client.get("/channels")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
