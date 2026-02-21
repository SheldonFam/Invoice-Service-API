"""add invoice number sequence

Revision ID: a1b2c3d4e5f6
Revises: ebef501accd3
Create Date: 2026-02-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "ebef501accd3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the sequence for invoice ID generation.
    # Start value is set based on existing invoices so we don't collide.
    op.execute(
        """
        DO $$
        DECLARE
            max_num INTEGER;
        BEGIN
            SELECT COALESCE(
                MAX(CAST(SUBSTRING(id FROM 5) AS INTEGER)), 0
            ) INTO max_num
            FROM invoices
            WHERE id LIKE 'INV-%';

            EXECUTE format(
                'CREATE SEQUENCE invoice_number_seq START WITH %s INCREMENT BY 1 NO CYCLE',
                max_num + 1
            );
        END $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP SEQUENCE IF EXISTS invoice_number_seq")
