"""user mfa and email verification

Revision ID: 9c6b1f3a7d21
Revises: 27ca9594dbaa
Create Date: 2026-07-20 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c6b1f3a7d21'
down_revision: Union[str, None] = '27ca9594dbaa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('email_verification_token', sa.String(length=64), nullable=True))
    op.add_column('users', sa.Column('email_verification_token_expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('totp_secret', sa.String(length=64), nullable=True))
    op.add_column(
        'users',
        sa.Column('totp_enabled', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column('users', 'totp_enabled', server_default=None)
    op.create_unique_constraint('uq_users_email_verification_token', 'users', ['email_verification_token'])


def downgrade() -> None:
    op.drop_constraint('uq_users_email_verification_token', 'users', type_='unique')
    op.drop_column('users', 'totp_enabled')
    op.drop_column('users', 'totp_secret')
    op.drop_column('users', 'email_verification_token_expires_at')
    op.drop_column('users', 'email_verification_token')
    op.drop_column('users', 'email_verified_at')
