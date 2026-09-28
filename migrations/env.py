"""Alembic environment placeholder for future SQLAlchemy migration adoption."""
from alembic import context

def run_migrations_online():
    # The current application uses SQLite's internal migration runner.
    # Keep Alembic ready for the PostgreSQL migration without changing runtime behavior.
    context.get_context().opts.get("dialect_name")

if context.is_offline_mode():
    pass
else:
    run_migrations_online()
