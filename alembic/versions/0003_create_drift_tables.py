"""create baseline_snapshots, drift_results, drift_alerts tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "baseline_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_type", sa.String(length=32), nullable=False),
        sa.Column("document_type_distribution", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("field_presence_rates", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("numeric_field_bins", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("schema_keys", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("embedding_centroid", postgresql.JSONB(), nullable=True),
        sa.Column("mean_extraction_confidence", sa.Float(), nullable=True),
        sa.Column("retrieval_hit_rate", sa.Float(), nullable=True),
        sa.Column("retrieval_mrr", sa.Float(), nullable=True),
        sa.Column("sample_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_baseline_snapshots_document_type", "baseline_snapshots", ["document_type"])
    op.create_index("ix_baseline_snapshots_active", "baseline_snapshots", ["is_active"])

    op.create_table(
        "drift_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dimension", sa.String(length=64), nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("baseline_summary", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("current_summary", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_drift_results_dimension", "drift_results", ["dimension"])
    op.create_index("ix_drift_results_severity", "drift_results", ["severity"])

    op.create_table(
        "drift_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "drift_result_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("drift_results.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("message", sa.String(length=1024), nullable=False),
        sa.Column("acknowledged", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_drift_alerts_created_at", "drift_alerts", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_drift_alerts_created_at", table_name="drift_alerts")
    op.drop_table("drift_alerts")

    op.drop_index("ix_drift_results_severity", table_name="drift_results")
    op.drop_index("ix_drift_results_dimension", table_name="drift_results")
    op.drop_table("drift_results")

    op.drop_index("ix_baseline_snapshots_active", table_name="baseline_snapshots")
    op.drop_index("ix_baseline_snapshots_document_type", table_name="baseline_snapshots")
    op.drop_table("baseline_snapshots")