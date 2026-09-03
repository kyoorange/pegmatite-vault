import csv
import io
import json
import uuid
import zipfile
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import ImportTokenError
from app.models.acquisition_method import AcquisitionMethod
from app.models.locality import Locality
from app.models.mineral import Mineral
from app.models.mineral_class import MineralClass
from app.models.specimen import Specimen
from app.schemas.data_import import (
    ImportCounts,
    ImportIssue,
    ImportResult,
    ImportValidation,
)

HEADERS = {
    "mineral_classes.csv": ["id", "name", "description"],
    "minerals.csv": [
        "id",
        "japanese_name",
        "english_name",
        "formula",
        "crystal_system",
        "mineral_class_id",
        "description",
    ],
    "localities.csv": [
        "id",
        "locality_name",
        "alias_name",
        "latitude",
        "longitude",
        "note",
    ],
    "acquisition_methods.csv": ["id", "name", "description"],
    "specimens.csv": [
        "id",
        "specimen_no",
        "specimen_name",
        "locality_id",
        "acquisition_method_id",
        "collection_date",
        "features",
        "note",
        "favorite",
        "created_at",
        "updated_at",
    ],
    "specimen_minerals.csv": ["specimen_id", "mineral_id"],
    "images.csv": [
        "id",
        "specimen_id",
        "archived_from_specimen_id",
        "original_filename",
        "original_extension",
        "media_type",
        "file_size",
        "caption",
        "sort_order",
        "status",
        "archived_at",
        "created_at",
    ],
}
MAX_IMPORT_BYTES = 20 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024
TOKEN_LIFETIME = timedelta(minutes=30)


def _issue(
    issues: list[ImportIssue],
    filename: str,
    row: int,
    code: str,
    message: str,
    field: str | None = None,
) -> None:
    issues.append(ImportIssue(file=filename, row=row, field=field, code=code, message=message))


def _read_archive(data: bytes) -> tuple[dict[str, list[dict[str, str]]], list[ImportIssue]]:
    issues: list[ImportIssue] = []
    tables: dict[str, list[dict[str, str]]] = {}
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        return {}, [
            ImportIssue(
                file="archive", row=1, code="invalid_zip", message="ZIP形式ではありません。"
            )
        ]
    members = [item for item in archive.infolist() if not item.is_dir()]
    if sum(item.file_size for item in members) > MAX_UNCOMPRESSED_BYTES:
        return {}, [
            ImportIssue(
                file="archive",
                row=1,
                code="archive_too_large",
                message="展開後のデータサイズが上限を超えています。",
            )
        ]
    seen_files: set[str] = set()
    for member in members:
        filename = Path(member.filename).name
        if member.filename != filename or filename not in HEADERS:
            _issue(issues, member.filename, 1, "unexpected_file", "未対応のファイルです。")
            continue
        if filename in seen_files:
            _issue(issues, filename, 1, "duplicate_file", "同じCSVが重複しています。")
            continue
        seen_files.add(filename)
        try:
            text = archive.read(member).decode("utf-8-sig")
        except UnicodeDecodeError:
            _issue(issues, filename, 1, "invalid_encoding", "UTF-8で読み取れません。")
            continue
        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames != HEADERS[filename]:
            _issue(issues, filename, 1, "invalid_header", "CSVヘッダーが一致しません。")
            continue
        tables[filename] = list(reader)
    for filename in HEADERS:
        if filename not in tables:
            _issue(issues, filename, 1, "missing_file", "必要なCSVがありません。")
    return tables, issues


def _uuid_value(
    issues: list[ImportIssue],
    filename: str,
    row: int,
    field: str,
    value: str,
    nullable: bool = False,
) -> uuid.UUID | None:
    if nullable and value == "":
        return None
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError):
        _issue(issues, filename, row, "invalid_uuid", "UUID形式が不正です。", field)
        return None


def _int_value(
    issues: list[ImportIssue],
    filename: str,
    row: int,
    field: str,
    value: str,
    nullable: bool = False,
) -> int | None:
    if nullable and value == "":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        _issue(issues, filename, row, "invalid_integer", "整数形式が不正です。", field)
        return None


