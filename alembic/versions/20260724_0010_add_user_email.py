"""add email authentication to users"""

from alembic import op
import sqlalchemy as sa

revision = "20260724_0010"
down_revision = "20260724_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email", sa.String(254), nullable=True))
    op.execute(
        "UPDATE users SET email = CASE "
        "WHEN username LIKE '%@%' THEN lower(username) "
        "ELSE lower(username) || '@neuroflow.local' END"
    )
    op.alter_column("users", "email", nullable=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_column("users", "email")
