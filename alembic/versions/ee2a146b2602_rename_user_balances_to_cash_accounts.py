"""rename user_balances to cash_accounts, add unique user_id and check constraints

Revision ID: ee2a146b2602
Revises: 0e2ec47780fd
Create Date: 2026-07-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "ee2a146b2602"
down_revision: Union[str, Sequence[str], None] = "0e2ec47780fd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("user_balances", "cash_accounts")
    op.drop_index("ix_user_balances_user_id", table_name="cash_accounts")
    op.create_index(
        op.f("ix_cash_accounts_user_id"), "cash_accounts", ["user_id"], unique=True
    )
    op.create_check_constraint(
        "ck_cash_balance_nonneg", "cash_accounts", "cash_balance >= 0"
    )
    op.create_check_constraint(
        "ck_locked_cash_nonneg", "cash_accounts", "locked_cash >= 0"
    )
    op.create_check_constraint(
        "ck_cash_covers_locked", "cash_accounts", "cash_balance >= locked_cash"
    )


def downgrade() -> None:
    op.drop_constraint("ck_cash_covers_locked", "cash_accounts", type_="check")
    op.drop_constraint("ck_locked_cash_nonneg", "cash_accounts", type_="check")
    op.drop_constraint("ck_cash_balance_nonneg", "cash_accounts", type_="check")
    op.drop_index(op.f("ix_cash_accounts_user_id"), table_name="cash_accounts")
    op.create_index(
        "ix_user_balances_user_id", "cash_accounts", ["user_id"], unique=False
    )
    op.rename_table("cash_accounts", "user_balances")
