from app.core.config import Settings
from app.core.storage import migrate_storage, validate_storage_target


def test_storage_migration_copies_and_switches_without_deleting_source(tmp_path):
    source = tmp_path / "source"
    source_image = source / "images" / "image-id" / "original.jpg"
    source_image.parent.mkdir(parents=True)
    source_image.write_bytes(b"pegmatite-vault-image")
    target = tmp_path / "target"
    runtime_settings = tmp_path / "runtime-settings.json"
    settings = Settings(
        database_url="postgresql+psycopg://unused",
        image_storage_root=source,
        runtime_settings_file=runtime_settings,
    )

    preview = validate_storage_target(settings, str(target))
    assert preview["ready"] is True
    assert preview["file_count"] == 1

    result = migrate_storage(settings, str(target))

    assert result["ready"] is True
    assert source_image.exists()
    assert (target / "images" / "image-id" / "original.jpg").read_bytes() == (
        b"pegmatite-vault-image"
    )
    assert settings.effective_image_storage_root == target.resolve()
