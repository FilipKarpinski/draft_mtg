"""empty message

Revision ID: 88cba00d81d5
Revises: b37c41780062
Create Date: 2025-04-10 15:23:05.168200

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '88cba00d81d5'
down_revision: Union[str, None] = 'b37c41780062'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('draft_players',
    sa.Column('draft_id', sa.Integer(), nullable=False),
    sa.Column('player_id', sa.Integer(), nullable=False),
    sa.Column('final_place', sa.Integer(), nullable=True),
    sa.Column('order', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['draft_id'], ['drafts.id'], ),
    sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
    sa.PrimaryKeyConstraint('draft_id', 'player_id')
    )
    op.drop_index('ix_drafts_draft_date', table_name='drafts')
    op.drop_column('drafts', 'draft_date')
    op.add_column('matches', sa.Column('round', sa.Integer(), nullable=False))
    op.add_column('matches', sa.Column('score', sa.String(), nullable=False))
    op.drop_column('matches', 'score_1')
    op.drop_column('matches', 'score_2')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('matches', sa.Column('score_2', sa.INTEGER(), autoincrement=False, nullable=False))
    op.add_column('matches', sa.Column('score_1', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_column('matches', 'score')
    op.drop_column('matches', 'round')
    op.add_column('drafts', sa.Column('draft_date', postgresql.TIMESTAMP(), autoincrement=False, nullable=False))
    op.create_index('ix_drafts_draft_date', 'drafts', ['draft_date'], unique=False)
    op.drop_table('draft_players')
    # ### end Alembic commands ###
