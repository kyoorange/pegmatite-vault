from sqlalchemy import Column, ForeignKey, Index, Table
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base

specimen_minerals = Table(
    "specimen_minerals",
    Base.metadata,
    Column(
        "specimen_id",
        UUID(as_uuid=True),
        ForeignKey("specimens.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    ),
    Column(
        "mineral_id",
        UUID(as_uuid=True),
        ForeignKey("minerals.id", ondelete="RESTRICT", onupdate="CASCADE"),
        primary_key=True,
    ),
    Index("ix_specimen_minerals_mineral_id", "mineral_id"),
)
