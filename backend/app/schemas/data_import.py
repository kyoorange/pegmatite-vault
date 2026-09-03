import uuid
from datetime import datetime

from pydantic import BaseModel


class ImportIssue(BaseModel):
    file: str
    row: int
    field: str | None = None
    code: str
    message: str


class ImportCounts(BaseModel):
    created: int = 0
    updated: int = 0
    skipped: int = 0


class ImportValidation(BaseModel):
    valid: bool
    commit_token: uuid.UUID | None = None
    expires_at: datetime | None = None
    issues: list[ImportIssue]
    preview: ImportCounts


class ImportCommit(BaseModel):
    commit_token: uuid.UUID


class ImportResult(ImportCounts):
    pass
