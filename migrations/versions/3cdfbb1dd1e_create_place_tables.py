"""
Create place tables

Revision ID: 3cdfbb1dd1e
Revises: 47d36160f6e
Create Date: 2015-10-28 09:16:10.822474
"""

from alembic import op
import sqlalchemy as sa


revision = '3cdfbb1dd1e'
down_revision = '47d36160f6e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'author',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('account_id', sa.Integer, nullable=True),
        sa.Column('ip_address', sa.String, nullable=False),
    )

    op.create_table(
        'approval',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('account_id', sa.Integer, sa.ForeignKey('account.id'),
                  nullable=True),
        sa.Column('date', sa.DateTime, nullable=True),
    )

    op.create_table(
        'place',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('slug', sa.String, unique=True, nullable=False),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('description', sa.String, nullable=False),
        sa.Column('location', sa.String, nullable=False),
        sa.Column('author_id', sa.Integer, sa.ForeignKey('author.id'),
                  nullable=False),
        sa.Column('approval_id', sa.Integer, sa.ForeignKey('approval.id'),
                  nullable=True),
    )

    op.create_table(
        'place_scale',
        sa.Column('place_id', sa.Integer, sa.ForeignKey('place.id'),
                  primary_key=True, nullable=False),
        sa.Column('text_0', sa.String, nullable=False),
        sa.Column('text_1', sa.String, nullable=False),
        sa.Column('text_2', sa.String, nullable=False),
        sa.Column('text_3', sa.String, nullable=False),
        sa.Column('text_4', sa.String, nullable=False),
        sa.Column('text_5', sa.String, nullable=False),
        sa.Column('text_6', sa.String, nullable=False),
        sa.Column('text_7', sa.String, nullable=False),
        sa.Column('text_8', sa.String, nullable=False),
        sa.Column('text_9', sa.String, nullable=False),
        sa.Column('text_10', sa.String, nullable=False),
    )

    op.create_table(
        'place_change',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('place_id', sa.Integer, sa.ForeignKey('place.id'),
                  nullable=False),
        sa.Column('author_id', sa.Integer, sa.ForeignKey('author.id'),
                  nullable=False),
        sa.Column('date', sa.DateTime, nullable=False),
        sa.Column('column', sa.String, nullable=False),
        sa.Column('old_value', sa.String, nullable=False),
        sa.Column('new_value', sa.String, nullable=False),
        sa.Column('approval_id', sa.Integer, sa.ForeignKey('approval.id'),
                  nullable=True),
    )

    op.create_table(
        'place_update',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('place_id', sa.Integer, sa.ForeignKey('place.id'),
                  nullable=False),
        sa.Column('author_id', sa.Integer, sa.ForeignKey('author.id'),
                  nullable=False),
        sa.Column('date', sa.DateTime, nullable=False),
        sa.Column('busyness', sa.Integer, nullable=False),
        sa.Column('approval_id', sa.Integer, sa.ForeignKey('approval.id'),
                  nullable=True),
    )


def downgrade():
    op.drop_table('place_update')
    op.drop_table('place_change')
    op.drop_table('place_scale')
    op.drop_table('place')
    op.drop_table('approval')
    op.drop_table('author')
