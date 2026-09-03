import uuid
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base


class Image(Base):
    __tablename__ = "images"
    __table_args__ = (
        CheckConstraint("file_size >= 0", name="ck_images_file_size_nonnegative"),
        CheckConstraint("sort_order >= 0", name="ck_images_sort_order_nonnegative"),
        CheckConstraint("status IN ('active', 'archived')", name="ck_images_status"),
        CheckConstraint(
            "("
            "status = 'active' AND specimen_id IS NOT NULL "
            "AND archived_from_specimen_id IS NULL AND archived_at IS NULL"
            ") OR ("
            "status = 'archived' AND specimen_id IS NULL "
            "AND archived_from_specimen_id IS NOT NULL AND archived_at IS NOT NULL"
            ")",
            name="ck_images_status_fields",
        ),
        Index("ix_images_specimen_sort_order", "specimen_id", "sort_order"),
        Index("ix_images_status_archived_at", "status", "archived_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    specimen_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("specimens.id", ondelete="SET NULL", onupdate="CASCADE"),
    )
    archived_from_specimen_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_extension: Mapped[str] = mapped_column(String(10), nullable=False)
    media_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    caption: Mapped[str | None] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active"
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    specimen = relationship("Specimen", back_populates="images")
