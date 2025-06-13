"""Add plan limit columns

Revision ID: add_plan_limits
Revises: f337765b5444
Create Date: 2025-06-13 15:16:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_plan_limits'
down_revision: Union[str, None] = 'f337765b5444'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add plan limit columns to plans table."""
    # Add new columns with default values
    op.add_column('plans', sa.Column('max_uploads_per_month',
                  sa.Integer(), nullable=False, server_default='50'))
    op.add_column('plans', sa.Column('max_summaries_per_month',
                  sa.Integer(), nullable=False, server_default='20'))
    op.add_column('plans', sa.Column('max_file_size_mb',
                  sa.Integer(), nullable=False, server_default='10'))


def downgrade() -> None:
    """Remove plan limit columns from plans table."""
    op.drop_column('plans', 'max_file_size_mb')
    op.drop_column('plans', 'max_summaries_per_month')
    op.drop_column('plans', 'max_uploads_per_month')
