"""insert_test_data

Revision ID: 0550b2db0759
Revises: 7ec51324d761
Create Date: 2025-08-20 10:30:25.471740

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, Integer


# revision identifiers, used by Alembic.
revision: str = '0550b2db0759'
down_revision: Union[str, Sequence[str], None] = '7ec51324d761'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Insert test data into tables."""
    # Define table structures for data insertion
    platform_table = table('platform',
        column('id', Integer),
        column('name', String),
        column('processor', String)
    )
    
    genre_table = table('genre',
        column('id', Integer),
        column('name', String)
    )
    
    publisher_table = table('publisher',
        column('id', Integer),
        column('name', String)
    )
    
    game_table = table('game',
        column('id', Integer),
        column('name', String),
        column('year', Integer),
        column('platform', Integer),
        column('genre', Integer),
        column('publisher', Integer),
        column('size', Integer),
        column('description', String)
    )
    
    manual_table = table('manual',
        column('id', Integer),
        column('game_id', Integer)
    )
    
    # Insert test data for platforms
    op.bulk_insert(platform_table,
        [
            {'id': 1, 'name': 'Nintendo Entertainment System', 'processor': 'Ricoh 2A03'},
            {'id': 2, 'name': 'Super Nintendo', 'processor': 'Ricoh 5A22'},
            {'id': 3, 'name': 'PlayStation', 'processor': 'MIPS R3000A'},
            {'id': 4, 'name': 'PC', 'processor': 'Various'}
        ]
    )
    
    # Insert test data for genres
    op.bulk_insert(genre_table,
        [
            {'id': 1, 'name': 'Action'},
            {'id': 2, 'name': 'Adventure'},
            {'id': 3, 'name': 'Role-Playing'},
            {'id': 4, 'name': 'Strategy'},
            {'id': 5, 'name': 'Simulation'}
        ]
    )
    
    # Insert test data for publishers
    op.bulk_insert(publisher_table,
        [
            {'id': 1, 'name': 'Nintendo'},
            {'id': 2, 'name': 'Square Enix'},
            {'id': 3, 'name': 'Electronic Arts'},
            {'id': 4, 'name': 'Blizzard Entertainment'}
        ]
    )
    
    # Insert test data for games
    op.bulk_insert(game_table,
        [
            {
                'id': 1, 
                'name': 'Super Mario Bros.', 
                'year': 1985, 
                'platform': 1, 
                'genre': 1, 
                'publisher': 1, 
                'size': 40, 
                'description': 'Classic platformer game featuring Mario and Luigi'
            },
            {
                'id': 2, 
                'name': 'Final Fantasy VI', 
                'year': 1994, 
                'platform': 2, 
                'genre': 3, 
                'publisher': 2, 
                'size': 24, 
                'description': 'RPG set in a fantasy world with magic and technology'
            },
            {
                'id': 3, 
                'name': 'StarCraft', 
                'year': 1998, 
                'platform': 4, 
                'genre': 4, 
                'publisher': 4, 
                'size': 1200, 
                'description': 'Real-time strategy game set in a sci-fi universe'
            }
        ]
    )
    
    # Insert test data for manuals
    op.bulk_insert(manual_table,
        [
            {'id': 1, 'game_id': 1},
            {'id': 2, 'game_id': 2},
            {'id': 3, 'game_id': 3}
        ]
    )


def downgrade() -> None:
    """Remove test data from tables."""
    # Delete all test data in reverse order of dependencies
    op.execute("DELETE FROM manual")
    op.execute("DELETE FROM game")
    op.execute("DELETE FROM publisher")
    op.execute("DELETE FROM genre")
    op.execute("DELETE FROM platform")
