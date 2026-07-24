"""create analyses and model result tables"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260722_0005"
down_revision = "20260722_0004"
branch_labels = None
depends_on = None

ANALYSIS_STATUSES = (
    "CREATED",
    "WAITING_FOR_INPUT",
    "READY",
    "PROCESSING",
    "COMPLETED",
    "PARTIAL_COMPLETED",
    "MODEL_NOT_AVAILABLE",
    "FAILED",
    "VALIDATED_BY_DOCTOR",
    "REPORT_GENERATED",
)
RESULT_STATUSES = ("COMPLETED", "MODEL_NOT_AVAILABLE", "FAILED")


def upgrade() -> None:
    analysis_status = postgresql.ENUM(*ANALYSIS_STATUSES, name="analysis_status")
    result_status = postgresql.ENUM(*RESULT_STATUSES, name="model_result_status")
    analysis_status.create(op.get_bind(), checkfirst=True)
    result_status.create(op.get_bind(), checkfirst=True)
    analysis_column = postgresql.ENUM(
        *ANALYSIS_STATUSES, name="analysis_status", create_type=False
    )
    result_column = postgresql.ENUM(
        *RESULT_STATUSES, name="model_result_status", create_type=False
    )
    op.create_table(
        "analyses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("clinical_data_id", sa.Uuid(), nullable=True),
        sa.Column("imaging_study_id", sa.Uuid(), nullable=True),
        sa.Column("status", analysis_column, nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinical_data_id"], ["clinical_data.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["imaging_study_id"], ["imaging_studies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analyses_patient_id"), "analyses", ["patient_id"])
    op.create_table(
        "tabular_predictions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("status", result_column, nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("risk_label", sa.String(length=100), nullable=True),
        sa.Column("model_version", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_tabular_predictions_analysis_id"),
        "tabular_predictions",
        ["analysis_id"],
        unique=True,
    )
    op.create_table(
        "image_segmentation_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("status", result_column, nullable=False),
        sa.Column("lesion_detected", sa.Boolean(), nullable=True),
        sa.Column("lesion_volume_ml", sa.Float(), nullable=True),
        sa.Column("mask_uri", sa.String(length=1000), nullable=True),
        sa.Column("preview_uri", sa.String(length=1000), nullable=True),
        sa.Column("model_version", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_image_segmentation_results_analysis_id"),
        "image_segmentation_results",
        ["analysis_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_image_segmentation_results_analysis_id"),
        table_name="image_segmentation_results",
    )
    op.drop_table("image_segmentation_results")
    op.drop_index(
        op.f("ix_tabular_predictions_analysis_id"), table_name="tabular_predictions"
    )
    op.drop_table("tabular_predictions")
    op.drop_index(op.f("ix_analyses_patient_id"), table_name="analyses")
    op.drop_table("analyses")
    postgresql.ENUM(name="model_result_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="analysis_status").drop(op.get_bind(), checkfirst=True)
