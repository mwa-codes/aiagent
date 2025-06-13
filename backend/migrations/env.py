from app.models import Base
import sys
import os
from alembic import context
from sqlalchemy import pool, create_engine
from sqlalchemy import engine_from_config
from logging.config import fileConfig

# Add the backend directory to Python path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

# Now import after setting up the path

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
sys.path.append(os.path.join(os.path.dirname(__file__), '../app'))
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Use DATABASE_URL_SYNC environment variable if available (for Docker)
    database_url = os.getenv('DATABASE_URL_SYNC')

    print(f"DEBUG: DATABASE_URL_SYNC = {database_url}")

    if database_url:
        # Use environment variable for Docker container
        print(f"DEBUG: Using environment database URL: {database_url}")
        connectable = create_engine(database_url, poolclass=pool.NullPool)
    else:
        # Use alembic.ini configuration for local development
        print("DEBUG: Using alembic.ini configuration")
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
