import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.specimen_mineral import specimen_minerals


class Specimen(Base):
    __tablename__ = "specimens"
    __table_args__ = (
        CheckConstraint("specimen_no > 0", name="ck_specimens_specimen_no_positive"),
        Index("ix_specimens_locality_id", "locality_id"),
        Index("ix_specimens_acquisition_method_id", "acquisition_method_id"),
        Index("ix_specimens_created_at", "created_at"),
        Index("ix_specimens_favorite", "favorite"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    specimen_no: Mapped[int] = mapped_column(Integer, nullable=False)
    specimen_name: Mapped[str] = mapped_column(String(255), nullable=False)
    locality_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("localities.id", ondelete="RESTRICT", onupdate="CASCADE"),
    )
    acquisition_method_id: Mapped[int | None] = mapped_column(
        ForeignKey("acquisition_methods.id", ondelete="RESTRICT", onupdate="CASCADE")
    )
    collection_date: Mapped[date | None] = mapped_column(Date)
    features: Mapped[str | None] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    favorite: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    minerals = relationship("Mineral", secondary=specimen_minerals, back_populates="specimens")
    images = relationship("Image", back_populates="specimen", passive_deletes=True)
    locality = relationship("Locality", back_populates="specimens")
    acquisition_method = relationship("AcquisitionMethod", back_populates="specimens")
