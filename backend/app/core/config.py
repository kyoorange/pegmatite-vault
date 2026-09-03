import json
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    image_storage_root: Path = Path("./storage")
    runtime_settings_file: Path = Path("./storage/runtime-settings.json")
    image_max_upload_bytes: int = Field(default=20 * 1024 * 1024, gt=0)
    image_display_max_px: int = Field(default=1920, gt=0)
    image_thumbnail_max_px: int = Field(default=480, gt=0)
    cors_origins: str = "http://localhost:5173"
    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def images_directory(self) -> Path:
        return self.effective_image_storage_root / "images"

    @property
    def runtime_settings_path(self) -> Path:
        path = self.runtime_settings_file.expanduser()
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path.resolve()

    @property
    def effective_image_storage_root(self) -> Path:
        root = self.image_storage_root.expanduser()
        try:
            if self.runtime_settings_path.exists():
                payload = json.loads(self.runtime_settings_path.read_text(encoding="utf-8"))
                if payload.get("image_storage_root"):
                    root = Path(payload["image_storage_root"]).expanduser()
        except (OSError, ValueError, TypeError):
            pass
        if not root.is_absolute():
            root = PROJECT_ROOT / root
        return root.resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
