"""
Database models and schema for AFI Stock Tracker
"""

from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timezone
import os

Base = declarative_base()

class StockPrice(Base):
    """Historical stock price data"""
    __tablename__ = 'stock_prices'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    open_price = Column(Float, nullable=True)
    high_price = Column(Float, nullable=True)
    low_price = Column(Float, nullable=True)
    close_price = Column(Float, nullable=False)
    adjusted_close = Column(Float, nullable=True)
    volume = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Dividend(Base):
    """Dividend payment history"""
    __tablename__ = 'dividends'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)
    ex_date = Column(DateTime, nullable=False)
    payment_date = Column(DateTime, nullable=True)
    record_date = Column(DateTime, nullable=True)
    amount = Column(Float, nullable=False)
    dividend_type = Column(String(20), default='regular')  # regular, special, interim, final
    franking_percentage = Column(Float, nullable=True)  # For Australian dividends
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class CompanyInfo(Base):
    """Company fundamental information"""
    __tablename__ = 'company_info'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, unique=True)
    name = Column(String(200), nullable=False)
    sector = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    market_cap = Column(Float, nullable=True)
    enterprise_value = Column(Float, nullable=True)
    pe_ratio = Column(Float, nullable=True)
    pb_ratio = Column(Float, nullable=True)
    dividend_yield = Column(Float, nullable=True)
    payout_ratio = Column(Float, nullable=True)
    beta = Column(Float, nullable=True)
    shares_outstanding = Column(Float, nullable=True)
    float_shares = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    website = Column(String(200), nullable=True)
    employees = Column(Integer, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class TechnicalIndicator(Base):
    """Technical indicator values"""
    __tablename__ = 'technical_indicators'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    indicator_name = Column(String(50), nullable=False)  # SMA_20, RSI, MACD, etc.
    value = Column(Float, nullable=False)
    parameter1 = Column(Float, nullable=True)  # Period, etc.
    parameter2 = Column(Float, nullable=True)  # Additional parameters
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class NewsArticle(Base):
    """News articles and sentiment analysis"""
    __tablename__ = 'news_articles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(1000), nullable=False, unique=True)
    source = Column(String(100), nullable=True)
    published_date = Column(DateTime, nullable=False)
    sentiment_compound = Column(Float, nullable=True)
    sentiment_positive = Column(Float, nullable=True)
    sentiment_negative = Column(Float, nullable=True)
    sentiment_neutral = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Portfolio(Base):
    """User portfolio holdings"""
    __tablename__ = 'portfolio'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False)
    shares = Column(Float, nullable=False)
    purchase_price = Column(Float, nullable=False)
    purchase_date = Column(DateTime, nullable=False)
    purchase_fees = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Transaction(Base):
    """Portfolio transaction history"""
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey('portfolio.id'), nullable=False)
    transaction_type = Column(String(20), nullable=False)  # buy, sell, dividend
    shares = Column(Float, nullable=True)  # For buy/sell
    price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)  # Total transaction amount
    fees = Column(Float, default=0.0)
    transaction_date = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    portfolio = relationship("Portfolio", backref="transactions")

class Alert(Base):
    """Price and news alerts"""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False)
    alert_type = Column(String(50), nullable=False)  # price_above, price_below, volume_spike, news_sentiment
    threshold_value = Column(Float, nullable=False)
    comparison_operator = Column(String(10), nullable=False)  # >, <, =, !=
    is_active = Column(Boolean, default=True)
    triggered_count = Column(Integer, default=0)
    last_triggered = Column(DateTime, nullable=True)
    notification_method = Column(String(50), default='email')  # email, push, sms
    created_at = Column(DateTime, default=datetime.utcnow)

class CacheEntry(Base):
    """Cache for API responses"""
    __tablename__ = 'cache'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String(200), nullable=False, unique=True)
    data = Column(Text, nullable=False)  # JSON serialized data
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)