"""Enterprise metadata baseline."""
from alembic import op
import sqlalchemy as sa

revision = "0001_enterprise_meta"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("arka_schema_meta", sa.Column("key", sa.String(100), primary_key=True), sa.Column("value", sa.Text(), nullable=False))

def downgrade() -> None:
    op.drop_table("arka_schema_meta")
