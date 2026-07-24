"""align clinical data with CatBoost features"""

from alembic import op
import sqlalchemy as sa

revision = "20260724_0009"
down_revision = "20260722_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "clinical_data",
        "age",
        existing_type=sa.Integer(),
        type_=sa.Float(),
        existing_nullable=True,
    )
    op.alter_column(
        "clinical_data",
        "average_glucose",
        new_column_name="avg_glucose_level",
        existing_type=sa.Float(),
        existing_nullable=True,
    )
    op.add_column("clinical_data", sa.Column("ever_married", sa.String(3), nullable=True))
    op.add_column("clinical_data", sa.Column("work_type", sa.String(20), nullable=True))
    op.add_column("clinical_data", sa.Column("residence_type", sa.String(5), nullable=True))


def downgrade() -> None:
    op.drop_column("clinical_data", "residence_type")
    op.drop_column("clinical_data", "work_type")
    op.drop_column("clinical_data", "ever_married")
    op.alter_column(
        "clinical_data",
        "avg_glucose_level",
        new_column_name="average_glucose",
        existing_type=sa.Float(),
        existing_nullable=True,
    )
    op.alter_column(
        "clinical_data",
        "age",
        existing_type=sa.Float(),
        type_=sa.Integer(),
        existing_nullable=True,
        postgresql_using="age::integer",
    )
