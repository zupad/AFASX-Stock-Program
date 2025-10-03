"""
Pydantic models for input validation and data security
"""

from pydantic import BaseModel, validator, Field, ConfigDict
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from enum import Enum
from decimal import Decimal
import re


class StockSymbol(BaseModel):
    """Validated stock symbol model"""
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol")
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    @validator('symbol')
    def validate_symbol(cls, v):
        # Remove any non-alphanumeric characters except dots and dashes
        cleaned = re.sub(r'[^A-Z0-9.\-]', '', v.upper())
        
        if not cleaned:
            raise ValueError('Invalid stock symbol format')
        
        # Basic validation for common patterns
        if not re.match(r'^[A-Z0-9]{1,6}(\.[A-Z]{1,3})?$', cleaned):
            raise ValueError('Stock symbol must be in format ABC or ABC.XY')
        
        return cleaned


class TimePerod(str, Enum):
    """Valid time periods for data requests"""
    ONE_DAY = "1d"
    FIVE_DAYS = "5d"
    ONE_MONTH = "1mo"
    THREE_MONTHS = "3mo"
    SIX_MONTHS = "6mo"
    ONE_YEAR = "1y"
    TWO_YEARS = "2y"
    FIVE_YEARS = "5y"
    TEN_YEARS = "10y"
    YEAR_TO_DATE = "ytd"
    MAX = "max"


class PriceData(BaseModel):
    """Validated price data model"""
    open_price: Optional[Decimal] = Field(None, ge=0, description="Opening price")
    high_price: Optional[Decimal] = Field(None, ge=0, description="High price")
    low_price: Optional[Decimal] = Field(None, ge=0, description="Low price")
    close_price: Decimal = Field(..., ge=0, description="Closing price")
    volume: Optional[int] = Field(None, ge=0, description="Trading volume")
    date: datetime = Field(..., description="Price date")
    
    @validator('high_price')
    def validate_high_price(cls, v, values):
        if v is not None and 'low_price' in values and values['low_price'] is not None:
            if v < values['low_price']:
                raise ValueError('High price cannot be less than low price')
        return v
    
    @validator('close_price')
    def validate_close_price(cls, v, values):
        if 'high_price' in values and values['high_price'] is not None:
            if v > values['high_price']:
                raise ValueError('Close price cannot be higher than high price')
        if 'low_price' in values and values['low_price'] is not None:
            if v < values['low_price']:
                raise ValueError('Close price cannot be lower than low price')
        return v


class CompanyInfo(BaseModel):
    """Validated company information model"""
    name: str = Field(..., min_length=1, max_length=200, description="Company name")
    symbol: str = Field(..., description="Stock symbol")
    sector: Optional[str] = Field(None, max_length=100, description="Business sector")
    industry: Optional[str] = Field(None, max_length=100, description="Industry")
    market_cap: Optional[int] = Field(None, ge=0, description="Market capitalization")
    pe_ratio: Optional[Decimal] = Field(None, ge=0, description="P/E ratio")
    dividend_yield: Optional[Decimal] = Field(None, ge=0, le=1, description="Dividend yield")
    beta: Optional[Decimal] = Field(None, description="Beta coefficient")
    description: Optional[str] = Field(None, max_length=5000, description="Company description")
    website: Optional[str] = Field(None, description="Company website")
    employees: Optional[int] = Field(None, ge=0, description="Number of employees")
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    @validator('website')
    def validate_website(cls, v):
        if v and not re.match(r'^https?:\/\/.+', v):
            raise ValueError('Website must be a valid URL starting with http:// or https://')
        return v


class TechnicalIndicatorRequest(BaseModel):
    """Request model for technical indicators"""
    symbol: StockSymbol
    indicator: str = Field(..., description="Technical indicator name")
    period: int = Field(14, ge=1, le=200, description="Calculation period")
    
    @validator('indicator')
    def validate_indicator(cls, v):
        valid_indicators = [
            'SMA', 'EMA', 'RSI', 'MACD', 'BBANDS', 'STOCH', 
            'ADX', 'AROON', 'ATR', 'WILLIAMS_R', 'ROC', 'MOMENTUM'
        ]
        if v.upper() not in valid_indicators:
            raise ValueError(f'Indicator must be one of: {", ".join(valid_indicators)}')
        return v.upper()


class PortfolioHolding(BaseModel):
    """Portfolio holding model with validation"""
    symbol: StockSymbol
    shares: Decimal = Field(..., gt=0, description="Number of shares")
    purchase_price: Decimal = Field(..., gt=0, description="Purchase price per share")
    purchase_date: date = Field(..., description="Purchase date")
    currency: str = Field("AUD", regex=r'^[A-Z]{3}$', description="Currency code")
    
    @validator('purchase_date')
    def validate_purchase_date(cls, v):
        if v > date.today():
            raise ValueError('Purchase date cannot be in the future')
        return v


class AlertConfig(BaseModel):
    """Alert configuration with validation"""
    symbol: StockSymbol
    alert_type: str = Field(..., description="Type of alert")
    threshold_value: Decimal = Field(..., description="Alert threshold")
    email_address: Optional[str] = Field(None, description="Email for notifications")
    is_active: bool = Field(True, description="Whether alert is active")
    
    @validator('alert_type')
    def validate_alert_type(cls, v):
        valid_types = ['PRICE_ABOVE', 'PRICE_BELOW', 'VOLUME_SPIKE', 'NEWS_SENTIMENT']
        if v.upper() not in valid_types:
            raise ValueError(f'Alert type must be one of: {", ".join(valid_types)}')
        return v.upper()
    
    @validator('email_address')
    def validate_email(cls, v):
        if v and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email address format')
        return v


