"""create doctor validations and reports"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260722_0006"
down_revision = "20260722_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    validation_status = postgresql.ENUM(
        "VALIDATED", "REJECTED", name="validation_status"
    )
    report_status = postgresql.ENUM(
        "READY_FOR_EXPORT",
        "LLM_DRAFT_REVIEW_REQUIRED",
        name="report_status",
    )
    validation_status.create(op.get_bind(), checkfirst=True)
    report_status.create(op.get_bind(), checkfirst=True)
    validation_column = postgresql.ENUM(
        "VALIDATED", "REJECTED", name="validation_status", create_type=False
    )
    report_column = postgresql.ENUM(
        "READY_FOR_EXPORT",
        "LLM_DRAFT_REVIEW_REQUIRED",
        name="report_status",
        create_type=False,
    )
    result_column = postgresql.ENUM(
        "COMPLETED",
        "MODEL_NOT_AVAILABLE",
        "FAILED",
        name="model_result_status",
        create_type=False,
    )
    op.create_table(
        "doctor_validations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("doctor_id", sa.Uuid(), nullable=False),
        sa.Column("validation_status", validation_column, nullable=False),
        sa.Column("comment", sa.String(length=2000), nullable=True),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["doctor_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_doctor_validations_analysis_id"),
        "doctor_validations",
        ["analysis_id"],
        unique=True,
    )
    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("deterministic_report_uri", sa.String(length=1000), nullable=False),
        sa.Column("deterministic_sha256", sa.String(length=64), nullable=False),
        sa.Column("llm_status", result_column, nullable=False),
        sa.Column("llm_enriched_report_uri", sa.String(length=1000), nullable=True),
        sa.Column("status", report_column, nullable=False),
        sa.Column("generated_by", sa.Uuid(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("llm_approved_by", sa.Uuid(), nullable=True),
        sa.Column("llm_approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["generated_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["llm_approved_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reports_analysis_id"), "reports", ["analysis_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_reports_analysis_id"), table_name="reports")
    op.drop_table("reports")
    op.drop_index(
        op.f("ix_doctor_validations_analysis_id"), table_name="doctor_validations"
    )
    op.drop_table("doctor_validations")
    postgresql.ENUM(name="report_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="validation_status").drop(op.get_bind(), checkfirst=True)
