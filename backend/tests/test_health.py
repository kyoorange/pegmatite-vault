from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app


class FakeSession:
    def execute(self, _statement: object) -> None:
        return None


def override_get_db():
    yield FakeSession()


def test_health() -> None:
    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {
            "status": "ok",
            "database": "ok",
            "image_storage": "ok",
        }
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["referrer-policy"] == "no-referrer"
        assert response.headers["permissions-policy"] == (
            "camera=(), microphone=(), geolocation=()"
        )
    finally:
        app.dependency_overrides.clear()
