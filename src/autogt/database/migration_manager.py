"""Database migration manager using Alembic."""

import os
import sys
from pathlib import Path
from typing import Optional

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError

from ..lib.config import get_database_config
from ..lib.exceptions import DatabaseError
from ..models import Base
import logging

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations using Alembic."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize migration manager.
        
        Args:
            config_path: Optional path to alembic.ini config file
        """
        self.config_path = config_path or self._get_default_config_path()
        self.db_config = get_database_config()
        
    def _get_default_config_path(self) -> str:
        """Get default path to alembic.ini file."""
        # Look for alembic.ini in project root
        project_root = Path(__file__).parent.parent.parent.parent
        alembic_ini = project_root / "alembic.ini"
        
        if not alembic_ini.exists():
            # Create default alembic.ini if it doesn't exist
            self._create_alembic_ini(alembic_ini)
            
        return str(alembic_ini)
    
    def _create_alembic_ini(self, path: Path) -> None:
        """Create default alembic.ini configuration."""
        alembic_ini_content = """# A generic, single database configuration.

[alembic]
# path to migration scripts
script_location = database/migrations

# template used to generate migration file names; The default value is %%(rev)s_%%(slug)s
# Uncomment the line below if you want the files to be prepended with date and time
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s

# sys.path path, will be prepended to sys.path if present.
# defaults to the current working directory.
prepend_sys_path = .

# timezone to use when rendering the date within the migration file
# as well as the filename.
# If specified, requires the python>=3.9 or backports.zoneinfo library to be added to the 
# requirements.txt file, or if python<3.9, the backports.zoneinfo library is required
# timezone =

# max length of characters to apply to the
# "slug" field
# truncate_slug_length = 40

# set to 'true' to run the environment during
# the 'revision' command, regardless of autogenerate
# revision_environment = false

# set to 'true' to allow .pyc and .pyo files without
# a source .py file to be detected as revisions in the
# versions/ directory
# sourceless = false

# version number format for new migration files
# If this is set to 'uuid', Alembic will generate a UUID for each revision
# instead of using integers. This is useful if multiple developers
# are working on different branches and need to avoid conflicts in
# revision numbers.
# version_num_format = uuid

# version location specification; This defaults
# to database/migrations/versions.  When using multiple version
# directories, initial revisions must be specified with --version-path.
# The path separator used here should be the separator specified by "version_path_separator" below.
# version_locations = %(here)s/bar:%(here)s/bat:database/migrations/versions

# version path separator; As mentioned above, this is the character used to split
# version_locations. The default within new alembic.ini files is "os", which uses os.pathsep.
# If this key is omitted entirely, it falls back to the legacy behavior of splitting on spaces and/or commas.
# Valid values for version_path_separator are:
#
# version_path_separator = :
# version_path_separator = ;
# version_path_separator = space
version_path_separator = os

# set to 'true' to search source files recursively
# in each "version_locations" directory
# recursive_version_locations = false

# the output encoding used when revision files
# are written from script.py.mako
# output_encoding = utf-8

sqlalchemy.url = driver://user:pass@localhost/dbname


[post_write_hooks]
# post_write_hooks defines scripts or Python functions that are run
# on newly generated revision scripts.  See the documentation for further
# detail and examples

# format using "black" - use the console_scripts runner, against the "black" entrypoint
# hooks = black
# black.type = console_scripts
# black.entrypoint = black
# black.options = -l 79 REVISION_SCRIPT_FILENAME

