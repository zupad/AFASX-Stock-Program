"""
Enhanced configuration management with environment-based configs and feature flags
"""

import os
import json
import yaml
import toml
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum
from dotenv import load_dotenv


class Environment(Enum):
    """Application environments"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str = "sqlite:///data/afi_tracker.db"
    pool_size: int = 5
    max_overflow: int = 10
    echo: bool = False
    pool_pre_ping: bool = True
    pool_recycle: int = 3600


@dataclass
class CacheConfig:
    """Cache configuration"""
    enabled: bool = True
    redis_url: str = "redis://localhost:6379/0"
    default_ttl: int = 1800
    max_connections: int = 10


@dataclass
class APIConfig:
    """API configuration"""
    alpha_vantage_key: Optional[str] = None
    finnhub_key: Optional[str] = None
    polygon_key: Optional[str] = None
    news_api_key: Optional[str] = None
    rate_limit_enabled: bool = True
    timeout: int = 30
    max_retries: int = 3


@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    enabled: bool = True
    prometheus_enabled: bool = True
    health_check_interval: int = 60
    metrics_port: int = 9090
    log_level: str = "INFO"
    structured_logging: bool = True


@dataclass
class SecurityConfig:
    """Security configuration"""
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    bcrypt_rounds: int = 12
    api_key_encryption: bool = True
    rate_limiting: bool = True
    cors_enabled: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])


@dataclass
class FeatureFlags:
    """Feature flags configuration"""
    async_processing: bool = True
    caching: bool = True
    monitoring: bool = True
    predictive_analysis: bool = False
    real_time_updates: bool = False
    advanced_charts: bool = True
    news_sentiment: bool = True
    portfolio_tracking: bool = True
    alerts: bool = True
    backtesting: bool = False


@dataclass
class NotificationConfig:
    """Notification configuration"""
    email_enabled: bool = False
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    pushbullet_api_key: Optional[str] = None


class EnhancedConfigManager:
    """Enhanced configuration manager with environment support and feature flags"""
    
    def __init__(self, env: Optional[str] = None, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Determine environment
        self.environment = Environment(env or os.getenv('ENVIRONMENT', 'development'))
        
        # Load environment variables
        self._load_env_files()
        
        # Initialize configurations
        self.database = self._load_database_config()
        self.cache = self._load_cache_config()
        self.apis = self._load_api_config()
        self.monitoring = self._load_monitoring_config()
        self.security = self._load_security_config()
        self.features = self._load_feature_flags()
        self.notifications = self._load_notification_config()
        
        # Environment-specific overrides
        self._apply_environment_overrides()
    
    def _load_env_files(self):
        """Load environment files in order of precedence"""
        env_files = [
            self.config_dir / '.env',
            self.config_dir / f'.env.{self.environment.value}',
            self.config_dir / '.env.local'
        ]
        
        for env_file in env_files:
            if env_file.exists():
                load_dotenv(env_file, override=True)
    
    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration"""
        # Environment-specific defaults
        defaults = {
            Environment.DEVELOPMENT: {
                'url': 'sqlite:///data/afi_tracker_dev.db',
                'echo': True
            },
            Environment.TESTING: {
                'url': 'sqlite:///data/afi_tracker_test.db',
                'echo': False,
                'pool_size': 1
            },
            Environment.STAGING: {
                'url': os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/afi_staging'),
                'pool_size': 3
            },
            Environment.PRODUCTION: {
                'url': os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/afi_prod'),
                'pool_size': 10,
                'max_overflow': 20
            }
        }
        
        config_data = defaults.get(self.environment, {})
        
        # Override with environment variables
        config_data.update({
            'url': os.getenv('DATABASE_URL', config_data.get('url')),
            'pool_size': int(os.getenv('DB_POOL_SIZE', config_data.get('pool_size', 5))),
            'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', config_data.get('max_overflow', 10))),
            'echo': os.getenv('DB_ECHO', str(config_data.get('echo', False))).lower() == 'true'
        })
        
        return DatabaseConfig(**config_data)
    
    def _load_cache_config(self) -> CacheConfig:
        """Load cache configuration"""
        enabled = self.environment != Environment.TESTING
        
        return CacheConfig(
            enabled=os.getenv('CACHE_ENABLED', str(enabled)).lower() == 'true',
            redis_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
            default_ttl=int(os.getenv('CACHE_DEFAULT_TTL', '1800')),
            max_connections=int(os.getenv('CACHE_MAX_CONNECTIONS', '10'))
        )
    
    def _load_api_config(self) -> APIConfig:
        """Load API configuration"""
        return APIConfig(
            alpha_vantage_key=os.getenv('ALPHA_VANTAGE_API_KEY'),
            finnhub_key=os.getenv('FINNHUB_API_KEY'),
            polygon_key=os.getenv('POLYGON_API_KEY'),
            news_api_key=os.getenv('NEWS_API_KEY'),
            rate_limit_enabled=os.getenv('API_RATE_LIMIT_ENABLED', 'true').lower() == 'true',
            timeout=int(os.getenv('API_TIMEOUT', '30')),
            max_retries=int(os.getenv('API_MAX_RETRIES', '3'))
        )
    
    def _load_monitoring_config(self) -> MonitoringConfig:
        """Load monitoring configuration"""
        enabled = self.environment != Environment.TESTING
        
        return MonitoringConfig(
            enabled=os.getenv('MONITORING_ENABLED', str(enabled)).lower() == 'true',
            prometheus_enabled=os.getenv('PROMETHEUS_ENABLED', str(enabled)).lower() == 'true',
            health_check_interval=int(os.getenv('HEALTH_CHECK_INTERVAL', '60')),
            metrics_port=int(os.getenv('METRICS_PORT', '9090')),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            structured_logging=os.getenv('STRUCTURED_LOGGING', 'true').lower() == 'true'
        )
    
    def _load_security_config(self) -> SecurityConfig:
        """Load security configuration"""
        return SecurityConfig(
            jwt_secret_key=os.getenv('JWT_SECRET_KEY'),
            jwt_algorithm=os.getenv('JWT_ALGORITHM', 'HS256'),
            jwt_expire_hours=int(os.getenv('JWT_EXPIRE_HOURS', '24')),
            bcrypt_rounds=int(os.getenv('BCRYPT_ROUNDS', '12')),
            api_key_encryption=os.getenv('API_KEY_ENCRYPTION', 'true').lower() == 'true',
            rate_limiting=os.getenv('RATE_LIMITING', 'true').lower() == 'true',
            cors_enabled=os.getenv('CORS_ENABLED', 'true').lower() == 'true',
            cors_origins=os.getenv('CORS_ORIGINS', '*').split(',')
        )
    
    def _load_feature_flags(self) -> FeatureFlags:
        """Load feature flags"""
        # Environment-specific defaults
        prod_features = self.environment == Environment.PRODUCTION
        
        return FeatureFlags(
            async_processing=os.getenv('FEATURE_ASYNC_PROCESSING', 'true').lower() == 'true',
            caching=os.getenv('FEATURE_CACHING', 'true').lower() == 'true',
            monitoring=os.getenv('FEATURE_MONITORING', str(not prod_features)).lower() == 'true',
            predictive_analysis=os.getenv('FEATURE_PREDICTIVE_ANALYSIS', 'false').lower() == 'true',
            real_time_updates=os.getenv('FEATURE_REAL_TIME_UPDATES', 'false').lower() == 'true',
            advanced_charts=os.getenv('FEATURE_ADVANCED_CHARTS', 'true').lower() == 'true',
            news_sentiment=os.getenv('FEATURE_NEWS_SENTIMENT', 'true').lower() == 'true',
            portfolio_tracking=os.getenv('FEATURE_PORTFOLIO_TRACKING', 'true').lower() == 'true',
            alerts=os.getenv('FEATURE_ALERTS', 'true').lower() == 'true',
            backtesting=os.getenv('FEATURE_BACKTESTING', 'false').lower() == 'true'
        )
    
    def _load_notification_config(self) -> NotificationConfig:
        """Load notification configuration"""
        return NotificationConfig(
            email_enabled=os.getenv('EMAIL_ENABLED', 'false').lower() == 'true',
            smtp_host=os.getenv('SMTP_HOST'),
            smtp_port=int(os.getenv('SMTP_PORT', '587')),
            smtp_username=os.getenv('SMTP_USERNAME'),
            smtp_password=os.getenv('SMTP_PASSWORD'),
            slack_webhook_url=os.getenv('SLACK_WEBHOOK_URL'),
            pushbullet_api_key=os.getenv('PUSHBULLET_API_KEY')
        )
    
    def _apply_environment_overrides(self):
        """Apply environment-specific configuration overrides"""
        if self.environment == Environment.DEVELOPMENT:
            # Development overrides
            self.monitoring.log_level = "DEBUG"
            self.database.echo = True
            
        elif self.environment == Environment.TESTING:
            # Testing overrides
            self.cache.enabled = False
            self.monitoring.enabled = False
            self.features.predictive_analysis = False
            self.features.real_time_updates = False
            
        elif self.environment == Environment.PRODUCTION:
            # Production overrides
            self.monitoring.log_level = "WARNING"
            self.database.echo = False
            self.security.cors_origins = os.getenv('CORS_ORIGINS', 'https://your-domain.com').split(',')
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled"""
        return getattr(self.features, feature_name, False)
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for a service"""
        key_mapping = {
            'alpha_vantage': self.apis.alpha_vantage_key,
            'finnhub': self.apis.finnhub_key,
            'polygon': self.apis.polygon_key,
            'news_api': self.apis.news_api_key
        }
        return key_mapping.get(service.lower())
    
    def has_api_key(self, service: str) -> bool:
        """Check if API key exists for a service"""
        return self.get_api_key(service) is not None
    
    def export_config(self, format: str = 'json') -> str:
        """Export configuration in specified format"""
        config_dict = {
            'environment': self.environment.value,
            'database': asdict(self.database),
            'cache': asdict(self.cache),
            'apis': asdict(self.apis),
            'monitoring': asdict(self.monitoring),
            'security': asdict(self.security),
            'features': asdict(self.features),
            'notifications': asdict(self.notifications)
        }
        
        # Remove sensitive data
        if 'apis' in config_dict:
            for key in config_dict['apis']:
                if 'key' in key.lower() and config_dict['apis'][key]:
                    config_dict['apis'][key] = '***REDACTED***'
        
        if 'security' in config_dict:
            for key in config_dict['security']:
                if 'secret' in key.lower() or 'password' in key.lower():
                    if config_dict['security'][key]:
                        config_dict['security'][key] = '***REDACTED***'
        
        if format.lower() == 'yaml':
            return yaml.dump(config_dict, default_flow_style=False)
        elif format.lower() == 'toml':
            return toml.dumps(config_dict)
        else:  # JSON
            return json.dumps(config_dict, indent=2)
    
    def save_config_template(self, filename: str = 'config_template.env'):
        """Save configuration template file"""
        template = f"""# AFI Stock Tracker Configuration Template
# Environment: {self.environment.value}

# General Settings
ENVIRONMENT={self.environment.value}
LOG_LEVEL=INFO

# Database Configuration
DATABASE_URL=sqlite:///data/afi_tracker.db
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_ECHO=false

# Cache Configuration
CACHE_ENABLED=true
REDIS_URL=redis://localhost:6379/0
CACHE_DEFAULT_TTL=1800
CACHE_MAX_CONNECTIONS=10

# API Keys (get your keys from respective services)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
FINNHUB_API_KEY=your_finnhub_key_here
POLYGON_API_KEY=your_polygon_key_here
NEWS_API_KEY=your_news_api_key_here

# API Settings
API_RATE_LIMIT_ENABLED=true
API_TIMEOUT=30
API_MAX_RETRIES=3

# Monitoring
MONITORING_ENABLED=true
PROMETHEUS_ENABLED=true
HEALTH_CHECK_INTERVAL=60
METRICS_PORT=9090
STRUCTURED_LOGGING=true

# Security
JWT_SECRET_KEY=generate_a_secure_random_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24
API_KEY_ENCRYPTION=true
RATE_LIMITING=true
CORS_ENABLED=true
CORS_ORIGINS=*

# Feature Flags
FEATURE_ASYNC_PROCESSING=true
FEATURE_CACHING=true
FEATURE_MONITORING=true
FEATURE_PREDICTIVE_ANALYSIS=false
FEATURE_REAL_TIME_UPDATES=false
FEATURE_ADVANCED_CHARTS=true
FEATURE_NEWS_SENTIMENT=true
FEATURE_PORTFOLIO_TRACKING=true
FEATURE_ALERTS=true
FEATURE_BACKTESTING=false

# Notifications
EMAIL_ENABLED=false
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_email_password
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
PUSHBULLET_API_KEY=your_pushbullet_key_here
"""
        
        template_path = self.config_dir / filename
        with open(template_path, 'w') as f:
            f.write(template)
        
        print(f"Configuration template saved to {template_path}")
        return template_path


# Global configuration instance
enhanced_config = EnhancedConfigManager()