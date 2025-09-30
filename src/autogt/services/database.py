"""Database service with SQLAlchemy session management for AutoGT TARA platform.

Reference: plan.md lines 74 (SQLite dev, PostgreSQL prod)
Provides session management, connection pooling, and migration support.
"""

import os
from typing import Generator, Optional, Dict, Any
from contextlib import contextmanager
from sqlalchemy import create_engine, Engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import logging

from ..models import Base


logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Custom exception for database operations."""
    pass


class DatabaseService:
    """Database service for AutoGT TARA platform.
    
    Supports SQLite for development and PostgreSQL for production.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize database service.
        
        Args:
            database_url: Database connection URL. If None, uses environment variables.
        """
        self.database_url = database_url or self._get_database_url()
        self.engine: Optional[Engine] = None
        self.session_factory: Optional[sessionmaker] = None
        self._setup_engine()
        self._setup_session_factory()
        # Auto-create tables if they don't exist
        self.create_all_tables()
    
    def _get_database_url(self) -> str:
        """Get database URL from environment or use SQLite default."""
        # Check for explicit database URL
        db_url = os.getenv('DATABASE_URL')
        if db_url:
            return db_url
        
        # Check for PostgreSQL components
        db_host = os.getenv('DB_HOST')
        if db_host:
            db_user = os.getenv('DB_USER', 'autogt')
            db_password = os.getenv('DB_PASSWORD', '')
            db_name = os.getenv('DB_NAME', 'autogt_tara')
            db_port = os.getenv('DB_PORT', '5432')
            
            password_part = f":{db_password}" if db_password else ""
            return f"postgresql://{db_user}{password_part}@{db_host}:{db_port}/{db_name}"
        
        # Default to SQLite for development
        db_path = os.getenv('DB_PATH', 'autogt_tara.db')
        return f"sqlite:///{db_path}"
    
    def _setup_engine(self) -> None:
        """Setup SQLAlchemy engine with appropriate configuration."""
        try:
            if self.database_url.startswith('sqlite'):
                # SQLite configuration for development
                self.engine = create_engine(
                    self.database_url,
                    poolclass=StaticPool,
                    pool_pre_ping=True,
                    connect_args={
                        "check_same_thread": False,
                        "timeout": 30
                    },
                    echo=os.getenv('SQL_DEBUG', '').lower() == 'true'
                )
                
                # Enable foreign key constraints for SQLite
                @event.listens_for(self.engine, "connect")
                def set_sqlite_pragma(dbapi_connection, connection_record):
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()
                
            else:
                # PostgreSQL configuration for production
                self.engine = create_engine(
                    self.database_url,
                    pool_size=5,
                    max_overflow=10,
                    pool_pre_ping=True,
                    pool_recycle=3600,  # 1 hour
                    echo=os.getenv('SQL_DEBUG', '').lower() == 'true'
                )
            
            logger.info(f"Database engine created for: {self.database_url.split('://')[0]}")
            
        except Exception as e:
            raise DatabaseError(f"Failed to create database engine: {e}")
    
    def _setup_session_factory(self) -> None:
        """Setup session factory."""
        if not self.engine:
            raise DatabaseError("Engine not initialized")
        
        self.session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False
        )
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup.
        
        Yields:
            SQLAlchemy session
            
        Raises:
            DatabaseError: If session operations fail
        """
        if not self.session_factory:
            raise DatabaseError("Session factory not initialized")
        
        session = self.session_factory()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            session.close()
    
    def create_all_tables(self) -> None:
        """Create all database tables.
        
        Raises:
            DatabaseError: If table creation fails
        """
        if not self.engine:
            raise DatabaseError("Engine not initialized")
        
        try:
            Base.metadata.create_all(self.engine)
            logger.info("All database tables created successfully")
        except Exception as e:
            raise DatabaseError(f"Failed to create tables: {e}")
    
    def drop_all_tables(self) -> None:
        """Drop all database tables. USE WITH CAUTION.
        
        Raises:
            DatabaseError: If table drop fails
        """
        if not self.engine:
            raise DatabaseError("Engine not initialized")
        
        try:
            Base.metadata.drop_all(self.engine)
            logger.warning("All database tables dropped")
        except Exception as e:
            raise DatabaseError(f"Failed to drop tables: {e}")
    
    def test_connection(self) -> bool:
        """Test database connectivity.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.get_session() as session:
                # Simple query to test connection
                session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Get database engine information.
        
        Returns:
            Dictionary with engine information
        """
        if not self.engine:
            return {"status": "not_initialized"}
        
        return {
            "status": "initialized",
            "url": self.database_url.split('://')[0] + "://[HIDDEN]",
            "dialect": self.engine.dialect.name,
            "driver": self.engine.dialect.driver,
            "pool_size": getattr(self.engine.pool, 'size', 'N/A'),
            "pool_overflow": getattr(self.engine.pool, 'overflow', 'N/A'),
        }
    
    def execute_raw_sql(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute raw SQL query. USE WITH CAUTION.
        
        Args:
            sql: SQL query string
            params: Query parameters
            
        Returns:
            Query result
        """
        try:
            with self.get_session() as session:
                result = session.execute(sql, params or {})
                session.commit()
                return result
        except Exception as e:
            raise DatabaseError(f"Raw SQL execution failed: {e}")
    
    def get_table_info(self) -> Dict[str, Any]:
        """Get information about existing tables.
        
        Returns:
            Dictionary with table information
        """
        if not self.engine:
            raise DatabaseError("Engine not initialized")
        
        try:
            from sqlalchemy import inspect
            inspector = inspect(self.engine)
            
            tables = {}
            for table_name in inspector.get_table_names():
                columns = inspector.get_columns(table_name)
                tables[table_name] = {
                    "columns": len(columns),
                    "column_names": [col['name'] for col in columns]
                }
            
            return {
                "table_count": len(tables),
                "tables": tables
            }
        except Exception as e:
            raise DatabaseError(f"Failed to get table info: {e}")
    
    def backup_sqlite_database(self, backup_path: str) -> None:
        """Backup SQLite database. Only works with SQLite.
        
        Args:
            backup_path: Path for backup file
        """
        if not self.database_url.startswith('sqlite'):
            raise DatabaseError("Backup only supported for SQLite databases")
        
        try:
            import sqlite3
            import shutil
            
            # Extract database path from URL
            db_path = self.database_url.replace('sqlite:///', '')
            
            # Copy database file
            shutil.copy2(db_path, backup_path)
            logger.info(f"Database backed up to: {backup_path}")
            
        except Exception as e:
            raise DatabaseError(f"Database backup failed: {e}")
    
    def close(self) -> None:
        """Close database connections and cleanup."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")


# Global database service instance
_db_service: Optional[DatabaseService] = None


def get_database_service() -> DatabaseService:
    """Get global database service instance.
    
    Returns:
        DatabaseService instance
    """
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service


def initialize_database(database_url: Optional[str] = None) -> DatabaseService:
    """Initialize global database service.
    
    Args:
        database_url: Optional database URL override
        
    Returns:
        DatabaseService instance
    """
    global _db_service
    _db_service = DatabaseService(database_url)
    return _db_service