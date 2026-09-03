import uuid

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.specimen_mineral import specimen_minerals


class Mineral(Base):
    __tablename__ = "minerals"
    __table_args__ = (Index("ix_minerals_mineral_class_id", "mineral_class_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    japanese_name: Mapped[str] = mapped_column(String(255), nullable=False)
    english_name: Mapped[str | None] = mapped_column(String(255))
    formula: Mapped[str | None] = mapped_column(String(255))
    crystal_system: Mapped[str | None] = mapped_column(String(100))
    mineral_class_id: Mapped[int | None] = mapped_column(
        ForeignKey("mineral_classes.id", ondelete="RESTRICT", onupdate="CASCADE")
    )
    description: Mapped[str | None] = mapped_column(Text)

    mineral_class = relationship("MineralClass", back_populates="minerals")
    specimens = relationship("Specimen", secondary=specimen_minerals, back_populates="minerals")
