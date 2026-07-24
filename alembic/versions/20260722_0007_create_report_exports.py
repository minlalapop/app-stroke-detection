"""create report exports"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260722_0007"
down_revision = "20260722_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    export_format = postgresql.ENUM("pdf", "docx", "xlsx", name="export_format")
    export_source = postgresql.ENUM(
        "DETERMINISTIC",
        "DETERMINISTIC_WITH_APPROVED_LLM",
        name="export_source",
    )
    export_format.create(op.get_bind(), checkfirst=True)
    export_source.create(op.get_bind(), checkfirst=True)
    format_column = postgresql.ENUM(
        "pdf", "docx", "xlsx", name="export_format", create_type=False
    )
    source_column = postgresql.ENUM(
        "DETERMINISTIC",
        "DETERMINISTIC_WITH_APPROVED_LLM",
        name="export_source",
        create_type=False,
    )
    op.create_table(
        "report_exports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("report_id", sa.Uuid(), nullable=False),
        sa.Column("format", format_column, nullable=False),
        sa.Column("source", source_column, nullable=False),
        sa.Column("file_uri", sa.String(length=1000), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("generated_by", sa.Uuid(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["generated_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_report_exports_report_id"), "report_exports", ["report_id"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_report_exports_report_id"), table_name="report_exports")
    op.drop_table("report_exports")
    postgresql.ENUM(name="export_source").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="export_format").drop(op.get_bind(), checkfirst=True)
