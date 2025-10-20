"""initial migration

Revision ID: 7ec51324d761
Revises: 
Create Date: 2025-08-20 08:49:05.749874

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = '7ec51324d761'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('game',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=True),
    sa.Column('platform', sa.Integer(), nullable=True),
    sa.Column('genre', sa.Integer(), nullable=True),
    sa.Column('publisher', sa.Integer(), nullable=True),
    sa.Column('size', sa.Integer(), nullable=True),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_game_description'), 'game', ['description'], unique=False)
    op.create_index(op.f('ix_game_genre'), 'game', ['genre'], unique=False)
    op.create_index(op.f('ix_game_name'), 'game', ['name'], unique=False)
    op.create_index(op.f('ix_game_platform'), 'game', ['platform'], unique=False)
    op.create_index(op.f('ix_game_publisher'), 'game', ['publisher'], unique=False)
    op.create_index(op.f('ix_game_size'), 'game', ['size'], unique=False)
    op.create_index(op.f('ix_game_year'), 'game', ['year'], unique=False)
    op.create_table('genre',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_genre_name'), 'genre', ['name'], unique=False)
    op.create_table('manual',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('game_id', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_manual_game_id'), 'manual', ['game_id'], unique=False)
    op.create_table('platform',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('processor', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_platform_name'), 'platform', ['name'], unique=False)
    op.create_index(op.f('ix_platform_processor'), 'platform', ['processor'], unique=False)
    op.create_table('publisher',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_publisher_name'), 'publisher', ['name'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_publisher_name'), table_name='publisher')
    op.drop_table('publisher')
    op.drop_index(op.f('ix_platform_processor'), table_name='platform')
    op.drop_index(op.f('ix_platform_name'), table_name='platform')
    op.drop_table('platform')
    op.drop_index(op.f('ix_manual_game_id'), table_name='manual')
    op.drop_table('manual')
    op.drop_index(op.f('ix_genre_name'), table_name='genre')
    op.drop_table('genre')
    op.drop_index(op.f('ix_game_year'), table_name='game')
    op.drop_index(op.f('ix_game_size'), table_name='game')
    op.drop_index(op.f('ix_game_publisher'), table_name='game')
    op.drop_index(op.f('ix_game_platform'), table_name='game')
    op.drop_index(op.f('ix_game_name'), table_name='game')
    op.drop_index(op.f('ix_game_genre'), table_name='game')
    op.drop_index(op.f('ix_game_description'), table_name='game')
    op.drop_table('game')
