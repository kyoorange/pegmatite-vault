import io
import os

import pytest
from fastapi.testclient import TestClient
from PIL import Image as PillowImage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.db.session import get_db
from app.main import app

pytestmark = pytest.mark.integration


@pytest.fixture
def integration_client(tmp_path):
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is not configured")
    engine = create_engine(database_url)
    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    def override_get_db():
        with session_factory() as session:
            yield session

    settings = get_settings().model_copy(
        update={
            "image_storage_root": tmp_path / "images",
            "runtime_settings_file": tmp_path / "runtime-settings.json",
        }
    )
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = lambda: settings
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def _png() -> bytes:
    output = io.BytesIO()
    PillowImage.new("RGB", (48, 48), "green").save(output, "PNG")
    return output.getvalue()


def test_specimen_and_image_lifecycle(integration_client: TestClient):
    created = integration_client.post(
        "/api/specimens",
        json={
            "specimen_name": "Integration specimen",
            "favorite": True,
            "mineral_ids": [],
        },
    )
    assert created.status_code == 201
    specimen = created.json()
    specimen_id = specimen["id"]
    assert specimen["specimen_no"] == 1

    fetched = integration_client.get(f"/api/specimens/{specimen_id}")
    assert fetched.status_code == 200
    assert fetched.json()["specimen_name"] == "Integration specimen"

    updated = integration_client.patch(
        f"/api/specimens/{specimen_id}",
        json={"specimen_name": "Updated integration specimen"},
    )
    assert updated.status_code == 200
    assert updated.json()["specimen_name"] == "Updated integration specimen"

    uploaded = integration_client.post(
        f"/api/specimens/{specimen_id}/images",
        files={"file": ("integration.png", _png(), "image/png")},
    )
    assert uploaded.status_code == 201
    image_id = uploaded.json()["id"]

    thumbnail = integration_client.get(
        f"/api/images/{image_id}/content",
        params={"variant": "thumbnail"},
    )
    assert thumbnail.status_code == 200
    assert thumbnail.headers["content-type"] == "image/webp"

    assert integration_client.delete(f"/api/images/{image_id}").status_code == 204
    archives = integration_client.get("/api/archived-images")
    assert archives.status_code == 200
    assert any(item["id"] == image_id for item in archives.json()["items"])

    restored = integration_client.post(
        f"/api/images/{image_id}/restore",
        json={"specimen_id": specimen_id},
    )
    assert restored.status_code == 200
    assert restored.json()["status"] == "active"

    assert integration_client.delete(f"/api/images/{image_id}").status_code == 204
    assert integration_client.delete(f"/api/images/{image_id}/permanent").status_code == 204
    assert integration_client.delete(f"/api/specimens/{specimen_id}").status_code == 204
