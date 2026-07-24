"""create imaging studies table"""

from alembic import op
import sqlalchemy as sa

revision = "20260722_0004"
down_revision = "20260722_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    study_status = sa.Enum("uploaded", name="imaging_study_status")
    op.create_table(
        "imaging_studies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("modality", sa.String(length=50), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("original_file_uri", sa.String(length=1000), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("status", study_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_imaging_studies_patient_id"),
        "imaging_studies",
        ["patient_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_imaging_studies_patient_id"), table_name="imaging_studies")
    op.drop_table("imaging_studies")
    sa.Enum("uploaded", name="imaging_study_status").drop(op.get_bind(), checkfirst=True)

