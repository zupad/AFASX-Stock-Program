"""
Alpha Vantage API client for advanced financial data and technical indicators
"""

from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.techindicators import TechIndicators
from alpha_vantage.fundamentaldata import FundamentalData
import pandas as pd
from typing import Dict, Any, Optional
from .base_client import BaseAPIClient

class AlphaVantageClient(BaseAPIClient):
    """Alpha Vantage API client for financial data"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "https://www.alphavantage.co", rate_limit=12.0)  # 5 calls per minute
        self.ts = TimeSeries(key=api_key, output_format='pandas')
        self.ti = TechIndicators(key=api_key, output_format='pandas')
        self.fd = FundamentalData(key=api_key, output_format='pandas')
        self.symbol = "AFI.AX"
    
    def get_current_price(self, symbol: str = None) -> Optional[float]:
        """Get current price using intraday data"""
        try:
            data, _ = self.ts.get_intraday(symbol or self.symbol, interval='1min', outputsize='compact')
            if not data.empty:
                latest_price = data.iloc[0]['4. close']
                return float(latest_price)
        except Exception as e:
            self.logger.error(f"Failed to get current price from Alpha Vantage: {e}")
        return None
    
    def get_historical_data(self, symbol: str = None, period: str = "1y") -> Optional[pd.DataFrame]:
        """Get historical daily data"""
        try:
            if period in ["1d", "5d"]:
                data, _ = self.ts.get_intraday(symbol or self.symbol, interval='5min', outputsize='full')
            else:
                data, _ = self.ts.get_daily_adjusted(symbol or self.symbol, outputsize='full')
            
            if not data.empty:
                # Standardize column names
                data.columns = ['open', 'high', 'low', 'close', 'adjusted_close', 'volume', 'dividend', 'split']
                return data
        except Exception as e:
            self.logger.error(f"Failed to get historical data from Alpha Vantage: {e}")
        return None
    
    def get_technical_indicators(self, symbol: str = None, indicator: str = "SMA", **kwargs) -> Optional[pd.DataFrame]:
        """Get technical indicators"""
        try:
            symbol = symbol or self.symbol
            
            if indicator == "SMA":
                data, _ = self.ti.get_sma(symbol, interval='daily', time_period=kwargs.get('period', 20))
            elif indicator == "EMA":
                data, _ = self.ti.get_ema(symbol, interval='daily', time_period=kwargs.get('period', 20))
            elif indicator == "RSI":
                data, _ = self.ti.get_rsi(symbol, interval='daily', time_period=kwargs.get('period', 14))
            elif indicator == "MACD":
                data, _ = self.ti.get_macd(symbol, interval='daily')
            elif indicator == "BBANDS":
                data, _ = self.ti.get_bbands(symbol, interval='daily', time_period=kwargs.get('period', 20))
            elif indicator == "STOCH":
                data, _ = self.ti.get_stoch(symbol, interval='daily')
            elif indicator == "ADX":
                data, _ = self.ti.get_adx(symbol, interval='daily', time_period=kwargs.get('period', 14))
            elif indicator == "AROON":
                data, _ = self.ti.get_aroon(symbol, interval='daily', time_period=kwargs.get('period', 14))
            else:
                self.logger.warning(f"Unsupported indicator: {indicator}")
                return None
            
            return data
        except Exception as e:
            self.logger.error(f"Failed to get technical indicator {indicator}: {e}")
            return None
    
    def get_company_overview(self, symbol: str = None) -> Optional[Dict[str, Any]]:
        """Get company fundamental data overview"""
        try:
            data, _ = self.fd.get_company_overview(symbol or self.symbol)
            return data.to_dict() if not data.empty else None
        except Exception as e:
            self.logger.error(f"Failed to get company overview: {e}")
            return None
    
    def get_earnings_data(self, symbol: str = None) -> Optional[Dict[str, pd.DataFrame]]:
        """Get earnings data"""
        try:
            annual_earnings, _ = self.fd.get_earnings(symbol or self.symbol)
            quarterly_earnings, _ = self.fd.get_earnings(symbol or self.symbol)
            
            return {
                'annual': annual_earnings,
                'quarterly': quarterly_earnings
            }
        except Exception as e:
            self.logger.error(f"Failed to get earnings data: {e}")
            return None
    
    def get_income_statement(self, symbol: str = None) -> Optional[Dict[str, pd.DataFrame]]:
        """Get income statement data"""
        try:
            annual_income, _ = self.fd.get_income_statement_annual(symbol or self.symbol)
            quarterly_income, _ = self.fd.get_income_statement_quarterly(symbol or self.symbol)
            
            return {
                'annual': annual_income,
                'quarterly': quarterly_income
            }
        except Exception as e:
            self.logger.error(f"Failed to get income statement: {e}")
            return None
    
    def get_balance_sheet(self, symbol: str = None) -> Optional[Dict[str, pd.DataFrame]]:
        """Get balance sheet data"""
        try:
            annual_balance, _ = self.fd.get_balance_sheet_annual(symbol or self.symbol)
            quarterly_balance, _ = self.fd.get_balance_sheet_quarterly(symbol or self.symbol)
            
            return {
                'annual': annual_balance,
                'quarterly': quarterly_balance
            }
        except Exception as e:
            self.logger.error(f"Failed to get balance sheet: {e}")
            return None
    
    def get_cash_flow(self, symbol: str = None) -> Optional[Dict[str, pd.DataFrame]]:
        """Get cash flow statement"""
        try:
            annual_cashflow, _ = self.fd.get_cash_flow_annual(symbol or self.symbol)
            quarterly_cashflow, _ = self.fd.get_cash_flow_quarterly(symbol or self.symbol)
            
            return {
                'annual': annual_cashflow,
                'quarterly': quarterly_cashflow
            }
        except Exception as e:
            self.logger.error(f"Failed to get cash flow: {e}")
            return None
    
    def get_all_technical_indicators(self, symbol: str = None) -> Dict[str, pd.DataFrame]:
        """Get multiple technical indicators at once"""
        indicators = {}
        symbol = symbol or self.symbol
        
        # Trend indicators
        for period in [10, 20, 50]:
            sma = self.get_technical_indicators(symbol, "SMA", period=period)
            if sma is not None:
                indicators[f'SMA_{period}'] = sma
            
            ema = self.get_technical_indicators(symbol, "EMA", period=period)
            if ema is not None:
                indicators[f'EMA_{period}'] = ema
        
        # Momentum indicators
        rsi = self.get_technical_indicators(symbol, "RSI")
        if rsi is not None:
            indicators['RSI'] = rsi
        
        macd = self.get_technical_indicators(symbol, "MACD")
        if macd is not None:
            indicators['MACD'] = macd
        
        # Volatility indicators
        bbands = self.get_technical_indicators(symbol, "BBANDS")
        if bbands is not None:
            indicators['BBANDS'] = bbands
        
        # Oscillators
        stoch = self.get_technical_indicators(symbol, "STOCH")
        if stoch is not None:
            indicators['STOCH'] = stoch
        
        return indicators