# lint with attempts to fix using "ruff" - use the exec runner, execute a binary
# hooks = ruff
# ruff.type = exec
# ruff.executable = %(here)s/.venv/bin/ruff
# ruff.options = --fix REVISION_SCRIPT_FILENAME

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""
        
        logger.info(f"Creating alembic.ini at {path}")
        path.write_text(alembic_ini_content)
    
    def init(self) -> None:
        """Initialize Alembic migration environment."""
        try:
            # Create migrations directory if it doesn't exist
            migrations_dir = Path("database/migrations")
            migrations_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize alembic if env.py doesn't exist
            env_py = migrations_dir / "env.py"
            if not env_py.exists():
                logger.info("Initializing Alembic migration environment")
                alembic_cfg = Config(self.config_path)
                command.init(alembic_cfg, str(migrations_dir))
                
                # Update env.py to use our models
                self._update_env_py(env_py)
            
            # Create initial migration if no migrations exist
            versions_dir = migrations_dir / "versions"
            if not versions_dir.exists() or not list(versions_dir.glob("*.py")):
                logger.info("Creating initial migration")
                self.create_migration("initial_schema")
                
            logger.info("Database migration environment initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize migrations: {e}")
            raise DatabaseError(f"Migration initialization failed: {e}")
    
    def _update_env_py(self, env_py_path: Path) -> None:
        """Update env.py to use our models and configuration."""
        env_py_content = '''"""Alembic environment configuration."""

import logging
from logging.config import fileConfig
from pathlib import Path
import sys

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.autogt.models import Base
from src.autogt.lib.config import get_database_config

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


def get_url():
    """Get database URL from config."""
    db_config = get_database_config()
    return db_config.get_url()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
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
    # Override the sqlalchemy.url in the alembic config
    config.set_main_option("sqlalchemy.url", get_url())
    
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
'''
        
        logger.info(f"Updating env.py at {env_py_path}")
        env_py_path.write_text(env_py_content)
    
    def create_migration(self, message: str) -> str:
        """Create a new migration.
        
        Args:
            message: Description of the migration
            
        Returns:
            The revision ID of the created migration
        """
        try:
            alembic_cfg = Config(self.config_path)
            alembic_cfg.set_main_option("sqlalchemy.url", self.db_config.get_url())
            
            # Create migration
            revision = command.revision(
                alembic_cfg,
                message=message,
                autogenerate=True
            )
            
            logger.info(f"Created migration: {message}")
            return revision.revision if revision else ""
            
        except Exception as e:
            logger.error(f"Failed to create migration: {e}")
            raise DatabaseError(f"Migration creation failed: {e}")
    
    def upgrade(self, revision: str = "head") -> None:
        """Upgrade database to specified revision.
        
        Args:
            revision: Target revision (default: "head")
        """
        try:
            alembic_cfg = Config(self.config_path)
            alembic_cfg.set_main_option("sqlalchemy.url", self.db_config.get_url())
            
            command.upgrade(alembic_cfg, revision)
            logger.info(f"Database upgraded to revision: {revision}")
            
        except Exception as e:
            logger.error(f"Failed to upgrade database: {e}")
            raise DatabaseError(f"Database upgrade failed: {e}")
    
    def downgrade(self, revision: str) -> None:
        """Downgrade database to specified revision.
        
        Args:
            revision: Target revision
        """
        try:
            alembic_cfg = Config(self.config_path)
            alembic_cfg.set_main_option("sqlalchemy.url", self.db_config.get_url())
            
            command.downgrade(alembic_cfg, revision)
            logger.info(f"Database downgraded to revision: {revision}")
            
        except Exception as e:
            logger.error(f"Failed to downgrade database: {e}")
            raise DatabaseError(f"Database downgrade failed: {e}")
    
    def current_revision(self) -> Optional[str]:
        """Get current database revision.
        
        Returns:
            Current revision ID or None if no migrations applied
        """
        try:
            engine = create_engine(self.db_config.get_url())
            
            # Check if alembic_version table exists
            inspector = inspect(engine)
            if "alembic_version" not in inspector.get_table_names():
                return None
            
            with engine.connect() as conn:
                result = conn.execute("SELECT version_num FROM alembic_version")
                row = result.fetchone()
                return row[0] if row else None
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to get current revision: {e}")
            return None
    
    def create_all_tables(self) -> None:
        """Create all tables using SQLAlchemy metadata (without migrations)."""
        try:
            engine = create_engine(self.db_config.get_url())
            Base.metadata.create_all(engine)
            logger.info("All tables created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise DatabaseError(f"Table creation failed: {e}")


def main():
    """CLI entry point for migration manager."""
    if len(sys.argv) < 2:
        print("Usage: python -m src.autogt.database.migration_manager <command>")
        print("Commands: init, create <message>, upgrade [revision], downgrade <revision>, current")
        sys.exit(1)
    
    manager = MigrationManager()
    command = sys.argv[1]
    
    try:
        if command == "init":
            manager.init()
        elif command == "create" and len(sys.argv) > 2:
            message = " ".join(sys.argv[2:])
            revision = manager.create_migration(message)
            print(f"Created migration: {revision}")
        elif command == "upgrade":
            revision = sys.argv[2] if len(sys.argv) > 2 else "head"
            manager.upgrade(revision)
        elif command == "downgrade" and len(sys.argv) > 2:
            manager.downgrade(sys.argv[2])
        elif command == "current":
            revision = manager.current_revision()
            print(f"Current revision: {revision}")
        elif command == "create-tables":
            manager.create_all_tables()
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()