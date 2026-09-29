"""create insights table

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "insights",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("insight_type", sa.String(length=32), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=4096), nullable=False),
        sa.Column("narrative", sa.String(length=4096), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("priority_score", sa.Float(), nullable=True),
        sa.Column("related_document_ids", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("insight_metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "insight_type IN ('completeness','financial','anomaly','risk','cross_document','trend')",
            name="ck_insights_type",
        ),
        sa.CheckConstraint(
            "severity IN ('low','medium','high','critical')",
            name="ck_insights_severity",
        ),
    )
    op.create_index("ix_insights_document_id", "insights", ["document_id"])
    op.create_index("ix_insights_type", "insights", ["insight_type"])
    op.create_index("ix_insights_severity", "insights", ["severity"])


def downgrade() -> None:
    op.drop_index("ix_insights_severity", table_name="insights")
    op.drop_index("ix_insights_type", table_name="insights")
    op.drop_index("ix_insights_document_id", table_name="insights")
    op.drop_table("insights")