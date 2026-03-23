import os
import sys
from logging.config import fileConfig


from alembic import context
from sqlalchemy import engine_from_config, pool


sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings
from app.core.database import Base
from app.models import Base


ALEMBIC_CONFIG = context.config

if ALEMBIC_CONFIG.config_file_name is not None:
    fileConfig(ALEMBIC_CONFIG.config_file_name)

TARGET_METADATA = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""
    
    context.configure(
        url=settings.get_database_url(),
        target_metadata=TARGET_METADATA,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode."""
    
    configuration = ALEMBIC_CONFIG.get_section(ALEMBIC_CONFIG.config_ini_section, {})
    
    configuration["sqlalchemy.url"] = settings.get_database_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=TARGET_METADATA,
            render_as_batch=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()