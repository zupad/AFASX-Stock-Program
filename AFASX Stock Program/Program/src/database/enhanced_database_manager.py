"""
Enhanced database manager with connection pooling, async support, and optimizations
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List, Union, AsyncGenerator
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import asynccontextmanager, contextmanager

from sqlalchemy import create_engine, desc, and_, or_, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import pandas as pd

from .models import Base, StockPrice, Dividend, CompanyInfo, TechnicalIndicator, NewsArticle, Portfolio, Transaction, Alert, CacheEntry
from ..validation.models import StockSymbol, PriceData


class EnhancedDatabaseManager:
    """Enhanced database operations manager with connection pooling and async support"""
    
    def __init__(self, 
                 db_url: str = "sqlite:///data/afi_tracker.db",
                 async_db_url: Optional[str] = None,
                 pool_size: int = 5,
                 max_overflow: int = 10,
                 echo: bool = False):
        
        self.db_url = db_url
        self.async_db_url = async_db_url or db_url.replace('sqlite://', 'sqlite+aiosqlite://')
        self.logger = logging.getLogger(__name__)
        
        # Create database directory if needed
        if db_url.startswith('sqlite:'):
            db_path = Path(db_url.replace('sqlite:///', ''))
            db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure connection pooling based on database type
        if 'sqlite' in db_url:
            # SQLite specific configuration
            engine_kwargs = {
                'poolclass': StaticPool,
                'connect_args': {
                    'check_same_thread': False,
                    'timeout': 30
                },
                'echo': echo
            }
        else:
            # PostgreSQL/MySQL configuration
            engine_kwargs = {
                'poolclass': QueuePool,
                'pool_size': pool_size,
                'max_overflow': max_overflow,
                'pool_pre_ping': True,
                'pool_recycle': 3600,
                'echo': echo
            }
        
        # Create sync engine
        self.engine = create_engine(db_url, **engine_kwargs)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create async engine
        async_engine_kwargs = engine_kwargs.copy()
        if 'connect_args' in async_engine_kwargs:
            async_engine_kwargs['connect_args'].pop('check_same_thread', None)
        
        self.async_engine = create_async_engine(self.async_db_url, **async_engine_kwargs)
        self.AsyncSessionLocal = async_sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=self.async_engine,
            class_=AsyncSession
        )
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        
        self.logger.info(f"Database manager initialized with URL: {db_url}")
    
    @contextmanager
    def get_session(self):
        """Get database session with proper cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session with proper cleanup"""
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    # Enhanced Stock Price Operations
    def save_stock_prices_bulk(self, symbol: str, price_data: pd.DataFrame, batch_size: int = 1000) -> int:
        """Save stock price data in batches for better performance"""
        with self.get_session() as session:
            saved_count = 0
            
            try:
                # Prepare data for bulk insert
                price_objects = []
                for date, row in price_data.iterrows():
                    # Check if record already exists (using a single query for batch)
                    existing_dates = session.query(StockPrice.date).filter(
                        and_(StockPrice.symbol == symbol, 
                             StockPrice.date >= date - timedelta(days=1),
                             StockPrice.date <= date + timedelta(days=1))
                    ).all()
                    
                    existing_dates_set = {d[0].date() for d in existing_dates}
                    
                    if date.date() not in existing_dates_set:
                        stock_price = StockPrice(
                            symbol=symbol,
                            date=date,
                            open_price=row.get('Open'),
                            high_price=row.get('High'),
                            low_price=row.get('Low'),
                            close_price=row.get('Close'),
                            adjusted_close=row.get('Adj Close'),
                            volume=int(row.get('Volume', 0)) if pd.notna(row.get('Volume')) else None
                        )
                        price_objects.append(stock_price)
                        saved_count += 1
                        
                        # Batch commit
                        if len(price_objects) >= batch_size:
                            session.bulk_save_objects(price_objects)
                            session.commit()
                            price_objects = []
                
                # Save remaining objects
                if price_objects:
                    session.bulk_save_objects(price_objects)
                    session.commit()
                
                self.logger.info(f"Bulk saved {saved_count} new price records for {symbol}")
                
            except SQLAlchemyError as e:
                session.rollback()
                self.logger.error(f"Failed to bulk save stock prices: {e}")
                raise
        
        return saved_count
    
    async def save_stock_prices_async(self, symbol: str, price_data: pd.DataFrame) -> int:
        """Save stock price data asynchronously"""
        async with self.get_async_session() as session:
            saved_count = 0
            
            try:
                for date, row in price_data.iterrows():
                    # Check if record already exists
                    result = await session.execute(
                        text("SELECT id FROM stock_prices WHERE symbol = :symbol AND date = :date"),
                        {"symbol": symbol, "date": date}
                    )
                    
                    if not result.fetchone():
                        stock_price = StockPrice(
                            symbol=symbol,
                            date=date,
                            open_price=row.get('Open'),
                            high_price=row.get('High'),
                            low_price=row.get('Low'),
                            close_price=row.get('Close'),
                            adjusted_close=row.get('Adj Close'),
                            volume=int(row.get('Volume', 0)) if pd.notna(row.get('Volume')) else None
                        )
                        session.add(stock_price)
                        saved_count += 1
                
                await session.commit()
                self.logger.info(f"Async saved {saved_count} new price records for {symbol}")
                
            except SQLAlchemyError as e:
                await session.rollback()
                self.logger.error(f"Failed to async save stock prices: {e}")
                raise
        
        return saved_count
    
    def get_stock_prices_optimized(self, symbol: str, 
                                 start_date: Optional[datetime] = None, 
                                 end_date: Optional[datetime] = None,
                                 limit: Optional[int] = None) -> pd.DataFrame:
        """Get stock price data with optimized query and pagination"""
        with self.get_session() as session:
            try:
                # Build optimized query
                query = session.query(StockPrice).filter(StockPrice.symbol == symbol)
                
                if start_date:
                    query = query.filter(StockPrice.date >= start_date)
                if end_date:
                    query = query.filter(StockPrice.date <= end_date)
                
                query = query.order_by(StockPrice.date.desc())
                
                if limit:
                    query = query.limit(limit)
                
                # Use SQL compilation for better performance
                prices = query.all()
                
                if not prices:
                    return pd.DataFrame()
                
                # Convert to DataFrame efficiently
                data = {
                    'Date': [p.date for p in prices],
                    'Open': [p.open_price for p in prices],
                    'High': [p.high_price for p in prices],
                    'Low': [p.low_price for p in prices],
                    'Close': [p.close_price for p in prices],
                    'Adj Close': [p.adjusted_close for p in prices],
                    'Volume': [p.volume for p in prices]
                }
                
                df = pd.DataFrame(data)
                df.set_index('Date', inplace=True)
                df.sort_index(inplace=True)
                
                return df
                
            except SQLAlchemyError as e:
                self.logger.error(f"Failed to get stock prices: {e}")
                return pd.DataFrame()
    
    # Portfolio Management
    def save_portfolio_holding(self, symbol: str, shares: float, purchase_price: float, 
                              purchase_date: datetime, currency: str = 'AUD') -> bool:
        """Save portfolio holding with validation"""
        with self.get_session() as session:
            try:
                # Validate input
                validated_symbol = StockSymbol(symbol=symbol)
                
                holding = Portfolio(
                    symbol=validated_symbol.symbol,
                    shares=shares,
                    purchase_price=purchase_price,
                    purchase_date=purchase_date,
                    currency=currency
                )
                
                session.add(holding)
                session.commit()
                
                self.logger.info(f"Saved portfolio holding: {shares} shares of {symbol}")
                return True
                
            except (SQLAlchemyError, ValueError) as e:
                session.rollback()
                self.logger.error(f"Failed to save portfolio holding: {e}")
                return False
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio summary with current values"""
        with self.get_session() as session:
            try:
                holdings = session.query(Portfolio).filter(Portfolio.is_active == True).all()
                
                summary = {
                    'total_holdings': len(holdings),
                    'symbols': [],
                    'total_cost': 0.0,
                    'holdings_detail': []
                }
                
                for holding in holdings:
                    # Get current price
                    latest_price = session.query(StockPrice).filter(
                        StockPrice.symbol == holding.symbol
                    ).order_by(StockPrice.date.desc()).first()
                    
                    current_price = latest_price.close_price if latest_price else holding.purchase_price
                    current_value = holding.shares * current_price
                    cost_basis = holding.shares * holding.purchase_price
                    gain_loss = current_value - cost_basis
                    gain_loss_pct = (gain_loss / cost_basis) * 100 if cost_basis > 0 else 0
                    
                    holding_detail = {
                        'symbol': holding.symbol,
                        'shares': holding.shares,
                        'purchase_price': holding.purchase_price,
                        'current_price': current_price,
                        'cost_basis': cost_basis,
                        'current_value': current_value,
                        'gain_loss': gain_loss,
                        'gain_loss_percent': gain_loss_pct,
                        'purchase_date': holding.purchase_date.isoformat()
                    }
                    
                    summary['holdings_detail'].append(holding_detail)
                    summary['symbols'].append(holding.symbol)
                    summary['total_cost'] += cost_basis
                
                return summary
                
            except SQLAlchemyError as e:
                self.logger.error(f"Failed to get portfolio summary: {e}")
                return {}
    
    # Advanced Analytics Queries
    def get_price_statistics(self, symbol: str, days: int = 252) -> Dict[str, float]:
        """Get advanced price statistics for a symbol"""
        with self.get_session() as session:
            try:
                # Get recent price data
                cutoff_date = datetime.now() - timedelta(days=days)
                prices = session.query(StockPrice.close_price, StockPrice.volume).filter(
                    and_(
                        StockPrice.symbol == symbol,
                        StockPrice.date >= cutoff_date
                    )
                ).order_by(StockPrice.date).all()
                
                if not prices:
                    return {}
                
                price_values = [p[0] for p in prices]
                volumes = [p[1] for p in prices if p[1] is not None]
                
                # Calculate statistics
                stats = {
                    'mean_price': sum(price_values) / len(price_values),
                    'min_price': min(price_values),
                    'max_price': max(price_values),
                    'price_volatility': pd.Series(price_values).std(),
                    'average_volume': sum(volumes) / len(volumes) if volumes else 0,
                    'data_points': len(price_values)
                }
                
                return stats
                
            except SQLAlchemyError as e:
                self.logger.error(f"Failed to get price statistics: {e}")
                return {}
    
    # Database Maintenance
    def cleanup_old_data(self, days_to_keep: int = 365) -> Dict[str, int]:
        """Clean up old data to maintain database performance"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cleanup_stats = {}
        
        with self.get_session() as session:
            try:
                # Clean old cache entries
                deleted_cache = session.query(CacheEntry).filter(
                    CacheEntry.expires_at < datetime.now()
                ).delete()
                
                # Clean old news articles (keep 6 months)
                news_cutoff = datetime.now() - timedelta(days=180)
                deleted_news = session.query(NewsArticle).filter(
                    NewsArticle.published_date < news_cutoff
                ).delete()
                
                # Clean old technical indicators (keep 2 years)
                tech_cutoff = datetime.now() - timedelta(days=730)
                deleted_tech = session.query(TechnicalIndicator).filter(
                    TechnicalIndicator.date < tech_cutoff
                ).delete()
                
                session.commit()
                
                cleanup_stats = {
                    'deleted_cache_entries': deleted_cache,
                    'deleted_news_articles': deleted_news,
                    'deleted_technical_indicators': deleted_tech
                }
                
                self.logger.info(f"Database cleanup completed: {cleanup_stats}")
                
            except SQLAlchemyError as e:
                session.rollback()
                self.logger.error(f"Database cleanup failed: {e}")
        
        return cleanup_stats
    
    def optimize_database(self) -> bool:
        """Optimize database performance"""
        try:
            with self.engine.connect() as connection:
                if 'sqlite' in self.db_url:
                    # SQLite optimizations
                    connection.execute(text("VACUUM"))
                    connection.execute(text("ANALYZE"))
                    connection.execute(text("PRAGMA optimize"))
                elif 'postgresql' in self.db_url:
                    # PostgreSQL optimizations
                    connection.execute(text("VACUUM ANALYZE"))
                    connection.execute(text("REINDEX DATABASE"))
                
                self.logger.info("Database optimization completed")
                return True
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database optimization failed: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics and health metrics"""
        stats = {}
        
        with self.get_session() as session:
            try:
                # Table row counts
                stats['stock_prices_count'] = session.query(StockPrice).count()
                stats['company_info_count'] = session.query(CompanyInfo).count()
                stats['dividends_count'] = session.query(Dividend).count()
                stats['portfolio_count'] = session.query(Portfolio).count()
                stats['news_articles_count'] = session.query(NewsArticle).count()
                stats['alerts_count'] = session.query(Alert).count()
                
                # Date ranges
                oldest_price = session.query(StockPrice.date).order_by(StockPrice.date).first()
                newest_price = session.query(StockPrice.date).order_by(StockPrice.date.desc()).first()
                
                if oldest_price and newest_price:
                    stats['price_data_range'] = {
                        'oldest': oldest_price[0].isoformat(),
                        'newest': newest_price[0].isoformat(),
                        'days_of_data': (newest_price[0] - oldest_price[0]).days
                    }
                
                # Database file size (for SQLite)
                if 'sqlite' in self.db_url:
                    db_path = self.db_url.replace('sqlite:///', '')
                    if os.path.exists(db_path):
                        stats['database_size_mb'] = os.path.getsize(db_path) / (1024 * 1024)
                
                return stats
                
            except SQLAlchemyError as e:
                self.logger.error(f"Failed to get database stats: {e}")
                return {}
    
    def close(self):
        """Close database connections"""
        self.engine.dispose()
        if hasattr(self, 'async_engine'):
            asyncio.create_task(self.async_engine.dispose())