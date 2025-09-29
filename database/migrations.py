"""Database schema migrations with Alembic.

Reference: data-model.md all entity schemas and T043 task
Handles database schema creation and evolution.
"""

from alembic import command, script
from alembic.config import Config as AlembicConfig
from alembic.runtime import migration
from sqlalchemy import create_engine, pool
from pathlib import Path
import logging

from ..services import DatabaseService
from ..models import Base


logger = logging.getLogger('autogt.migrations')


class MigrationManager:
    """Manager for database schema migrations."""
    
    def __init__(self, database_url: str):
        """Initialize migration manager.
        
        Args:
            database_url: Database connection URL
        """
        self.database_url = database_url
        self.migrations_dir = Path(__file__).parent.parent.parent.parent / "database" / "migrations"
        self.alembic_cfg = self._setup_alembic_config()
    
    def _setup_alembic_config(self) -> AlembicConfig:
        """Setup Alembic configuration."""
        # Create migrations directory if it doesn't exist
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        
        # Create alembic.ini file if it doesn't exist
        alembic_ini = self.migrations_dir.parent / "alembic.ini"
        if not alembic_ini.exists():
            self._create_alembic_ini(alembic_ini)
        
        # Create Alembic configuration
        cfg = AlembicConfig(str(alembic_ini))
        cfg.set_main_option("script_location", str(self.migrations_dir))
        cfg.set_main_option("sqlalchemy.url", self.database_url)
        
        return cfg
    
    def _create_alembic_ini(self, alembic_ini_path: Path) -> None:
        """Create Alembic configuration file."""
        alembic_ini_content = f"""# A generic, single database configuration.

[alembic]
# path to migration scripts
script_location = {self.migrations_dir}

# template used to generate migration file names
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d%%(second).2d_%%(rev)s_%%(slug)s

# sys.path path, will be prepended to sys.path if present.
# defaults to the current working directory.
prepend_sys_path = .

# timezone to use when rendering the date within the migration file
# as well as the filename.
# If specified, requires the python-dateutil library that can be
# installed by adding `alembic[tz]` to the pip requirements
# string value is passed to dateutil.tz.gettz()
# leave blank for localtime
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

# version num format
version_num_format = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d%%(second).2d

# version path separator; As mentioned above, this is the character used to split
# version_locations. The default within new alembic.ini files is "os", which uses
# os.pathsep. If this key is omitted entirely, it falls back to the legacy
# behavior of splitting on spaces and/or commas.
# Valid values for version_path_separator are:
#
# version_path_separator = :
# version_path_separator = ;
# version_path_separator = space
version_path_separator = os

# the output encoding used when revision files
# are written from script.py.mako
# output_encoding = utf-8

sqlalchemy.url = {self.database_url}

[post_write_hooks]
# post_write_hooks defines scripts or Python functions that are run
# on newly generated revision scripts.  See the documentation for further
# detail and examples

# format using "black" - use the console_scripts runner, against the "black" entrypoint
# hooks = black
# black.type = console_scripts
# black.entrypoint = black
# black.options = -l 79 REVISION_SCRIPT_FILENAME

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
        
        with open(alembic_ini_path, 'w') as f:
            f.write(alembic_ini_content)
    
    def initialize_migrations(self) -> None:
        """Initialize Alembic migration environment."""
        try:
            # Check if migrations are already initialized
            if (self.migrations_dir / "versions").exists():
                logger.info("Migrations already initialized")
                return
            
            logger.info("Initializing database migrations...")
            
            # Initialize Alembic
            command.init(self.alembic_cfg, str(self.migrations_dir))
            
            # Create custom env.py
            self._create_env_py()
            
            logger.info("Migration environment initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize migrations: {e}")
            raise
    
    def _create_env_py(self) -> None:
        """Create custom env.py for migrations."""
        env_py_content = '''"""Alembic migration environment for AutoGT TARA platform."""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import your model's MetaData object here
from autogt.models import Base
target_metadata = Base.metadata

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


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
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
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
        
        env_py_path = self.migrations_dir / "env.py"
        with open(env_py_path, 'w') as f:
            f.write(env_py_content)
    
    def create_initial_migration(self) -> None:
        """Create initial migration with all models."""
        try:
            logger.info("Creating initial migration...")
            
            # Generate initial migration
            command.revision(
                self.alembic_cfg,
                autogenerate=True,
                message="Initial migration: all TARA models"
            )
            
            logger.info("Initial migration created")
            
        except Exception as e:
            logger.error(f"Failed to create initial migration: {e}")
            raise
    
    def apply_migrations(self) -> None:
        """Apply all pending migrations."""
        try:
            logger.info("Applying database migrations...")
            
            # Run migrations to head
            command.upgrade(self.alembic_cfg, "head")
            
            logger.info("Migrations applied successfully")
            
        except Exception as e:
            logger.error(f"Failed to apply migrations: {e}")
            raise
    
    def get_current_revision(self) -> str:
        """Get current database revision."""
        try:
            engine = create_engine(self.database_url)
            
            with engine.connect() as conn:
                context = migration.MigrationContext.configure(conn)
                return context.get_current_revision() or "None"
                
        except Exception as e:
            logger.error(f"Failed to get current revision: {e}")
            return "Unknown"
    
    def create_migration(self, message: str, autogenerate: bool = True) -> None:
        """Create a new migration.
        
        Args:
            message: Migration message
            autogenerate: Whether to auto-generate changes
        """
        try:
            logger.info(f"Creating migration: {message}")
            
            command.revision(
                self.alembic_cfg,
                autogenerate=autogenerate,
                message=message
            )
            
            logger.info("Migration created")
            
        except Exception as e:
            logger.error(f"Failed to create migration: {e}")
            raise
    
    def rollback_migration(self, revision: str = "-1") -> None:
        """Rollback to a specific migration.
        
        Args:
            revision: Revision to rollback to (default: previous)
        """
        try:
            logger.info(f"Rolling back to revision: {revision}")
            
            command.downgrade(self.alembic_cfg, revision)
            
            logger.info("Rollback completed")
            
        except Exception as e:
            logger.error(f"Failed to rollback migration: {e}")
            raise
    
    def setup_database(self) -> None:
        """Complete database setup with migrations."""
        try:
            logger.info("Setting up database with migrations...")
            
            # Initialize migration environment
            self.initialize_migrations()
            
            # Create initial migration if needed
            current_revision = self.get_current_revision()
            if current_revision == "None":
                self.create_initial_migration()
            
            # Apply all migrations
            self.apply_migrations()
            
            logger.info("Database setup completed")
            
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            raise


def setup_database(database_url: str) -> None:
    """Setup database with migrations.
    
    Args:
        database_url: Database connection URL
    """
    manager = MigrationManager(database_url)
    manager.setup_database()


def create_migration(database_url: str, message: str) -> None:
    """Create a new migration.
    
    Args:
        database_url: Database connection URL
        message: Migration message
    """
    manager = MigrationManager(database_url)
    manager.create_migration(message)