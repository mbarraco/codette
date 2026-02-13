"""add title, test_cases, and deleted_at to problems

Revision ID: a1b2c3d4e5f6
Revises: 51ddc4342314
Create Date: 2026-02-13 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "51ddc4342314"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("problems", sa.Column("title", sa.String(255), nullable=False, server_default="Untitled"))
    op.add_column("problems", sa.Column("test_cases", sa.JSON(), nullable=True))
    op.add_column("problems", sa.Column("deleted_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("problems", "deleted_at")
    op.drop_column("problems", "test_cases")
    op.drop_column("problems", "title")
