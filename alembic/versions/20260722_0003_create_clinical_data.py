"""create clinical data table"""

from alembic import op
import sqlalchemy as sa

revision = "20260722_0003"
down_revision = "20260722_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clinical_data",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("hypertension", sa.Boolean(), nullable=True),
        sa.Column("heart_disease", sa.Boolean(), nullable=True),
        sa.Column("average_glucose", sa.Float(), nullable=True),
        sa.Column("bmi", sa.Float(), nullable=True),
        sa.Column("smoking_status", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_clinical_data_patient_id"),
        "clinical_data",
        ["patient_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_clinical_data_patient_id"), table_name="clinical_data")
    op.drop_table("clinical_data")
