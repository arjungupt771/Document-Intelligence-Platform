"""initial documents and extractions tables

Revision ID: 0001
Revises:
Create Date: 2026-09-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# NOTE: document_type/status are plain VARCHAR + CHECK, not native Postgres
# ENUM types, to match the ORM's `Enum(..., native_enum=False)` columns in
# app/storage/models.py (a real ENUM type would need `ALTER TYPE ... ADD
# VALUE` migrations forever; a CHECK constraint is a normal column change).


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("document_type", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="uploaded"),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("content_hash", name="uq_documents_content_hash"),
        sa.CheckConstraint(
            "document_type IN ('unknown','invoice','purchase_order','contract')",
            name="ck_documents_document_type",
        ),
        sa.CheckConstraint(
            "status IN ('uploaded','queued','processing','ready','failed')",
            name="ck_documents_status",
        ),
    )
    op.create_index("ix_documents_status", "documents", ["status"])
    op.create_index("ix_documents_document_type", "documents", ["document_type"])

    op.create_table(
        "extractions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("document_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("field_confidence", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("error_message", sa.String(length=2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "document_type IN ('unknown','invoice','purchase_order','contract')",
            name="ck_extractions_document_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending','completed','failed')",
            name="ck_extractions_status",
        ),
    )
    op.create_index("ix_extractions_document_id", "extractions", ["document_id"])
    op.create_index("ix_extractions_status", "extractions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_extractions_status", table_name="extractions")
    op.drop_index("ix_extractions_document_id", table_name="extractions")
    op.drop_table("extractions")

    op.drop_index("ix_documents_document_type", table_name="documents")
    op.drop_index("ix_documents_status", table_name="documents")
    op.drop_table("documents")
