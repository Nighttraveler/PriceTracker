"""add_descatalogado_to_variantes

Revision ID: 9b508d6e1ac1
Revises: 
Create Date: 2026-06-04 22:05:34.133735

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b508d6e1ac1'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "variantes",
        sa.Column("descatalogado", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("variantes", "descatalogado")
