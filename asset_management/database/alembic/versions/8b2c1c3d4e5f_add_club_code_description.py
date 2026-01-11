"""add club code and description

Revision ID: 8b2c1c3d4e5f
Revises: 47a99100431f
Create Date: 2026-01-09 12:00:00.000000

"""
from typing import Sequence, Union
import secrets
import string

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8b2c1c3d4e5f"
down_revision: Union[str, Sequence[str], None] = "47a99100431f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_CODE_ALPHABET = string.ascii_uppercase + string.digits
_CODE_LENGTH = 6


def _generate_code() -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LENGTH))


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("club", sa.Column("description", sa.String(length=255), nullable=True))
    op.add_column("club", sa.Column("club_code", sa.String(length=50), nullable=True))

    connection = op.get_bind()
    existing_codes = set()

    rows = connection.execute(sa.text("SELECT id FROM club")).fetchall()
    for (club_id,) in rows:
        code = _generate_code()
        while code in existing_codes:
            code = _generate_code()
        existing_codes.add(code)
        connection.execute(
            sa.text("UPDATE club SET club_code = :code WHERE id = :club_id"),
            {"code": code, "club_id": club_id},
        )

    op.alter_column("club", "club_code", nullable=False)
    op.create_unique_constraint("uq_club_club_code", "club", ["club_code"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_club_club_code", "club", type_="unique")
    op.drop_column("club", "club_code")
    op.drop_column("club", "description")
