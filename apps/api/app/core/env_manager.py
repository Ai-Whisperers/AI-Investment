"""
Environment Configuration Manager
Handles environment variables and configuration across different deployment targets
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class DeploymentTarget(Enum):
    """Supported deployment targets."""
    LOCAL = "local"
    RENDER = "render"
    RAILWAY = "railway"
    SUPABASE = "supabase"
    VERCEL = "vercel"
    CLOUDFLARE = "cloudflare"


@dataclass
class ServiceConfig:
    """Configuration for a service."""
    name: str
    provider: str
    url: Optional[str] = None
    api_key: Optional[str] = None
    settings: Optional[Dict] = None


class EnvironmentManager:
    """Manages environment configuration across different deployment targets."""
    
    def __init__(self, env_file: Optional[str] = None):
        self.env_file = env_file or '.env'
        self.configs = {}
        self.target = self._detect_deployment_target()
        self._load_configurations()
        
    def _detect_deployment_target(self) -> DeploymentTarget:
        """Detect current deployment target based on environment variables."""
        
        # Check for platform-specific env vars
        if os.getenv('RENDER'):
            return DeploymentTarget.RENDER
        elif os.getenv('RAILWAY_ENVIRONMENT'):
            return DeploymentTarget.RAILWAY
        elif os.getenv('VERCEL'):
            return DeploymentTarget.VERCEL
        elif os.getenv('CF_WORKERS'):
            return DeploymentTarget.CLOUDFLARE
        elif os.getenv('SUPABASE_URL'):
            return DeploymentTarget.SUPABASE
        else:
            return DeploymentTarget.LOCAL
            
    def _load_configurations(self):
        """Load configurations for all services."""
        
        # Database configuration
        self.configs['database'] = self._get_database_config()
        
        # Cache configuration
        self.configs['cache'] = self._get_cache_config()
        
        # API configurations
        self.configs['apis'] = self._get_api_configs()
        
        # Authentication configuration
        self.configs['auth'] = self._get_auth_config()
        
        # Monitoring configuration
        self.configs['monitoring'] = self._get_monitoring_config()
        
    def _get_database_config(self) -> ServiceConfig:
        """Get database configuration based on deployment target."""
        
        if self.target == DeploymentTarget.SUPABASE:
            return ServiceConfig(
                name="database",
                provider="supabase",
                url=os.getenv('SUPABASE_DATABASE_URL'),
                settings={
                    'pool_size': 5,
                    'max_overflow': 10,
                    'pool_recycle': 300,
                    'ssl_mode': 'require'
                }
            )
        elif self.target == DeploymentTarget.RENDER:
            return ServiceConfig(
                name="database",
                provider="render",
                url=os.getenv('DATABASE_URL'),
                settings={
                    'pool_size': 10,
                    'max_overflow': 20,
                    'pool_recycle': 3600
                }
            )
        elif self.target == DeploymentTarget.RAILWAY:
            return ServiceConfig(
                name="database",
                provider="railway",
                url=os.getenv('RAILWAY_DATABASE_URL'),
                settings={
                    'pool_size': 10,
                    'max_overflow': 15,
                    'pool_recycle': 1800
                }
            )
        else:  # Local development
            return ServiceConfig(
                name="database",
                provider="postgresql",
                url=os.getenv('DATABASE_URL', 'postgresql://localhost/waardhaven'),
                settings={
                    'pool_size': 5,
                    'max_overflow': 10,
                    'echo': True  # Enable SQL logging in development
                }
            )
            
    def _get_cache_config(self) -> ServiceConfig:
        """Get cache configuration based on deployment target."""
        
        # Try different Redis providers
        redis_url = (
            os.getenv('REDIS_URL') or
            os.getenv('UPSTASH_REDIS_URL') or
            os.getenv('REDIS_CLOUD_URL') or
            os.getenv('REDISCLOUD_URL')
        )
        
        if redis_url:
            # Determine provider from URL
            if 'upstash' in redis_url:
                provider = 'upstash'
            elif 'rediscloud' in redis_url or 'redis-cloud' in redis_url:
                provider = 'redis_cloud'
            else:
                provider = 'redis'
                
            return ServiceConfig(
                name="cache",
                provider=provider,
                url=redis_url,
                settings={
                    'decode_responses': True,
                    'max_connections': 10,
                    'socket_timeout': 5
                }
            )
        else:
            # Fallback to in-memory cache
            return ServiceConfig(
                name="cache",
                provider="memory",
                url=None,
                settings={
                    'max_size': 1000,
                    'ttl': 300
                }
            )
            
    def _get_api_configs(self) -> Dict[str, ServiceConfig]:
        """Get API configurations."""
        
        return {
            'reddit': ServiceConfig(
                name="reddit",
                provider="praw",
                api_key=os.getenv('REDDIT_CLIENT_SECRET'),
                settings={
                    'client_id': os.getenv('REDDIT_CLIENT_ID'),
                    'user_agent': 'waardhaven-autoindex/1.0',
                    'rate_limit': 60  # requests per minute
                }
            ),
            'youtube': ServiceConfig(
                name="youtube",
                provider="youtube_data_api",
                api_key=os.getenv('YOUTUBE_API_KEY'),
                settings={
                    'daily_quota': 10000,
                    'search_cost': 100,
                    'video_cost': 1
                }
            ),
            'marketaux': ServiceConfig(
                name="marketaux",
                provider="marketaux",
                api_key=os.getenv('MARKETAUX_API_KEY'),
                settings={
                    'rate_limit': 100,  # requests per day (free tier)
                    'timeout': 30
                }
            ),
            'twelvedata': ServiceConfig(
                name="twelvedata",
                provider="twelvedata",
                api_key=os.getenv('TWELVEDATA_API_KEY'),
                settings={
                    'rate_limit': 8,  # requests per minute (free tier)
                    'batch_size': 8,
                    'timeout': 10
                }
            ),
            'discord': ServiceConfig(
                name="discord",
                provider="webhook",
                url=os.getenv('DISCORD_WEBHOOK'),
                settings={
                    'rate_limit': 30,  # messages per minute
                    'max_embeds': 10
                }
            )
        }
        
    def _get_auth_config(self) -> ServiceConfig:
        """Get authentication configuration."""
        
        return ServiceConfig(
            name="auth",
            provider="jwt",
            api_key=os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
            settings={
                'algorithm': os.getenv('JWT_ALGORITHM', 'HS256'),
                'access_token_expire': int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30')),
                'refresh_token_expire': int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', '7')),
                'google_client_id': os.getenv('GOOGLE_CLIENT_ID'),
                'google_client_secret': os.getenv('GOOGLE_CLIENT_SECRET')
            }
        )
        
    def _get_monitoring_config(self) -> ServiceConfig:
        """Get monitoring configuration."""
        
        return ServiceConfig(
            name="monitoring",
            provider="custom",
            settings={
                'sentry_dsn': os.getenv('SENTRY_DSN'),
                'log_level': os.getenv('LOG_LEVEL', 'INFO'),
                'metrics_enabled': os.getenv('METRICS_ENABLED', 'false').lower() == 'true',
                'health_check_interval': 60,
                'alert_threshold': {
                    'error_rate': 0.05,
                    'response_time': 1000,  # ms
                    'memory_usage': 80  # percent
                }
            }
        )
        
    def get_config(self, service: str) -> Optional[ServiceConfig]:
        """Get configuration for a specific service."""
        
        if service in self.configs:
            return self.configs[service]
        elif service in self.configs.get('apis', {}):
            return self.configs['apis'][service]
        else:
            logger.warning(f"No configuration found for service: {service}")
            return None
            
    def get_all_configs(self) -> Dict[str, Any]:
        """Get all configurations."""
        return self.configs
        
    def validate_configuration(self) -> List[str]:
        """Validate that all required configurations are present."""
        
        errors = []
        warnings = []
        
        # Check critical configurations
        if not self.configs.get('database') or not self.configs['database'].url:
            errors.append("Database URL not configured")
            
        # Check API keys
        apis_to_check = ['reddit', 'youtube', 'marketaux', 'twelvedata']
        for api in apis_to_check:
            api_config = self.configs.get('apis', {}).get(api)
            if not api_config or not api_config.api_key:
                warnings.append(f"{api.upper()} API key not configured")
                
        # Check auth configuration
        auth_config = self.configs.get('auth')
        if auth_config and auth_config.api_key == 'dev-secret-key-change-in-production':
            if self.target != DeploymentTarget.LOCAL:
                errors.append("Using default SECRET_KEY in non-local environment")
                
        return errors + warnings
        
    def export_env_file(self, filepath: str = '.env.example'):
        """Export current configuration to env file format."""
        
        lines = [
            "# Waardhaven AutoIndex Environment Configuration",
            f"# Generated for: {self.target.value}",
            "",
            "# Database",
            f"DATABASE_URL={self.configs['database'].url or ''}",
            "",
            "# Cache",
            f"REDIS_URL={self.configs['cache'].url or ''}",
            "",
            "# Authentication",
            f"SECRET_KEY={self.configs['auth'].api_key}",
            f"JWT_ALGORITHM={self.configs['auth'].settings['algorithm']}",
            f"ACCESS_TOKEN_EXPIRE_MINUTES={self.configs['auth'].settings['access_token_expire']}",
            "",
            "# APIs",
        ]
        
        for api_name, api_config in self.configs.get('apis', {}).items():
            if api_config.api_key:
                lines.append(f"{api_name.upper()}_API_KEY={api_config.api_key}")
            if api_config.url:
                lines.append(f"{api_name.upper()}_URL={api_config.url}")
                
            # Add specific settings
            if api_name == 'reddit' and api_config.settings:
                lines.append(f"REDDIT_CLIENT_ID={api_config.settings.get('client_id', '')}")
                
        # Write to file
        with open(filepath, 'w') as f:
            f.write('\n'.join(lines))
            
        logger.info(f"Environment configuration exported to {filepath}")
        
    def apply_to_environment(self):
        """Apply configurations to environment variables."""
        
        # Set database URL
        if self.configs['database'].url:
            os.environ['DATABASE_URL'] = self.configs['database'].url
            
        # Set cache URL
        if self.configs['cache'].url:
            os.environ['REDIS_URL'] = self.configs['cache'].url
            
        # Set API keys
        for api_name, api_config in self.configs.get('apis', {}).items():
            if api_config.api_key:
                os.environ[f'{api_name.upper()}_API_KEY'] = api_config.api_key
                
        logger.info(f"Environment configured for {self.target.value}")


# Singleton instance
_env_manager = None


def get_env_manager() -> EnvironmentManager:
    """Get or create environment manager instance."""
    global _env_manager
    if not _env_manager:
        _env_manager = EnvironmentManager()
    return _env_manager


def validate_environment() -> bool:
    """Validate environment configuration."""
    
    manager = get_env_manager()
    errors = manager.validate_configuration()
    
    if errors:
        logger.error("Environment validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        return False
        
    logger.info(f"Environment validated for {manager.target.value}")
    return True