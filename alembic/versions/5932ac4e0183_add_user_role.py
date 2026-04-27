"""add user role

Revision ID: 5932ac4e0183
Revises: 1a0aff8f9953
Create Date: 2026-04-25

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "5932ac4e0183"
down_revision: Union[str, Sequence[str], None] = "1a0aff8f9953"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE user_role_enum AS ENUM ('user', 'admin')")
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.Enum("user", "admin", name="user_role_enum"),
            nullable=False,
            server_default="user",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "role")
    op.execute("DROP TYPE user_role_enum")
