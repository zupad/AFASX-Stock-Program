"""
Configuration management for AFI Stock Tracker
Handles API keys, user preferences, and application settings
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class APIConfig:
    """API configuration settings"""
    alpha_vantage_key: Optional[str] = None
    finnhub_key: Optional[str] = None
    polygon_key: Optional[str] = None
    news_api_key: Optional[str] = None
    pushbullet_key: Optional[str] = None
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    redis_url: Optional[str] = None

@dataclass
class PortfolioConfig:
    """Portfolio tracking configuration"""
    afi_shares: float = 0.0
    purchase_price: float = 0.0
    purchase_date: Optional[str] = None
    dividend_reinvestment: bool = True
    currency: str = "AUD"

@dataclass
class AlertConfig:
    """Alert and notification settings"""
    email_alerts: bool = False
    email_address: Optional[str] = None
    push_notifications: bool = False
    price_change_threshold: float = 5.0  # Percentage
    volume_threshold: float = 150.0  # Percentage of average
    news_sentiment_threshold: float = -0.5  # Negative sentiment alert

@dataclass
class DisplayConfig:
    """Display and UI preferences"""
    theme: str = "dark"
    chart_style: str = "plotly"
    refresh_interval: int = 300  # seconds
    show_technical_indicators: bool = True
    show_news: bool = True
    default_timeframe: str = "1y"

class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "settings.json"
        self.env_file = self.config_dir / ".env"
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
        # Load configurations
        self.api_config = self._load_api_config()
        self.portfolio_config = self._load_portfolio_config()
        self.alert_config = self._load_alert_config()
        self.display_config = self._load_display_config()
    
    def _load_api_config(self) -> APIConfig:
        """Load API configuration from environment variables"""
        return APIConfig(
            alpha_vantage_key=os.getenv('ALPHA_VANTAGE_API_KEY'),
            finnhub_key=os.getenv('FINNHUB_API_KEY'),
            polygon_key=os.getenv('POLYGON_API_KEY'),
            news_api_key=os.getenv('NEWS_API_KEY'),
            pushbullet_key=os.getenv('PUSHBULLET_API_KEY'),
            twilio_account_sid=os.getenv('TWILIO_ACCOUNT_SID'),
            twilio_auth_token=os.getenv('TWILIO_AUTH_TOKEN'),
            redis_url=os.getenv('REDIS_URL', 'redis://localhost:6379')
        )
    
    def _load_config_from_file(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}
    
    def _load_portfolio_config(self) -> PortfolioConfig:
        """Load portfolio configuration"""
        config_data = self._load_config_from_file()
        portfolio_data = config_data.get('portfolio', {})
        return PortfolioConfig(**portfolio_data)
    
    def _load_alert_config(self) -> AlertConfig:
        """Load alert configuration"""
        config_data = self._load_config_from_file()
        alert_data = config_data.get('alerts', {})
        return AlertConfig(**alert_data)
    
    def _load_display_config(self) -> DisplayConfig:
        """Load display configuration"""
        config_data = self._load_config_from_file()
        display_data = config_data.get('display', {})
        return DisplayConfig(**display_data)
    
    def save_config(self):
        """Save all configurations to file"""
        config_data = {
            'portfolio': asdict(self.portfolio_config),
            'alerts': asdict(self.alert_config),
            'display': asdict(self.display_config)
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def update_portfolio(self, shares: float, purchase_price: float, purchase_date: str):
        """Update portfolio configuration"""
        self.portfolio_config.afi_shares = shares
        self.portfolio_config.purchase_price = purchase_price
        self.portfolio_config.purchase_date = purchase_date
        self.save_config()
    
    def update_alerts(self, **kwargs):
        """Update alert configuration"""
        for key, value in kwargs.items():
            if hasattr(self.alert_config, key):
                setattr(self.alert_config, key, value)
        self.save_config()
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for a specific service"""
        key_mapping = {
            'alpha_vantage': self.api_config.alpha_vantage_key,
            'finnhub': self.api_config.finnhub_key,
            'polygon': self.api_config.polygon_key,
            'news_api': self.api_config.news_api_key,
            'pushbullet': self.api_config.pushbullet_key,
        }
        return key_mapping.get(service)
    
    def has_api_key(self, service: str) -> bool:
        """Check if API key exists for a service"""
        return self.get_api_key(service) is not None
    
    def create_env_template(self):
        """Create .env template file"""
        template = """# API Keys for AFI Stock Tracker
# Get your free API keys from:

# Alpha Vantage (Stock data) - https://www.alphavantage.co/support/#api-key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here

# Finnhub (Financial data) - https://finnhub.io/register
FINNHUB_API_KEY=your_finnhub_key_here

# Polygon (Market data) - https://polygon.io/
POLYGON_API_KEY=your_polygon_key_here

# News API (Financial news) - https://newsapi.org/register
NEWS_API_KEY=your_news_api_key_here

# Pushbullet (Notifications) - https://www.pushbullet.com/
PUSHBULLET_API_KEY=your_pushbullet_key_here

# Twilio (SMS notifications) - https://www.twilio.com/
TWILIO_ACCOUNT_SID=your_twilio_sid_here
TWILIO_AUTH_TOKEN=your_twilio_token_here

# Redis (Optional caching) - Use local Redis or Redis Cloud
REDIS_URL=redis://localhost:6379
"""
        
        env_template_file = self.config_dir / ".env.template"
        with open(env_template_file, 'w') as f:
            f.write(template)
        
        print(f"Created .env template at {env_template_file}")
        print("Copy this file to .env and add your API keys")

# Global config instance
config = ConfigManager()