class APICredentials(BaseModel):
    """API credentials with validation"""
    service_name: str = Field(..., description="API service name")
    api_key: str = Field(..., min_length=8, description="API key")
    is_active: bool = Field(True, description="Whether credentials are active")
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    @validator('service_name')
    def validate_service_name(cls, v):
        valid_services = ['ALPHA_VANTAGE', 'FINNHUB', 'NEWS_API', 'POLYGON']
        if v.upper() not in valid_services:
            raise ValueError(f'Service must be one of: {", ".join(valid_services)}')
        return v.upper()
    
    @validator('api_key')
    def validate_api_key(cls, v):
        # Remove any whitespace and validate format
        cleaned = v.strip()
        if not re.match(r'^[A-Za-z0-9_\-]+$', cleaned):
            raise ValueError('API key contains invalid characters')
        return cleaned


class NewsRequest(BaseModel):
    """News request with validation"""
    query: str = Field(..., min_length=1, max_length=100, description="Search query")
    page_size: int = Field(20, ge=1, le=100, description="Number of articles")
    language: str = Field("en", regex=r'^[a-z]{2}$', description="Language code")
    sort_by: str = Field("publishedAt", description="Sort criteria")
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        valid_sorts = ['relevancy', 'popularity', 'publishedAt']
        if v not in valid_sorts:
            raise ValueError(f'Sort by must be one of: {", ".join(valid_sorts)}')
        return v


class DatabaseConfig(BaseModel):
    """Database configuration with validation"""
    database_url: str = Field(..., description="Database connection URL")
    pool_size: int = Field(5, ge=1, le=50, description="Connection pool size")
    max_overflow: int = Field(10, ge=0, le=100, description="Max pool overflow")
    echo: bool = Field(False, description="Enable SQL logging")
    
    @validator('database_url')
    def validate_database_url(cls, v):
        # Basic validation for database URL format
        if not re.match(r'^(sqlite|postgresql|mysql):\/\/', v):
            raise ValueError('Database URL must start with sqlite://, postgresql://, or mysql://')
        return v


class CacheConfig(BaseModel):
    """Cache configuration with validation"""
    redis_url: str = Field(..., description="Redis connection URL")
    default_ttl: int = Field(1800, ge=60, le=86400, description="Default TTL in seconds")
    max_connections: int = Field(10, ge=1, le=100, description="Max Redis connections")
    
    @validator('redis_url')
    def validate_redis_url(cls, v):
        if not re.match(r'^redis:\/\/', v):
            raise ValueError('Redis URL must start with redis://')
        return v


class AnalysisRequest(BaseModel):
    """Analysis request with comprehensive validation"""
    symbol: StockSymbol
    period: TimePerod = TimePerod.ONE_YEAR
    include_technical: bool = Field(True, description="Include technical analysis")
    include_fundamental: bool = Field(True, description="Include fundamental analysis")
    include_news: bool = Field(False, description="Include news analysis")
    include_predictions: bool = Field(False, description="Include price predictions")
    
    class Config:
        use_enum_values = True


# Sanitization utilities
class DataSanitizer:
    """Data sanitization utilities"""
    
    @staticmethod
    def sanitize_sql_input(input_str: str) -> str:
        """Sanitize input to prevent SQL injection"""
        if not isinstance(input_str, str):
            return str(input_str)
        
        # Remove or escape dangerous characters
        dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_']
        sanitized = input_str
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized.strip()
    
    @staticmethod
    def sanitize_file_path(path: str) -> str:
        """Sanitize file path to prevent directory traversal"""
        if not isinstance(path, str):
            return str(path)
        
        # Remove dangerous path components
        dangerous_patterns = ['../', '..\\', '../', '.\\', '~/', '/etc/', '/var/']
        sanitized = path
        
        for pattern in dangerous_patterns:
            sanitized = sanitized.replace(pattern, '')
        
        # Only allow alphanumeric, dots, dashes, underscores, and forward slashes
        sanitized = re.sub(r'[^a-zA-Z0-9.\-_/]', '', sanitized)
        
        return sanitized.strip('/')
    
    @staticmethod
    def validate_json_input(data: Any, max_depth: int = 10) -> bool:
        """Validate JSON input to prevent nested attacks"""
        def check_depth(obj, depth=0):
            if depth > max_depth:
                return False
            
            if isinstance(obj, dict):
                for value in obj.values():
                    if not check_depth(value, depth + 1):
                        return False
            elif isinstance(obj, list):
                for item in obj:
                    if not check_depth(item, depth + 1):
                        return False
            
            return True
        
        return check_depth(data)


# Input validation decorators
def validate_input(**field_validators):
    """Decorator to validate function inputs"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Validate each specified field
            for field_name, validator_class in field_validators.items():
                if field_name in kwargs:
                    try:
                        # Validate using Pydantic model
                        if hasattr(validator_class, 'model_validate'):
                            kwargs[field_name] = validator_class.model_validate(kwargs[field_name])
                        else:
                            kwargs[field_name] = validator_class(**kwargs[field_name])
                    except Exception as e:
                        raise ValueError(f"Validation failed for {field_name}: {str(e)}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator