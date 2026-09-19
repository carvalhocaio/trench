"""limit weeks to the regular season

Revision ID: 46fbcd2840f7
Revises: d3d13568c0f2
Create Date: 2026-09-19 13:21:23.258715

"""

from collections.abc import Sequence

from alembic import op

revision: str = "46fbcd2840f7"
down_revision: str | Sequence[str] | None = "d3d13568c0f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CONSTRAINT = op.f("ck_games_week_range")


def upgrade() -> None:
    op.drop_constraint(CONSTRAINT, "games", type_="check")
    op.create_check_constraint(CONSTRAINT, "games", "week BETWEEN 1 AND 18")


def downgrade() -> None:
    op.drop_constraint(CONSTRAINT, "games", type_="check")
    op.create_check_constraint(CONSTRAINT, "games", "week BETWEEN 1 AND 22")
