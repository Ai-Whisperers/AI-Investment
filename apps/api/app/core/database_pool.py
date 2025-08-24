"""
Enhanced Database Connection Pool Management
Fixes connection exhaustion issues in test suite and production
"""

import logging
from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import Session, sessionmaker, scoped_session
from sqlalchemy.pool import NullPool, QueuePool
import os

logger = logging.getLogger(__name__)


class DatabasePoolManager:
    """Manages database connection pools for different environments."""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv('DATABASE_URL')
        self.engine = None
        self.session_factory = None
        self.scoped_session = None
        self._is_testing = 'pytest' in sys.modules or os.getenv('TESTING') == 'true'
        
    def create_engine(self):
        """Create SQLAlchemy engine with appropriate pool configuration."""
        
        if not self.database_url:
            raise ValueError("Database URL not provided")
            
        # Detect database type
        is_sqlite = 'sqlite' in self.database_url.lower()
        is_testing = self._is_testing
        
        if is_sqlite:
            # SQLite configuration (for testing)
            engine_config = {
                'connect_args': {
                    'check_same_thread': False,  # Allow multi-threading
                    'timeout': 30  # Increase timeout
                },
                'poolclass': NullPool if is_testing else QueuePool,
                'echo': os.getenv('SQL_ECHO', 'false').lower() == 'true'
            }
            
            # For in-memory SQLite, use StaticPool to share connection
            if ':memory:' in self.database_url:
                from sqlalchemy.pool import StaticPool
                engine_config['poolclass'] = StaticPool
                
        else:
            # PostgreSQL configuration
            if is_testing:
                # Testing configuration - smaller pool
                engine_config = {
                    'poolclass': NullPool,  # No connection pooling for tests
                    'echo': False,
                    'connect_args': {
                        'connect_timeout': 10,
                        'application_name': 'waardhaven_test'
                    }
                }
            else:
                # Production configuration
                engine_config = {
                    'pool_size': int(os.getenv('DB_POOL_SIZE', '10')),
                    'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '20')),
                    'pool_pre_ping': True,  # Verify connections before using
                    'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', '3600')),
                    'echo_pool': os.getenv('SQL_ECHO_POOL', 'false').lower() == 'true',
                    'echo': os.getenv('SQL_ECHO', 'false').lower() == 'true',
                    'connect_args': {
                        'connect_timeout': 10,
                        'application_name': 'waardhaven_api',
                        'keepalives': 1,
                        'keepalives_idle': 30,
                        'keepalives_interval': 10,
                        'keepalives_count': 5,
                    }
                }
                
                # Supabase-specific settings
                if 'supabase' in self.database_url.lower():
                    engine_config['pool_size'] = 5  # Smaller pool for Supabase
                    engine_config['max_overflow'] = 10
                    engine_config['pool_recycle'] = 300  # 5 minutes
                    
        # Create engine
        self.engine = create_engine(self.database_url, **engine_config)
        
        # Add event listeners for debugging
        if os.getenv('DEBUG_POOL', 'false').lower() == 'true':
            self._setup_pool_debugging()
            
        logger.info(f"Database engine created with pool class: {engine_config.get('poolclass', QueuePool).__name__}")
        
        return self.engine
        
    def create_session_factory(self):
        """Create session factory with proper configuration."""
        
        if not self.engine:
            self.create_engine()
            
        # Create session factory
        self.session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False  # Prevent lazy loading issues
        )
        
        # Create scoped session for thread safety
        self.scoped_session = scoped_session(self.session_factory)
        
        return self.session_factory
        
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup."""
        
        if not self.session_factory:
            self.create_session_factory()
            
        session = self.session_factory()
        
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
            
    def get_scoped_session(self) -> Session:
        """Get a thread-local session."""
        
        if not self.scoped_session:
            self.create_session_factory()
            
        return self.scoped_session()
        
    def remove_scoped_session(self):
        """Remove the current thread-local session."""
        
        if self.scoped_session:
            self.scoped_session.remove()
            
    def dispose_engine(self):
        """Dispose of all connections in the pool."""
        
        if self.engine:
            self.engine.dispose()
            logger.info("Database engine disposed")
            
    def get_pool_status(self) -> dict:
        """Get current pool status for monitoring."""
        
        if not self.engine or not hasattr(self.engine.pool, 'status'):
            return {'status': 'unavailable'}
            
        pool = self.engine.pool
        
        return {
            'size': getattr(pool, 'size', 0),
            'checked_in': getattr(pool, 'checkedin', 0),
            'checked_out': getattr(pool, 'checkedout', 0),
            'overflow': getattr(pool, 'overflow', 0),
            'total': getattr(pool, 'checkedin', 0) + getattr(pool, 'checkedout', 0)
        }
        
    def _setup_pool_debugging(self):
        """Setup event listeners for pool debugging."""
        
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            logger.debug(f"Pool: Connection created - {id(dbapi_conn)}")
            
        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            logger.debug(f"Pool: Connection checked out - {id(dbapi_conn)}")
            
        @event.listens_for(self.engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            logger.debug(f"Pool: Connection checked in - {id(dbapi_conn)}")
            
        @event.listens_for(self.engine, "close")
        def receive_close(dbapi_conn, connection_record):
            logger.debug(f"Pool: Connection closed - {id(dbapi_conn)}")


# Global pool manager instance
_pool_manager = None


def get_pool_manager() -> DatabasePoolManager:
    """Get or create the global pool manager."""
    
    global _pool_manager
    if not _pool_manager:
        _pool_manager = DatabasePoolManager()
    return _pool_manager


def get_db_session() -> Generator[Session, None, None]:
    """Get a database session for use in FastAPI dependencies."""
    
    manager = get_pool_manager()
    with manager.get_session() as session:
        yield session


def cleanup_connections():
    """Cleanup all database connections (useful for tests)."""
    
    manager = get_pool_manager()
    manager.remove_scoped_session()
    manager.dispose_engine()
    
    global _pool_manager
    _pool_manager = None
    
    logger.info("Database connections cleaned up")


# FastAPI dependency
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions."""
    
    manager = get_pool_manager()
    session = manager.get_scoped_session()
    
    try:
        yield session
    finally:
        manager.remove_scoped_session()


# Test-specific utilities
class TestDatabaseManager:
    """Database manager for testing with proper isolation."""
    
    def __init__(self):
        self.test_db_url = os.getenv('TEST_DATABASE_URL', 'sqlite:///:memory:')
        self.manager = DatabasePoolManager(self.test_db_url)
        
    def setup(self):
        """Setup test database."""
        
        from app.database import Base
        
        # Create engine and tables
        engine = self.manager.create_engine()
        Base.metadata.create_all(bind=engine)
        
        logger.info("Test database setup complete")
        
    def teardown(self):
        """Teardown test database."""
        
        from app.database import Base
        
        if self.manager.engine:
            # Drop all tables
            Base.metadata.drop_all(bind=self.manager.engine)
            
            # Cleanup connections
            self.manager.dispose_engine()
            
        logger.info("Test database teardown complete")
        
    @contextmanager
    def get_test_session(self):
        """Get an isolated test session."""
        
        with self.manager.get_session() as session:
            yield session
            
            # Rollback any changes (for test isolation)
            session.rollback()


# Import guard for sys module
import sys