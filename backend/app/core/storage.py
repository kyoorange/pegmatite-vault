import functools
import hashlib
import json
import shutil
import uuid
from collections.abc import Callable
from pathlib import Path
from threading import RLock

from app.core.config import Settings

storage_operation_lock = RLock()


def synchronized_storage[StorageFunction: Callable](
    function: StorageFunction,
) -> StorageFunction:
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        with storage_operation_lock:
            return function(*args, **kwargs)

    return wrapper


def ensure_image_storage(settings: Settings) -> Path:
    directory = settings.images_directory
    directory.mkdir(parents=True, exist_ok=True)
    probe = directory / ".write-test"
    probe.touch(exist_ok=True)
    probe.unlink()
    return directory


def image_storage_is_writable(settings: Settings) -> bool:
    try:
        ensure_image_storage(settings)
    except OSError:
        return False
    return True


def _directory_stats(path: Path) -> tuple[int, int]:
    file_count = 0
    total_bytes = 0
    if path.exists():
        for item in path.rglob("*"):
            if item.is_file():
                file_count += 1
                total_bytes += item.stat().st_size
    return file_count, total_bytes


def validate_storage_target(settings: Settings, target: str) -> dict:
    source_root = settings.effective_image_storage_root
    target_root = Path(target).expanduser()
    if not target_root.is_absolute():
        target_root = (source_root.parent / target_root).resolve()
    else:
        target_root = target_root.resolve()
    same_path = target_root == source_root
    source_files, source_bytes = _directory_stats(settings.images_directory)
    issues: list[str] = []
    try:
        target_root.mkdir(parents=True, exist_ok=True)
        probe = target_root / f".write-test-{uuid.uuid4()}"
        probe.touch()
        probe.unlink()
        free_bytes = shutil.disk_usage(target_root).free
    except OSError as exc:
        free_bytes = 0
        issues.append(f"保存先へ書き込めません: {exc}")
    target_images = target_root / "images"
    if (
        not same_path
        and target_images.exists()
        and (not target_images.is_dir() or any(target_images.iterdir()))
    ):
        issues.append("移行先のimagesディレクトリが空ではありません。")
    if not same_path and free_bytes < source_bytes:
        issues.append("移行先の空き容量が不足しています。")
    return {
        "source_path": str(source_root),
        "target_path": str(target_root),
        "file_count": source_files,
        "total_bytes": source_bytes,
        "free_bytes": free_bytes,
        "same_path": same_path,
        "ready": not issues,
        "issues": issues,
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@synchronized_storage
def migrate_storage(settings: Settings, target: str) -> dict:
    validation = validate_storage_target(settings, target)
    if not validation["ready"] or validation["same_path"]:
        return validation
    source_images = settings.images_directory
    target_root = Path(validation["target_path"])
    target_images = target_root / "images"
    staging = target_root / f".pegmatite-migration-{uuid.uuid4()}"
    try:
        shutil.copytree(source_images, staging)
        for source_file in source_images.rglob("*"):
            if not source_file.is_file():
                continue
            relative = source_file.relative_to(source_images)
            copied_file = staging / relative
            if not copied_file.exists() or _sha256(source_file) != _sha256(copied_file):
                raise OSError(f"チェックサムが一致しません: {relative}")
        if target_images.exists():
            target_images.rmdir()
        staging.rename(target_images)
        settings.runtime_settings_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = settings.runtime_settings_path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(
                {"image_storage_root": str(target_root)},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        temporary.replace(settings.runtime_settings_path)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return validation
