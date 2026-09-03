import csv
import io
import zipfile
from collections.abc import Iterable
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.acquisition_method import AcquisitionMethod
from app.models.image import Image
from app.models.locality import Locality
from app.models.mineral import Mineral
from app.models.mineral_class import MineralClass
from app.models.specimen import Specimen
from app.models.specimen_mineral import specimen_minerals


def _value(value: object) -> object:
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _csv_bytes(headers: list[str], rows: Iterable[Iterable[object]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([_value(value) for value in row])
    return output.getvalue().encode("utf-8-sig")


def build_export(db: Session) -> tuple[bytes, str]:
    files = {
        "mineral_classes.csv": _csv_bytes(
            ["id", "name", "description"],
            (
                (item.id, item.name, item.description)
                for item in db.scalars(select(MineralClass).order_by(MineralClass.id))
            ),
        ),
        "minerals.csv": _csv_bytes(
            [
                "id",
                "japanese_name",
                "english_name",
                "formula",
                "crystal_system",
                "mineral_class_id",
                "description",
            ],
            (
                (
                    item.id,
                    item.japanese_name,
                    item.english_name,
                    item.formula,
                    item.crystal_system,
                    item.mineral_class_id,
                    item.description,
                )
                for item in db.scalars(select(Mineral).order_by(Mineral.id))
            ),
        ),
        "localities.csv": _csv_bytes(
            ["id", "locality_name", "alias_name", "latitude", "longitude", "note"],
            (
                (
                    item.id,
                    item.locality_name,
                    item.alias_name,
                    item.latitude,
                    item.longitude,
                    item.note,
                )
                for item in db.scalars(select(Locality).order_by(Locality.id))
            ),
        ),
        "acquisition_methods.csv": _csv_bytes(
            ["id", "name", "description"],
            (
                (item.id, item.name, item.description)
                for item in db.scalars(select(AcquisitionMethod).order_by(AcquisitionMethod.id))
            ),
        ),
        "specimens.csv": _csv_bytes(
            [
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
            (
                (
                    item.id,
                    item.specimen_no,
                    item.specimen_name,
                    item.locality_id,
                    item.acquisition_method_id,
                    item.collection_date,
                    item.features,
                    item.note,
                    item.favorite,
                    item.created_at,
                    item.updated_at,
                )
                for item in db.scalars(select(Specimen).order_by(Specimen.id))
            ),
        ),
        "specimen_minerals.csv": _csv_bytes(
            ["specimen_id", "mineral_id"],
            db.execute(
                select(
                    specimen_minerals.c.specimen_id,
                    specimen_minerals.c.mineral_id,
                ).order_by(
                    specimen_minerals.c.specimen_id,
                    specimen_minerals.c.mineral_id,
                )
            ),
        ),
        "images.csv": _csv_bytes(
            [
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
            (
                (
                    item.id,
                    item.specimen_id,
                    item.archived_from_specimen_id,
                    item.original_filename,
                    item.original_extension,
                    item.media_type,
                    item.file_size,
                    item.caption,
                    item.sort_order,
                    item.status,
                    item.archived_at,
                    item.created_at,
                )
                for item in db.scalars(select(Image).order_by(Image.id))
            ),
        ),
    }
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for filename, content in files.items():
            zip_file.writestr(filename, content)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return archive.getvalue(), f"pegmatite-vault-export-{timestamp}.zip"
