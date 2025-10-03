"""
Yahoo Finance API client - Primary data source for AFI stock data
Provides real-time quotes, historical data, and financial information
"""

import yfinance as yf
import pandas as pd
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from .base_client import BaseAPIClient

class YahooFinanceClient(BaseAPIClient):
    """Yahoo Finance API client for stock data"""
    
    def __init__(self):
        # Yahoo Finance doesn't require API key
        super().__init__(api_key="", base_url="", rate_limit=0.1)
        self.symbol = "AFI.AX"  # Australian Foundation Investment Company
    
    def get_current_price(self, symbol: str = None) -> Optional[float]:
        """Get current stock price"""
        try:
            ticker = yf.Ticker(symbol or self.symbol)
            info = ticker.info
            return info.get('currentPrice') or info.get('regularMarketPrice')
        except Exception as e:
            self.logger.error(f"Failed to get current price: {e}")
            return None
    
    def get_historical_data(self, symbol: str = None, period: str = "1y") -> Optional[pd.DataFrame]:
        """Get historical price data"""
        try:
            ticker = yf.Ticker(symbol or self.symbol)
            return ticker.history(period=period)
        except Exception as e:
            self.logger.error(f"Failed to get historical data: {e}")
            return None
    
    def get_company_info(self, symbol: str = None) -> Optional[Dict[str, Any]]:
        """Get comprehensive company information"""
        try:
            ticker = yf.Ticker(symbol or self.symbol)
            info = ticker.info
            
            return {
                'name': info.get('longName', 'Australian Foundation Investment Company'),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'market_cap': info.get('marketCap'),
                'enterprise_value': info.get('enterpriseValue'),
                'pe_ratio': info.get('forwardPE'),
                'pb_ratio': info.get('priceToBook'),
                'dividend_yield': info.get('dividendYield'),
                'payout_ratio': info.get('payoutRatio'),
                'beta': info.get('beta'),
                '52_week_high': info.get('fiftyTwoWeekHigh'),
                '52_week_low': info.get('fiftyTwoWeekLow'),
                'avg_volume': info.get('averageVolume'),
                'shares_outstanding': info.get('sharesOutstanding'),
                'float_shares': info.get('floatShares'),
                'description': info.get('longBusinessSummary'),
                'website': info.get('website'),
                'employees': info.get('fullTimeEmployees')
            }
        except Exception as e:
            self.logger.error(f"Failed to get company info: {e}")
            return None
    
    def get_dividend_history(self, symbol: str = None, period: str = "2y") -> Optional[pd.DataFrame]:
        """Get dividend payment history"""
        try:
            ticker = yf.Ticker(symbol or self.symbol)
            dividends = ticker.dividends
            
            if not dividends.empty:
                # Convert dividend index to timezone-naive if needed
                if dividends.index.tz is not None:
                    dividends.index = dividends.index.tz_convert('UTC').tz_localize(None)
                
                # Filter by period
                end_date = datetime.now()
                if period == "1y":
                    start_date = end_date - timedelta(days=365)
                elif period == "2y":
                    start_date = end_date - timedelta(days=730)
                elif period == "5y":
                    start_date = end_date - timedelta(days=1825)
                else:
                    start_date = dividends.index.min()
                
                # Ensure start_date is timezone-naive for comparison
                if hasattr(start_date, 'tz') and start_date.tz is not None:
                    start_date = start_date.tz_localize(None)
                
                filtered_dividends = dividends[dividends.index >= start_date]
                return filtered_dividends.to_frame('dividend')
            
            return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Failed to get dividend history: {e}")
            return pd.DataFrame()
    
    def get_financial_statements(self, symbol: str = None) -> Optional[Dict[str, pd.DataFrame]]:
        """Get financial statements (income, balance sheet, cash flow)"""
        try:
            ticker = yf.Ticker(symbol or self.symbol)
            
            return {
                'income_statement': ticker.financials,
                'balance_sheet': ticker.balance_sheet,
                'cash_flow': ticker.cashflow,
                'quarterly_income': ticker.quarterly_financials,
                'quarterly_balance': ticker.quarterly_balance_sheet,
                'quarterly_cashflow': ticker.quarterly_cashflow
            }
        except Exception as e:
            self.logger.error(f"Failed to get financial statements: {e}")
            return None
    
    def get_analyst_recommendations(self, symbol: str = None) -> Optional[pd.DataFrame]:
        """Get analyst recommendations and price targets"""
        try:
            ticker = yf.Ticker(symbol or self.symbol)
            recommendations = ticker.recommendations
            
            if recommendations is not None and not recommendations.empty:
                return recommendations
            
            return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Failed to get analyst recommendations: {e}")
            return None
    
    def get_options_data(self, symbol: str = None) -> Optional[Dict[str, Any]]:
        """Get options data if available"""
        try:
            ticker = yf.Ticker(symbol or self.symbol)
            
            # Get available expiration dates
            expiration_dates = ticker.options
            
            if not expiration_dates:
                return None
            
            # Get options for the nearest expiration
            nearest_expiry = expiration_dates[0]
            options_chain = ticker.option_chain(nearest_expiry)
            
            return {
                'expiration_dates': expiration_dates,
                'calls': options_chain.calls,
                'puts': options_chain.puts,
                'nearest_expiry': nearest_expiry
            }
        except Exception as e:
            self.logger.error(f"Failed to get options data: {e}")
            return None
    
    def get_institutional_holders(self, symbol: str = None) -> Optional[pd.DataFrame]:
        """Get institutional holders information"""
        try:
            ticker = yf.Ticker(symbol or self.symbol)
            return ticker.institutional_holders
        except Exception as e:
            self.logger.error(f"Failed to get institutional holders: {e}")
            return None
    
    def get_major_holders(self, symbol: str = None) -> Optional[pd.DataFrame]:
        """Get major holders breakdown"""
        try:
            ticker = yf.Ticker(symbol or self.symbol)
            return ticker.major_holders
        except Exception as e:
            self.logger.error(f"Failed to get major holders: {e}")
            return None
    
    def get_insider_transactions(self, symbol: str = None) -> Optional[pd.DataFrame]:
        """Get insider trading transactions"""
        try:
            ticker = yf.Ticker(symbol or self.symbol)
            return ticker.insider_transactions
        except Exception as e:
            self.logger.error(f"Failed to get insider transactions: {e}")
            return None
    
    def get_calendar_events(self, symbol: str = None) -> Optional[Dict[str, Any]]:
        """Get upcoming calendar events (earnings, dividends)"""
        try:
            ticker = yf.Ticker(symbol or self.symbol)
            calendar = ticker.calendar
            
            if calendar is not None and not calendar.empty:
                return {
                    'earnings_date': calendar.index.tolist(),
                    'earnings_estimate': calendar.to_dict()
                }
            
            return None
        except Exception as e:
            self.logger.error(f"Failed to get calendar events: {e}")
            return None