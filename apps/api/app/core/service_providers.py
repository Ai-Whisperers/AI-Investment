"""
Service Provider Abstraction Layer
Provides modular interfaces for swapping between different service providers
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import os
import logging
from datetime import datetime
import redis
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class DatabaseProvider(ABC):
    """Abstract base class for database providers."""
    
    @abstractmethod
    def connect(self) -> Any:
        """Establish database connection."""
        pass
        
    @abstractmethod
    def disconnect(self):
        """Close database connection."""
        pass
        
    @abstractmethod
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Execute a query and return results."""
        pass
        
    @abstractmethod
    def execute_command(self, command: str, params: Optional[tuple] = None) -> bool:
        """Execute a command (INSERT, UPDATE, DELETE)."""
        pass


class PostgreSQLProvider(DatabaseProvider):
    """PostgreSQL database provider (works with Supabase, Render, Railway)."""
    
    def __init__(self, connection_url: str):
        self.connection_url = connection_url
        self.engine = None
        self.session_factory = None
        
    def connect(self):
        """Create SQLAlchemy engine and session factory."""
        try:
            # Configure for different environments
            if 'supabase' in self.connection_url.lower():
                # Supabase-specific settings
                self.engine = create_engine(
                    self.connection_url,
                    pool_size=5,
                    max_overflow=10,
                    pool_pre_ping=True,
                    pool_recycle=300,  # Recycle connections every 5 minutes
                    connect_args={
                        "keepalives": 1,
                        "keepalives_idle": 30,
                        "keepalives_interval": 10,
                        "keepalives_count": 5,
                    }
                )
            else:
                # Standard PostgreSQL settings
                self.engine = create_engine(
                    self.connection_url,
                    pool_size=10,
                    max_overflow=20,
                    pool_pre_ping=True,
                    pool_recycle=3600
                )
                
            self.session_factory = sessionmaker(bind=self.engine)
            logger.info("Database connection established")
            return self.engine
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
            
    def disconnect(self):
        """Dispose of engine connections."""
        if self.engine:
            self.engine.dispose()
            
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Execute query using raw SQL."""
        with self.engine.connect() as conn:
            result = conn.execute(query, params or ())
            return [dict(row) for row in result]
            
    def execute_command(self, command: str, params: Optional[tuple] = None) -> bool:
        """Execute command using raw SQL."""
        try:
            with self.engine.connect() as conn:
                conn.execute(command, params or ())
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return False
            
    def get_session(self):
        """Get a new database session."""
        if not self.session_factory:
            self.connect()
        return self.session_factory()


class CacheProvider(ABC):
    """Abstract base class for cache providers."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
        
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        pass
        
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        pass
        
    @abstractmethod
    def flush(self) -> bool:
        """Flush all cache entries."""
        pass