def _validate_rows(
    db: Session, tables: dict[str, list[dict[str, str]]], issues: list[ImportIssue]
) -> ImportCounts:
    id_fields = {
        "mineral_classes.csv": ("id", int),
        "minerals.csv": ("id", uuid.UUID),
        "localities.csv": ("id", uuid.UUID),
        "acquisition_methods.csv": ("id", int),
        "specimens.csv": ("id", uuid.UUID),
    }
    parsed_ids: dict[str, set[object]] = {}
    model_map = {
        "mineral_classes.csv": MineralClass,
        "minerals.csv": Mineral,
        "localities.csv": Locality,
        "acquisition_methods.csv": AcquisitionMethod,
        "specimens.csv": Specimen,
    }
    counts = ImportCounts(skipped=len(tables.get("images.csv", [])))
    for filename, (field, kind) in id_fields.items():
        values: set[object] = set()
        for row_number, row in enumerate(tables.get(filename, []), 2):
            value = (
                _uuid_value(issues, filename, row_number, field, row[field])
                if kind is uuid.UUID
                else _int_value(issues, filename, row_number, field, row[field])
            )
            if value is None:
                continue
            if value in values:
                _issue(issues, filename, row_number, "duplicate_id", "IDが重複しています。", field)
            values.add(value)
        parsed_ids[filename] = values
        existing = set(
            db.scalars(select(model_map[filename].id).where(model_map[filename].id.in_(values)))
        )
        counts.updated += len(existing)
        counts.created += len(values - existing)

    available_classes = parsed_ids["mineral_classes.csv"] | set(db.scalars(select(MineralClass.id)))
    available_localities = parsed_ids["localities.csv"] | set(db.scalars(select(Locality.id)))
    available_methods = parsed_ids["acquisition_methods.csv"] | set(
        db.scalars(select(AcquisitionMethod.id))
    )
    available_minerals = parsed_ids["minerals.csv"] | set(db.scalars(select(Mineral.id)))
    available_specimens = parsed_ids["specimens.csv"] | set(db.scalars(select(Specimen.id)))

    for number, row in enumerate(tables.get("minerals.csv", []), 2):
        class_id = _int_value(
            issues, "minerals.csv", number, "mineral_class_id", row["mineral_class_id"], True
        )
        if class_id is not None and class_id not in available_classes:
            _issue(
                issues,
                "minerals.csv",
                number,
                "missing_reference",
                "鉱物分類が存在しません。",
                "mineral_class_id",
            )
    for number, row in enumerate(tables.get("specimens.csv", []), 2):
        if not row["specimen_name"].strip():
            _issue(
                issues, "specimens.csv", number, "required", "標本名は必須です。", "specimen_name"
            )
        _int_value(issues, "specimens.csv", number, "specimen_no", row["specimen_no"])
        locality_id = _uuid_value(
            issues, "specimens.csv", number, "locality_id", row["locality_id"], True
        )
        method_id = _int_value(
            issues,
            "specimens.csv",
            number,
            "acquisition_method_id",
            row["acquisition_method_id"],
            True,
        )
        if locality_id is not None and locality_id not in available_localities:
            _issue(
                issues,
                "specimens.csv",
                number,
                "missing_reference",
                "採集地が存在しません。",
                "locality_id",
            )
        if method_id is not None and method_id not in available_methods:
            _issue(
                issues,
                "specimens.csv",
                number,
                "missing_reference",
                "入手経路が存在しません。",
                "acquisition_method_id",
            )
    for number, row in enumerate(tables.get("specimen_minerals.csv", []), 2):
        specimen_id = _uuid_value(
            issues, "specimen_minerals.csv", number, "specimen_id", row["specimen_id"]
        )
        mineral_id = _uuid_value(
            issues, "specimen_minerals.csv", number, "mineral_id", row["mineral_id"]
        )
        if specimen_id is not None and specimen_id not in available_specimens:
            _issue(
                issues,
                "specimen_minerals.csv",
                number,
                "missing_reference",
                "標本が存在しません。",
                "specimen_id",
            )
        if mineral_id is not None and mineral_id not in available_minerals:
            _issue(
                issues,
                "specimen_minerals.csv",
                number,
                "missing_reference",
                "鉱物が存在しません。",
                "mineral_id",
            )
    return counts


def validate_import(db: Session, settings: Settings, file: UploadFile) -> ImportValidation:
    data = file.file.read(MAX_IMPORT_BYTES + 1)
    if len(data) > MAX_IMPORT_BYTES:
        return ImportValidation(
            valid=False,
            issues=[
                ImportIssue(
                    file="archive",
                    row=1,
                    code="file_too_large",
                    message="ファイルサイズが上限を超えています。",
                )
            ],
            preview=ImportCounts(),
        )
    tables, issues = _read_archive(data)
    preview = _validate_rows(db, tables, issues) if tables else ImportCounts()
    if issues:
        return ImportValidation(valid=False, issues=issues, preview=preview)
    token = uuid.uuid4()
    expires_at = datetime.now(UTC) + TOKEN_LIFETIME
    staging = settings.images_directory.parent / "imports"
    staging.mkdir(parents=True, exist_ok=True)
    (staging / f"{token}.json").write_text(
        json.dumps({"expires_at": expires_at.isoformat(), "tables": tables}, ensure_ascii=False),
        encoding="utf-8",
    )
    return ImportValidation(
        valid=True,
        commit_token=token,
        expires_at=expires_at,
        issues=[],
        preview=preview,
    )


