"""add failure fields to runs

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-02-14 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("runs", sa.Column("failure_stage", sa.Text(), nullable=True))
    op.add_column("runs", sa.Column("failure_error", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("runs", "failure_error")
    op.drop_column("runs", "failure_stage")
