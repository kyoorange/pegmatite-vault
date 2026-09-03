import csv
import io
import zipfile

import pytest

from app.services.data_import import HEADERS, _read_archive


def _csv_content(headers: list[str]) -> str:
    output = io.StringIO(newline="")
    csv.writer(output).writerow(headers)
    return output.getvalue()


def _archive(entries: list[tuple[str, str]]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for filename, content in entries:
            archive.writestr(filename, content)
    return output.getvalue()


def test_import_archive_accepts_export_shape():
    data = _archive([(filename, _csv_content(headers)) for filename, headers in HEADERS.items()])

    tables, issues = _read_archive(data)

    assert issues == []
    assert set(tables) == set(HEADERS)


def test_import_archive_rejects_path_traversal():
    entries = [(filename, _csv_content(headers)) for filename, headers in HEADERS.items()]
    entries.append(("../specimens.csv", _csv_content(HEADERS["specimens.csv"])))

    _, issues = _read_archive(_archive(entries))

    assert any(issue.code == "unexpected_file" for issue in issues)


def test_import_archive_rejects_duplicate_csv():
    entries = [(filename, _csv_content(headers)) for filename, headers in HEADERS.items()]
    entries.append(("specimens.csv", _csv_content(HEADERS["specimens.csv"])))

    with pytest.warns(UserWarning, match="Duplicate name"):
        archive = _archive(entries)
    _, issues = _read_archive(archive)

    assert any(issue.code == "duplicate_file" for issue in issues)
