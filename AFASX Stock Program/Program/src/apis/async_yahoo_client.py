"""
Async Yahoo Finance API client for improved performance
"""

import asyncio
import aiohttp
import pandas as pd
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor
from .base_client import BaseAPIClient


class AsyncYahooFinanceClient(BaseAPIClient):
    """Async Yahoo Finance API client for stock data"""
    
    def __init__(self):
        super().__init__(api_key="", base_url="", rate_limit=0.1)
        self.symbol = "AFI.AX"
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        self.executor.shutdown(wait=True)
    
    async def get_current_price(self, symbol: str = None) -> Optional[float]:
        """Get current stock price asynchronously"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor, 
                self._sync_get_current_price, 
                symbol or self.symbol
            )
            return result
        except Exception as e:
            self.logger.error(f"Failed to get current price: {e}")
            return None
    
    def _sync_get_current_price(self, symbol: str) -> Optional[float]:
        """Synchronous helper for current price"""
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return info.get('currentPrice') or info.get('regularMarketPrice')
    
    async def get_historical_data(self, symbol: str = None, period: str = "1y") -> Optional[pd.DataFrame]:
        """Get historical price data asynchronously"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._sync_get_historical_data,
                symbol or self.symbol,
                period
            )
            return result
        except Exception as e:
            self.logger.error(f"Failed to get historical data: {e}")
            return None
    
    def _sync_get_historical_data(self, symbol: str, period: str) -> Optional[pd.DataFrame]:
        """Synchronous helper for historical data"""
        ticker = yf.Ticker(symbol)
        return ticker.history(period=period)
    
    async def get_company_info(self, symbol: str = None) -> Optional[Dict[str, Any]]:
        """Get comprehensive company information asynchronously"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._sync_get_company_info,
                symbol or self.symbol
            )
            return result
        except Exception as e:
            self.logger.error(f"Failed to get company info: {e}")
            return None
    
    def _sync_get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Synchronous helper for company info"""
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        return {
            'name': info.get('longName', 'Australian Foundation Investment Company'),
            'sector': info.get('sector'),
            'industry': info.get('industry'),
            'market_cap': info.get('marketCap'),
            'enterprise_value': info.get('enterpriseValue'),
            'pe_ratio': info.get('trailingPE'),
            'pb_ratio': info.get('priceToBook'),
            'dividend_yield': info.get('dividendYield'),
            'payout_ratio': info.get('payoutRatio'),
            'beta': info.get('beta'),
            'shares_outstanding': info.get('sharesOutstanding'),
            'float_shares': info.get('floatShares'),
            'profit_margins': info.get('profitMargins'),
            'description': info.get('longBusinessSummary'),
            'website': info.get('website'),
            'employees': info.get('fullTimeEmployees')
        }
    
    async def get_dividend_history(self, symbol: str = None) -> Optional[pd.DataFrame]:
        """Get dividend history asynchronously"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._sync_get_dividend_history,
                symbol or self.symbol
            )
            return result
        except Exception as e:
            self.logger.error(f"Failed to get dividend history: {e}")
            return None
    
    def _sync_get_dividend_history(self, symbol: str) -> Optional[pd.DataFrame]:
        """Synchronous helper for dividend history"""
        ticker = yf.Ticker(symbol)
        return ticker.dividends
    
    async def get_multiple_symbols_data(self, symbols: List[str], period: str = "1y") -> Dict[str, Dict[str, Any]]:
        """Get data for multiple symbols concurrently"""
        tasks = []
        for symbol in symbols:
            task = asyncio.create_task(self._get_symbol_data(symbol, period))
            tasks.append((symbol, task))
        
        results = {}
        for symbol, task in tasks:
            try:
                results[symbol] = await task
            except Exception as e:
                self.logger.error(f"Failed to get data for {symbol}: {e}")
                results[symbol] = None
        
        return results
    
    async def _get_symbol_data(self, symbol: str, period: str) -> Dict[str, Any]:
        """Get comprehensive data for a single symbol"""
        # Run multiple operations concurrently
        tasks = [
            self.get_historical_data(symbol, period),
            self.get_company_info(symbol),
            self.get_current_price(symbol),
            self.get_dividend_history(symbol)
        ]
        
        historical_data, company_info, current_price, dividend_data = await asyncio.gather(*tasks)
        
        return {
            'historical_data': historical_data,
            'company_info': company_info,
            'current_price': current_price,
            'dividend_data': dividend_data
        }