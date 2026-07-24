"""Normalize legacy patient sex values.

Revision ID: 20260724_0011
Revises: 20260724_0010
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20260724_0011"
down_revision: str | None = "20260724_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE patients
        SET sex = 'Female'
        WHERE lower(trim(sex)) IN ('f', 'female')
        """
    )
    op.execute(
        """
        UPDATE patients
        SET sex = 'Male'
        WHERE lower(trim(sex)) IN ('m', 'male')
        """
    )


def downgrade() -> None:
    # The original abbreviated value cannot be inferred after normalization.
    pass
