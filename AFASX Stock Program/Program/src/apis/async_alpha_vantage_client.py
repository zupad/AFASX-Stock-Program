"""
Async Alpha Vantage API client for improved performance
"""

import asyncio
import aiohttp
import pandas as pd
from typing import Dict, Any, Optional, List
import logging
import json
from .base_client import BaseAPIClient


class AsyncAlphaVantageClient(BaseAPIClient):
    """Async Alpha Vantage API client for financial data"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "https://www.alphavantage.co", rate_limit=12.0)
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _make_async_request(self, function: str, symbol: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make async API request to Alpha Vantage"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        params = {
            'function': function,
            'symbol': symbol,
            'apikey': self.api_key,
            **kwargs
        }
        
        try:
            # Rate limiting
            await asyncio.sleep(self.rate_limit)
            
            async with self.session.get(
                f"{self.base_url}/query",
                params=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                # Check for API errors
                if 'Error Message' in data:
                    self.logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                    return None
                
                if 'Note' in data:
                    self.logger.warning(f"Alpha Vantage API limit: {data['Note']}")
                    return None
                
                return data
                
        except Exception as e:
            self.logger.error(f"Alpha Vantage API request failed: {e}")
            return None
    
    async def get_current_price(self, symbol: str = None) -> Optional[float]:
        """Get current price using Global Quote"""
        symbol = symbol or "AFI.AX"
        
        data = await self._make_async_request(
            function='GLOBAL_QUOTE',
            symbol=symbol.replace('.AX', '')  # Remove .AX for Alpha Vantage
        )
        
        if not data:
            return None
        
        try:
            quote = data.get('Global Quote', {})
            price = quote.get('05. price')
            return float(price) if price else None
        except (KeyError, ValueError, TypeError):
            return None
    
    async def get_historical_data(self, symbol: str = None, period: str = "1y") -> Optional[pd.DataFrame]:
        """Get historical daily data"""
        symbol = symbol or "AFI.AX"
        
        # Choose function based on period
        if period in ["1d", "5d"]:
            function = 'TIME_SERIES_INTRADAY'
            extra_params = {'interval': '5min', 'outputsize': 'full'}
        else:
            function = 'TIME_SERIES_DAILY_ADJUSTED'
            extra_params = {'outputsize': 'full'}
        
        data = await self._make_async_request(
            function=function,
            symbol=symbol.replace('.AX', ''),
            **extra_params
        )
        
        if not data:
            return None
        
        try:
            # Extract time series data
            if function == 'TIME_SERIES_INTRADAY':
                time_series_key = 'Time Series (5min)'
            else:
                time_series_key = 'Time Series (Daily)'
            
            time_series = data.get(time_series_key, {})
            
            if not time_series:
                return None
            
            # Convert to DataFrame
            df_data = []
            for date_str, values in time_series.items():
                row = {
                    'Date': pd.to_datetime(date_str),
                    'Open': float(values.get('1. open', 0)),
                    'High': float(values.get('2. high', 0)),
                    'Low': float(values.get('3. low', 0)),
                    'Close': float(values.get('4. close', 0)),
                    'Volume': int(values.get('5. volume', 0))
                }
                
                if function == 'TIME_SERIES_DAILY_ADJUSTED':
                    row['Adj Close'] = float(values.get('5. adjusted close', 0))
                    row['Dividend'] = float(values.get('7. dividend amount', 0))
                    row['Split'] = float(values.get('8. split coefficient', 1))
                
                df_data.append(row)
            
            df = pd.DataFrame(df_data)
            df.set_index('Date', inplace=True)
            df.sort_index(inplace=True)
            
            return df
            
        except (KeyError, ValueError, TypeError) as e:
            self.logger.error(f"Failed to parse historical data: {e}")
            return None
    
    async def get_technical_indicator(self, symbol: str = None, indicator: str = "SMA", **kwargs) -> Optional[pd.DataFrame]:
        """Get technical indicators"""
        symbol = symbol or "AFI.AX"
        
        # Map indicators to Alpha Vantage functions
        indicator_map = {
            'SMA': 'SMA',
            'EMA': 'EMA',
            'RSI': 'RSI',
            'MACD': 'MACD',
            'BBANDS': 'BBANDS',
            'STOCH': 'STOCH',
            'ADX': 'ADX',
            'AROON': 'AROON'
        }
        
        function = indicator_map.get(indicator.upper())
        if not function:
            self.logger.warning(f"Unsupported indicator: {indicator}")
            return None
        
        params = {
            'interval': 'daily',
            'time_period': kwargs.get('period', 20),
            'series_type': kwargs.get('series_type', 'close')
        }
        
        data = await self._make_async_request(
            function=function,
            symbol=symbol.replace('.AX', ''),
            **params
        )
        
        if not data:
            return None
        
        try:
            # Find the technical analysis key
            tech_key = None
            for key in data.keys():
                if 'Technical Analysis' in key:
                    tech_key = key
                    break
            
            if not tech_key:
                return None
            
            tech_data = data[tech_key]
            
            # Convert to DataFrame
            df_data = []
            for date_str, values in tech_data.items():
                row = {'Date': pd.to_datetime(date_str)}
                for value_key, value in values.items():
                    clean_key = value_key.split('. ')[-1]  # Remove number prefix
                    row[clean_key] = float(value)
                df_data.append(row)
            
            df = pd.DataFrame(df_data)
            df.set_index('Date', inplace=True)
            df.sort_index(inplace=True)
            
            return df
            
        except (KeyError, ValueError, TypeError) as e:
            self.logger.error(f"Failed to parse technical indicator {indicator}: {e}")
            return None
    
    async def get_multiple_indicators(self, symbol: str = None, indicators: List[str] = None) -> Dict[str, pd.DataFrame]:
        """Get multiple technical indicators concurrently"""
        symbol = symbol or "AFI.AX"
        indicators = indicators or ['SMA', 'RSI', 'MACD', 'BBANDS']
        
        tasks = []
        for indicator in indicators:
            task = asyncio.create_task(self.get_technical_indicator(symbol, indicator))
            tasks.append((indicator, task))
        
        results = {}
        for indicator, task in tasks:
            try:
                results[indicator] = await task
            except Exception as e:
                self.logger.error(f"Failed to get {indicator}: {e}")
                results[indicator] = None
        
        return results
    
    async def get_company_overview(self, symbol: str = None) -> Optional[Dict[str, Any]]:
        """Get company fundamental data overview"""
        symbol = symbol or "AFI.AX"
        
        data = await self._make_async_request(
            function='OVERVIEW',
            symbol=symbol.replace('.AX', '')
        )
        
        if not data:
            return None
        
        try:
            return {
                'name': data.get('Name'),
                'description': data.get('Description'),
                'sector': data.get('Sector'),
                'industry': data.get('Industry'),
                'market_cap': float(data.get('MarketCapitalization', 0)),
                'pe_ratio': float(data.get('PERatio', 0)),
                'peg_ratio': float(data.get('PEGRatio', 0)),
                'book_value': float(data.get('BookValue', 0)),
                'dividend_per_share': float(data.get('DividendPerShare', 0)),
                'dividend_yield': float(data.get('DividendYield', 0)),
                'eps': float(data.get('EPS', 0)),
                'revenue_per_share': float(data.get('RevenuePerShareTTM', 0)),
                'profit_margin': float(data.get('ProfitMargin', 0)),
                'operating_margin': float(data.get('OperatingMarginTTM', 0)),
                'return_on_assets': float(data.get('ReturnOnAssetsTTM', 0)),
                'return_on_equity': float(data.get('ReturnOnEquityTTM', 0)),
                'revenue': float(data.get('RevenueTTM', 0)),
                'gross_profit': float(data.get('GrossProfitTTM', 0)),
                'diluted_eps': float(data.get('DilutedEPSTTM', 0)),
                'quarterly_earnings_growth': float(data.get('QuarterlyEarningsGrowthYOY', 0)),
                'quarterly_revenue_growth': float(data.get('QuarterlyRevenueGrowthYOY', 0)),
                'analyst_target_price': float(data.get('AnalystTargetPrice', 0)),
                'trailing_pe': float(data.get('TrailingPE', 0)),
                'forward_pe': float(data.get('ForwardPE', 0)),
                'price_to_sales_ratio': float(data.get('PriceToSalesRatioTTM', 0)),
                'price_to_book_ratio': float(data.get('PriceToBookRatio', 0)),
                'ev_to_revenue': float(data.get('EVToRevenue', 0)),
                'ev_to_ebitda': float(data.get('EVToEBITDA', 0)),
                'beta': float(data.get('Beta', 0)),
                '52_week_high': float(data.get('52WeekHigh', 0)),
                '52_week_low': float(data.get('52WeekLow', 0)),
                '50_day_ma': float(data.get('50DayMovingAverage', 0)),
                '200_day_ma': float(data.get('200DayMovingAverage', 0)),
                'shares_outstanding': float(data.get('SharesOutstanding', 0))
            }
        except (ValueError, TypeError) as e:
            self.logger.error(f"Failed to parse company overview: {e}")
            return None