"""
Database manager for AFI Stock Tracker
Handles database connections, operations, and data management
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy import create_engine, desc, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd

from .models import Base, StockPrice, Dividend, CompanyInfo, TechnicalIndicator, NewsArticle, Portfolio, Transaction, Alert, CacheEntry

class DatabaseManager:
    """Database operations manager"""
    
    def __init__(self, db_path: str = "data/afi_tracker.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create database engine
        self.engine = create_engine(f'sqlite:///{self.db_path}', echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        
        self.logger = logging.getLogger(__name__)
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    # Stock Price Operations
    def save_stock_prices(self, symbol: str, price_data: pd.DataFrame) -> int:
        """Save stock price data to database"""
        session = self.get_session()
        saved_count = 0
        
        try:
            for date, row in price_data.iterrows():
                # Check if record already exists
                existing = session.query(StockPrice).filter(
                    and_(StockPrice.symbol == symbol, StockPrice.date == date)
                ).first()
                
                if not existing:
                    stock_price = StockPrice(
                        symbol=symbol,
                        date=date,
                        open_price=row.get('Open'),
                        high_price=row.get('High'),
                        low_price=row.get('Low'),
                        close_price=row.get('Close'),
                        adjusted_close=row.get('Adj Close'),
                        volume=row.get('Volume')
                    )
                    session.add(stock_price)
                    saved_count += 1
            
            session.commit()
            self.logger.info(f"Saved {saved_count} new price records for {symbol}")
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Failed to save stock prices: {e}")
        finally:
            session.close()
        
        return saved_count
    
    def get_stock_prices(self, symbol: str, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
        """Get stock price data from database"""
        session = self.get_session()
        
        try:
            query = session.query(StockPrice).filter(StockPrice.symbol == symbol)
            
            if start_date:
                query = query.filter(StockPrice.date >= start_date)
            if end_date:
                query = query.filter(StockPrice.date <= end_date)
            
            query = query.order_by(StockPrice.date)
            prices = query.all()
            
            # Convert to DataFrame
            data = []
            for price in prices:
                data.append({
                    'Date': price.date,
                    'Open': price.open_price,
                    'High': price.high_price,
                    'Low': price.low_price,
                    'Close': price.close_price,
                    'Adj Close': price.adjusted_close,
                    'Volume': price.volume
                })
            
            df = pd.DataFrame(data)
            if not df.empty:
                df.set_index('Date', inplace=True)
            
            return df
            
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to get stock prices: {e}")
            return pd.DataFrame()
        finally:
            session.close()
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get the most recent closing price"""
        session = self.get_session()
        
        try:
            latest = session.query(StockPrice).filter(StockPrice.symbol == symbol).order_by(desc(StockPrice.date)).first()
            return latest.close_price if latest else None
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to get latest price: {e}")
            return None
        finally:
            session.close()
    
    # Dividend Operations
    def save_dividends(self, symbol: str, dividend_data: pd.DataFrame) -> int:
        """Save dividend data to database"""
        session = self.get_session()
        saved_count = 0
        
        try:
            for date, amount in dividend_data.items():
                # Check if record already exists
                existing = session.query(Dividend).filter(
                    and_(Dividend.symbol == symbol, Dividend.ex_date == date)
                ).first()
                
                if not existing:
                    dividend = Dividend(
                        symbol=symbol,
                        ex_date=date,
                        amount=amount,
                        dividend_type='regular'
                    )
                    session.add(dividend)
                    saved_count += 1
            
            session.commit()
            self.logger.info(f"Saved {saved_count} new dividend records for {symbol}")
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Failed to save dividends: {e}")
        finally:
            session.close()
        
        return saved_count
    
    def get_dividends(self, symbol: str, start_date: datetime = None) -> pd.DataFrame:
        """Get dividend data from database"""
        session = self.get_session()
        
        try:
            query = session.query(Dividend).filter(Dividend.symbol == symbol)
            
            if start_date:
                query = query.filter(Dividend.ex_date >= start_date)
            
            query = query.order_by(Dividend.ex_date)
            dividends = query.all()
            
            data = []
            for div in dividends:
                data.append({
                    'Date': div.ex_date,
                    'Amount': div.amount,
                    'Type': div.dividend_type,
                    'Franking': div.franking_percentage
                })
            
            return pd.DataFrame(data)
            
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to get dividends: {e}")
            return pd.DataFrame()
        finally:
            session.close()
    
    # Company Info Operations
    def save_company_info(self, symbol: str, company_data: Dict[str, Any]) -> bool:
        """Save or update company information"""
        session = self.get_session()
        
        try:
            # Check if record exists
            existing = session.query(CompanyInfo).filter(CompanyInfo.symbol == symbol).first()
            
            if existing:
                # Update existing record
                for key, value in company_data.items():
                    if hasattr(existing, key) and value is not None:
                        setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
            else:
                # Create new record
                company_info = CompanyInfo(symbol=symbol, **company_data)
                session.add(company_info)
            
            session.commit()
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Failed to save company info: {e}")
            return False
        finally:
            session.close()
    
    def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get company information"""
        session = self.get_session()
        
        try:
            company = session.query(CompanyInfo).filter(CompanyInfo.symbol == symbol).first()
            if company:
                return {
                    'name': company.name,
                    'sector': company.sector,
                    'industry': company.industry,
                    'market_cap': company.market_cap,
                    'pe_ratio': company.pe_ratio,
                    'pb_ratio': company.pb_ratio,
                    'dividend_yield': company.dividend_yield,
                    'payout_ratio': company.payout_ratio,
                    'beta': company.beta,
                    'shares_outstanding': company.shares_outstanding,
                    'description': company.description,
                    'website': company.website,
                    'employees': company.employees,
                    'updated_at': company.updated_at
                }
            return None
            
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to get company info: {e}")
            return None
        finally:
            session.close()
    
    # Technical Indicators Operations
    def save_technical_indicators(self, symbol: str, indicators: Dict[str, pd.DataFrame]) -> int:
        """Save technical indicator data"""
        session = self.get_session()
        saved_count = 0
        
        try:
            for indicator_name, data in indicators.items():
                for date, value in data.items():
                    if isinstance(value, pd.Series):
                        # Handle multi-column indicators like MACD
                        for col_name, col_value in value.items():
                            full_name = f"{indicator_name}_{col_name}"
                            existing = session.query(TechnicalIndicator).filter(
                                and_(
                                    TechnicalIndicator.symbol == symbol,
                                    TechnicalIndicator.date == date,
                                    TechnicalIndicator.indicator_name == full_name
                                )
                            ).first()
                            
                            if not existing:
                                indicator = TechnicalIndicator(
                                    symbol=symbol,
                                    date=date,
                                    indicator_name=full_name,
                                    value=float(col_value)
                                )
                                session.add(indicator)
                                saved_count += 1
                    else:
                        # Single value indicator
                        existing = session.query(TechnicalIndicator).filter(
                            and_(
                                TechnicalIndicator.symbol == symbol,
                                TechnicalIndicator.date == date,
                                TechnicalIndicator.indicator_name == indicator_name
                            )
                        ).first()
                        
                        if not existing:
                            indicator = TechnicalIndicator(
                                symbol=symbol,
                                date=date,
                                indicator_name=indicator_name,
                                value=float(value)
                            )
                            session.add(indicator)
                            saved_count += 1
            
            session.commit()
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Failed to save technical indicators: {e}")
        finally:
            session.close()
        
        return saved_count
    
    # News Operations
    def save_news_articles(self, articles: List[Dict[str, Any]]) -> int:
        """Save news articles with sentiment analysis"""
        session = self.get_session()
        saved_count = 0
        
        try:
            for article_data in articles:
                # Check if article already exists (by URL)
                existing = session.query(NewsArticle).filter(NewsArticle.url == article_data['url']).first()
                
                if not existing:
                    sentiment = article_data.get('sentiment', {})
                    article = NewsArticle(
                        symbol=article_data.get('symbol', 'AFI'),
                        title=article_data['title'],
                        description=article_data.get('description', ''),
                        url=article_data['url'],
                        source=article_data.get('source', ''),
                        published_date=article_data['published_date'],
                        sentiment_compound=sentiment.get('compound'),
                        sentiment_positive=sentiment.get('positive'),
                        sentiment_negative=sentiment.get('negative'),
                        sentiment_neutral=sentiment.get('neutral')
                    )
                    session.add(article)
                    saved_count += 1
            
            session.commit()
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Failed to save news articles: {e}")
        finally:
            session.close()
        
        return saved_count
    
    def get_recent_news(self, symbol: str, days: int = 7, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent news articles"""
        session = self.get_session()
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            articles = session.query(NewsArticle).filter(
                and_(
                    NewsArticle.symbol == symbol,
                    NewsArticle.published_date >= cutoff_date
                )
            ).order_by(desc(NewsArticle.published_date)).limit(limit).all()
            
            return [{
                'title': article.title,
                'description': article.description,
                'url': article.url,
                'source': article.source,
                'published_date': article.published_date,
                'sentiment': {
                    'compound': article.sentiment_compound,
                    'positive': article.sentiment_positive,
                    'negative': article.sentiment_negative,
                    'neutral': article.sentiment_neutral
                }
            } for article in articles]
            
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to get recent news: {e}")
            return []
        finally:
            session.close()
    
    # Portfolio Operations
    def add_portfolio_holding(self, symbol: str, shares: float, purchase_price: float, purchase_date: datetime, **kwargs) -> bool:
        """Add new portfolio holding"""
        session = self.get_session()
        
        try:
            holding = Portfolio(
                symbol=symbol,
                shares=shares,
                purchase_price=purchase_price,
                purchase_date=purchase_date,
                purchase_fees=kwargs.get('fees', 0.0),
                notes=kwargs.get('notes', '')
            )
            session.add(holding)
            session.commit()
            
            # Add transaction record
            transaction = Transaction(
                portfolio_id=holding.id,
                transaction_type='buy',
                shares=shares,
                price=purchase_price,
                amount=shares * purchase_price + kwargs.get('fees', 0.0),
                fees=kwargs.get('fees', 0.0),
                transaction_date=purchase_date,
                notes=kwargs.get('notes', '')
            )
            session.add(transaction)
            session.commit()
            
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Failed to add portfolio holding: {e}")
            return False
        finally:
            session.close()
    
    def get_portfolio_holdings(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Get portfolio holdings"""
        session = self.get_session()
        
        try:
            query = session.query(Portfolio).filter(Portfolio.is_active == True)
            
            if symbol:
                query = query.filter(Portfolio.symbol == symbol)
            
            holdings = query.all()
            
            return [{
                'id': holding.id,
                'symbol': holding.symbol,
                'shares': holding.shares,
                'purchase_price': holding.purchase_price,
                'purchase_date': holding.purchase_date,
                'purchase_fees': holding.purchase_fees,
                'notes': holding.notes
            } for holding in holdings]
            
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to get portfolio holdings: {e}")
            return []
        finally:
            session.close()
    
    # Cache Operations
    def get_cached_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached data if not expired"""
        session = self.get_session()
        
        try:
            cache_entry = session.query(CacheEntry).filter(CacheEntry.cache_key == cache_key).first()
            
            if cache_entry and cache_entry.expires_at > datetime.utcnow():
                return json.loads(cache_entry.data)
            elif cache_entry:
                # Remove expired entry
                session.delete(cache_entry)
                session.commit()
            
            return None
            
        except (SQLAlchemyError, json.JSONDecodeError) as e:
            self.logger.error(f"Failed to get cached data: {e}")
            return None
        finally:
            session.close()
    
    def set_cached_data(self, cache_key: str, data: Dict[str, Any], expires_in_hours: int = 1) -> bool:
        """Cache data with expiration"""
        session = self.get_session()
        
        try:
            expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
            
            # Remove existing entry
            existing = session.query(CacheEntry).filter(CacheEntry.cache_key == cache_key).first()
            if existing:
                session.delete(existing)
            
            # Add new entry
            cache_entry = CacheEntry(
                cache_key=cache_key,
                data=json.dumps(data, default=str),
                expires_at=expires_at
            )
            session.add(cache_entry)
            session.commit()
            
            return True
            
        except (SQLAlchemyError, TypeError) as e:
            session.rollback()
            self.logger.error(f"Failed to set cached data: {e}")
            return False
        finally:
            session.close()
    
    def save_stock_data(self, symbol: str, price_data: pd.DataFrame) -> bool:
        """Save stock data (compatibility method for advanced tracker)"""
        try:
            if price_data is not None and not price_data.empty:
                saved_count = self.save_stock_prices(symbol, price_data)
                return saved_count > 0
            return False
        except Exception as e:
            self.logger.error(f"Failed to save stock data: {e}")
            return False