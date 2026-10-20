"""Isolate private economy records and register account access requests.

Revision ID: 0012
Revises: 0011
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PRIVATE_TABLES = (
    "sale_listings",
    "sale_capture_batches",
    "sale_capture_files",
    "sale_capture_listing_actions",
)


def upgrade() -> None:
    for table in PRIVATE_TABLES:
        op.add_column(
            table, sa.Column("owner_id", sa.String(40), nullable=False, server_default="owner")
        )
        op.create_index(f"ix_{table}_owner_id", table, ["owner_id"])
    op.add_column(
        "price_observations",
        sa.Column("contributor_id", sa.String(40), nullable=False, server_default="owner"),
    )
    op.create_table(
        "user_accounts",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("google_subject", sa.String(255), unique=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.Column("notification_attempted_at", sa.DateTime(timezone=True)),
        sa.Column("notification_sent_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("status IN ('pending', 'approved', 'denied')", name="ck_account_status"),
    )


def downgrade() -> None:
    op.drop_table("user_accounts")
    op.drop_column("price_observations", "contributor_id")
    for table in reversed(PRIVATE_TABLES):
        op.drop_index(f"ix_{table}_owner_id", table_name=table)
        op.drop_column(table, "owner_id")
