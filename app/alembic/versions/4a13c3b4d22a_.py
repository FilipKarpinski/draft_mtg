"""empty message

Revision ID: 4a13c3b4d22a
Revises: 88cba00d81d5
Create Date: 2025-04-10 15:39:51.253743

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a13c3b4d22a'
down_revision: Union[str, None] = '88cba00d81d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