def _none(value: str) -> str | None:
    return value or None


def _date(value: str) -> date | None:
    return date.fromisoformat(value) if value else None


def _datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _decimal(value: str) -> Decimal | None:
    try:
        return Decimal(value) if value else None
    except InvalidOperation as exc:
        raise ImportTokenError("検証後のデータが変更されています。") from exc


def commit_import(db: Session, settings: Settings, token: uuid.UUID) -> ImportResult:
    staged = settings.images_directory.parent / "imports" / f"{token}.json"
    if not staged.exists():
        raise ImportTokenError("検証トークンが存在しないか、すでに使用されています。")
    payload = json.loads(staged.read_text(encoding="utf-8"))
    if datetime.fromisoformat(payload["expires_at"]) < datetime.now(UTC):
        staged.unlink(missing_ok=True)
        raise ImportTokenError("検証トークンの有効期限が切れています。")
    tables = payload["tables"]
    issues: list[ImportIssue] = []
    preview = _validate_rows(db, tables, issues)
    if issues:
        raise ImportTokenError("検証後にDB状態が変化したため、もう一度検証してください。")
    try:
        for row in tables["mineral_classes.csv"]:
            item_id = int(row["id"])
            item = db.get(MineralClass, item_id) or MineralClass(id=item_id)
            item.name, item.description = row["name"], _none(row["description"])
            db.add(item)
        for row in tables["localities.csv"]:
            item_id = uuid.UUID(row["id"])
            item = db.get(Locality, item_id) or Locality(id=item_id)
            item.locality_name = row["locality_name"]
            item.alias_name = _none(row["alias_name"])
            item.latitude = _decimal(row["latitude"])
            item.longitude = _decimal(row["longitude"])
            item.note = _none(row["note"])
            db.add(item)
        for row in tables["acquisition_methods.csv"]:
            item_id = int(row["id"])
            item = db.get(AcquisitionMethod, item_id) or AcquisitionMethod(id=item_id)
            item.name, item.description = row["name"], _none(row["description"])
            db.add(item)
        db.flush()
        for row in tables["minerals.csv"]:
            item_id = uuid.UUID(row["id"])
            item = db.get(Mineral, item_id) or Mineral(id=item_id)
            item.japanese_name = row["japanese_name"]
            item.english_name = _none(row["english_name"])
            item.formula = _none(row["formula"])
            item.crystal_system = _none(row["crystal_system"])
            item.mineral_class_id = (
                int(row["mineral_class_id"]) if row["mineral_class_id"] else None
            )
            item.description = _none(row["description"])
            db.add(item)
        db.flush()
        for row in tables["specimens.csv"]:
            item_id = uuid.UUID(row["id"])
            item = db.get(Specimen, item_id) or Specimen(id=item_id)
            item.specimen_no = int(row["specimen_no"])
            item.specimen_name = row["specimen_name"]
            item.locality_id = uuid.UUID(row["locality_id"]) if row["locality_id"] else None
            item.acquisition_method_id = (
                int(row["acquisition_method_id"]) if row["acquisition_method_id"] else None
            )
            item.collection_date = _date(row["collection_date"])
            item.features = _none(row["features"])
            item.note = _none(row["note"])
            item.favorite = row["favorite"].lower() in {"true", "1", "yes"}
            item.created_at = _datetime(row["created_at"])
            item.updated_at = _datetime(row["updated_at"])
            db.add(item)
        db.flush()
        links: dict[uuid.UUID, list[uuid.UUID]] = {}
        for row in tables["specimen_minerals.csv"]:
            links.setdefault(uuid.UUID(row["specimen_id"]), []).append(uuid.UUID(row["mineral_id"]))
        imported_specimen_ids = [uuid.UUID(row["id"]) for row in tables["specimens.csv"]]
        for specimen_id in imported_specimen_ids:
            db.get(Specimen, specimen_id).minerals = (
                [db.get(Mineral, mineral_id) for mineral_id in mineral_ids]
                if (mineral_ids := links.get(specimen_id, []))
                else []
            )
        for table_name in ("mineral_classes", "acquisition_methods"):
            db.execute(
                text(
                    f"SELECT setval("
                    f"pg_get_serial_sequence('{table_name}', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM {table_name}), 1), "
                    f"EXISTS(SELECT 1 FROM {table_name})"
                    f")"
                )
            )
        db.commit()
    except Exception:
        db.rollback()
        raise
    staged.unlink(missing_ok=True)
    return ImportResult(**preview.model_dump())