class RedisProvider(CacheProvider):
    """Redis cache provider (works with Redis Cloud, Upstash, local)."""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.client = None
        self.connect()
        
    def connect(self):
        """Establish Redis connection."""
        try:
            # Parse Redis URL and connect
            if self.redis_url.startswith('rediss://'):
                # SSL connection (Redis Cloud, Upstash)
                self.client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    max_connections=10
                )
            else:
                # Standard connection
                self.client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                
            # Test connection
            self.client.ping()
            logger.info("Redis connection established")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            # Fallback to in-memory cache if Redis unavailable
            self.client = None
            
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
        if not self.client:
            return None
            
        try:
            import json
            value = self.client.get(key)
            if value:
                try:
                    return json.loads(value)
                except:
                    return value
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
            
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis with optional TTL."""
        if not self.client:
            return False
            
        try:
            import json
            # Serialize value
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            else:
                value = str(value)
                
            if ttl:
                return self.client.setex(key, ttl, value)
            else:
                return self.client.set(key, value)
                
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
            
    def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        if not self.client:
            return False
            
        try:
            return self.client.delete(key) > 0
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
            
    def flush(self) -> bool:
        """Flush all Redis entries."""
        if not self.client:
            return False
            
        try:
            return self.client.flushdb()
        except Exception as e:
            logger.error(f"Redis flush error: {e}")
            return False


class InMemoryCacheProvider(CacheProvider):
    """In-memory cache provider for development/testing."""
    
    def __init__(self):
        self.cache = {}
        self.ttl_tracker = {}
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache."""
        # Check if key exists and not expired
        if key in self.cache:
            if key in self.ttl_tracker:
                if datetime.now() > self.ttl_tracker[key]:
                    # Expired, remove it
                    del self.cache[key]
                    del self.ttl_tracker[key]
                    return None
            return self.cache[key]
        return None
        
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in memory cache."""
        self.cache[key] = value
        if ttl:
            from datetime import timedelta
            self.ttl_tracker[key] = datetime.now() + timedelta(seconds=ttl)
        return True
        
    def delete(self, key: str) -> bool:
        """Delete key from memory cache."""
        if key in self.cache:
            del self.cache[key]
            if key in self.ttl_tracker:
                del self.ttl_tracker[key]
            return True
        return False
        
    def flush(self) -> bool:
        """Clear all cache entries."""
        self.cache.clear()
        self.ttl_tracker.clear()
        return True


class ServiceProviderFactory:
    """Factory for creating service providers based on environment."""
    
    @staticmethod
    def create_database_provider() -> DatabaseProvider:
        """Create database provider based on environment."""
        # Check for database URLs in order of preference
        db_url = (
            os.getenv('SUPABASE_DATABASE_URL') or
            os.getenv('DATABASE_URL') or
            os.getenv('RAILWAY_DATABASE_URL') or
            'sqlite:///./test.db'  # Fallback for testing
        )
        
        if 'sqlite' in db_url:
            logger.warning("Using SQLite database (development/testing only)")
            
        return PostgreSQLProvider(db_url)
        
    @staticmethod
    def create_cache_provider() -> CacheProvider:
        """Create cache provider based on environment."""
        # Check for Redis URLs
        redis_url = (
            os.getenv('REDIS_URL') or
            os.getenv('UPSTASH_REDIS_URL') or
            os.getenv('REDIS_CLOUD_URL')
        )
        
        if redis_url:
            try:
                return RedisProvider(redis_url)
            except Exception as e:
                logger.warning(f"Failed to connect to Redis, using in-memory cache: {e}")
                
        # Fallback to in-memory cache
        logger.info("Using in-memory cache provider")
        return InMemoryCacheProvider()


# Global instances (singleton pattern)
_db_provider = None
_cache_provider = None


def get_database_provider() -> DatabaseProvider:
    """Get or create database provider instance."""
    global _db_provider
    if not _db_provider:
        _db_provider = ServiceProviderFactory.create_database_provider()
        _db_provider.connect()
    return _db_provider


def get_cache_provider() -> CacheProvider:
    """Get or create cache provider instance."""
    global _cache_provider
    if not _cache_provider:
        _cache_provider = ServiceProviderFactory.create_cache_provider()
    return _cache_provider


# Environment-specific configurations
class EnvironmentConfig:
    """Environment-specific configuration."""
    
    @staticmethod
    def get_config() -> Dict:
        """Get configuration based on environment."""
        env = os.getenv('ENVIRONMENT', 'development')
        
        base_config = {
            'debug': env != 'production',
            'testing': env == 'testing',
            'log_level': 'DEBUG' if env != 'production' else 'INFO',
            'cors_origins': ['*'] if env == 'development' else [
                'https://waardhaven.vercel.app',
                'https://waardhaven.com'
            ],
            'rate_limit': {
                'default': 100 if env == 'development' else 60,
                'authenticated': 500 if env == 'development' else 300
            }
        }
        
        # Environment-specific overrides
        if env == 'production':
            base_config.update({
                'ssl_required': True,
                'secure_cookies': True,
                'session_timeout': 1800  # 30 minutes
            })
        elif env == 'staging':
            base_config.update({
                'ssl_required': True,
                'secure_cookies': False,
                'session_timeout': 3600  # 1 hour
            })
        else:  # development/testing
            base_config.update({
                'ssl_required': False,
                'secure_cookies': False,
                'session_timeout': 86400  # 24 hours
            })
            
        return base_config