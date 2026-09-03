"""initial schema

Revision ID: 20260726_0001
Revises:
Create Date: 2026-07-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260726_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "acquisition_methods",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "localities",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("locality_name", sa.String(length=255), nullable=False),
        sa.Column("alias_name", sa.String(length=255), nullable=True),
        sa.Column("latitude", sa.Numeric(precision=10, scale=7), nullable=True),
        sa.Column("longitude", sa.Numeric(precision=10, scale=7), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "latitude IS NULL OR latitude BETWEEN -90 AND 90",
            name="ck_localities_latitude_range",
        ),
        sa.CheckConstraint(
            "longitude IS NULL OR longitude BETWEEN -180 AND 180",
            name="ck_localities_longitude_range",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "mineral_classes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "minerals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("japanese_name", sa.String(length=255), nullable=False),
        sa.Column("english_name", sa.String(length=255), nullable=True),
        sa.Column("formula", sa.String(length=255), nullable=True),
        sa.Column("crystal_system", sa.String(length=100), nullable=True),
        sa.Column("mineral_class_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["mineral_class_id"],
            ["mineral_classes.id"],
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_minerals_mineral_class_id", "minerals", ["mineral_class_id"])
    op.create_table(
        "specimens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("specimen_no", sa.Integer(), nullable=False),
        sa.Column("specimen_name", sa.String(length=255), nullable=False),
        sa.Column("locality_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("acquisition_method_id", sa.Integer(), nullable=True),
        sa.Column("collection_date", sa.Date(), nullable=True),
        sa.Column("features", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("favorite", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("specimen_no > 0", name="ck_specimens_specimen_no_positive"),
        sa.ForeignKeyConstraint(
            ["acquisition_method_id"],
            ["acquisition_methods.id"],
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["locality_id"], ["localities.id"], onupdate="CASCADE", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_specimens_acquisition_method_id", "specimens", ["acquisition_method_id"])
    op.create_index("ix_specimens_created_at", "specimens", ["created_at"])
    op.create_index("ix_specimens_favorite", "specimens", ["favorite"])
    op.create_index("ix_specimens_locality_id", "specimens", ["locality_id"])
    op.create_table(
        "images",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("specimen_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("archived_from_specimen_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("original_extension", sa.String(length=10), nullable=False),
        sa.Column("media_type", sa.String(length=100), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("caption", sa.String(length=255), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "status", sa.String(length=20), server_default=sa.text("'active'"), nullable=False
        ),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("file_size >= 0", name="ck_images_file_size_nonnegative"),
        sa.CheckConstraint("sort_order >= 0", name="ck_images_sort_order_nonnegative"),
        sa.CheckConstraint("status IN ('active', 'archived')", name="ck_images_status"),
        sa.CheckConstraint(
            "(status = 'active' AND specimen_id IS NOT NULL "
            "AND archived_from_specimen_id IS NULL AND archived_at IS NULL) OR "
            "(status = 'archived' AND specimen_id IS NULL "
            "AND archived_from_specimen_id IS NOT NULL AND archived_at IS NOT NULL)",
            name="ck_images_status_fields",
        ),
        sa.ForeignKeyConstraint(
            ["specimen_id"], ["specimens.id"], onupdate="CASCADE", ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_images_specimen_sort_order", "images", ["specimen_id", "sort_order"])
    op.create_index("ix_images_status_archived_at", "images", ["status", "archived_at"])
    op.create_table(
        "specimen_minerals",
        sa.Column("specimen_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mineral_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["mineral_id"], ["minerals.id"], onupdate="CASCADE", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["specimen_id"], ["specimens.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("specimen_id", "mineral_id"),
    )
    op.create_index("ix_specimen_minerals_mineral_id", "specimen_minerals", ["mineral_id"])


def downgrade() -> None:
    op.drop_index("ix_specimen_minerals_mineral_id", table_name="specimen_minerals")
    op.drop_table("specimen_minerals")
    op.drop_index("ix_images_status_archived_at", table_name="images")
    op.drop_index("ix_images_specimen_sort_order", table_name="images")
    op.drop_table("images")
    op.drop_index("ix_specimens_locality_id", table_name="specimens")
    op.drop_index("ix_specimens_favorite", table_name="specimens")
    op.drop_index("ix_specimens_created_at", table_name="specimens")
    op.drop_index("ix_specimens_acquisition_method_id", table_name="specimens")
    op.drop_table("specimens")
    op.drop_index("ix_minerals_mineral_class_id", table_name="minerals")
    op.drop_table("minerals")
    op.drop_table("mineral_classes")
    op.drop_table("localities")
    op.drop_table("acquisition_methods")
