"""
Create account tables.

Revision ID: 47d36160f6e
Revises:
Create Date: 2015-10-28 09:10:51.118193
"""

from alembic import op
import sqlalchemy as sa


revision = '47d36160f6e'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'account',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('display_name', sa.String, nullable=False),
        sa.Column('password_hashed', sa.String, nullable=False),
        sa.Column('creation_date', sa.DateTime, nullable=False),
    )

    op.create_table(
        'account_reset_password',
        sa.Column('account_id', sa.Integer, sa.ForeignKey('account.id'),
                  primary_key=True, nullable=False),
        sa.Column('key', sa.String),
        sa.Column('key_expiration_date', sa.DateTime),
        sa.Column('last_email_date', sa.DateTime),
    )

    op.create_table(
        'account_email_address',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('account_id', sa.Integer, sa.ForeignKey('account.id'),
                  nullable=False),
        sa.Column('email_address', sa.String, unique=True,
                  nullable=False),
        sa.Column('verified', sa.Boolean, nullable=False),
        sa.Column('verification_key', sa.String, nullable=False),
        sa.Column('last_verification_email_date', sa.DateTime),
    )

    op.create_table(
        'account_primary_email_address',
        sa.Column('account_id', sa.Integer, sa.ForeignKey('account.id'),
                  primary_key=True, nullable=False),
        sa.Column('email_address_id', sa.Integer,
                  sa.ForeignKey('account_email_address.id'), nullable=False),
    )


def downgrade():
    op.drop_table('account_primary_email_address')
    op.drop_table('account_email_address')
    op.drop_table('account_reset_password')
    op.drop_table('account')
