"""
Financial metrics and ratio analysis
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import logging

class FinancialAnalyzer:
    """Financial metrics and ratio analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_returns(self, prices: pd.Series) -> Dict[str, float]:
        """Calculate various return metrics"""
        if len(prices) < 2:
            return {}
        
        # Daily returns
        daily_returns = prices.pct_change().dropna()
        
        # Total return
        total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
        
        # Annualized return
        trading_days = len(daily_returns)
        years = trading_days / 252  # Approximate trading days per year
        annualized_return = ((prices.iloc[-1] / prices.iloc[0]) ** (1/years) - 1) * 100 if years > 0 else 0
        
        # Volatility (annualized)
        volatility = daily_returns.std() * np.sqrt(252) * 100
        
        # Sharpe ratio (assuming risk-free rate of 2%)
        risk_free_rate = 0.02
        excess_return = (annualized_return - risk_free_rate * 100) / 100
        sharpe_ratio = excess_return / (volatility / 100) if volatility > 0 else 0
        
        # Maximum drawdown
        cumulative = (1 + daily_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'avg_daily_return': daily_returns.mean() * 100,
            'std_daily_return': daily_returns.std() * 100
        }
    
    def calculate_dividend_metrics(self, prices: pd.Series, dividends: pd.DataFrame) -> Dict[str, Any]:
        """Calculate dividend-related metrics"""
        if dividends.empty:
            return {}
        
        current_price = prices.iloc[-1] if not prices.empty else 0
        
        # Annual dividend yield
        annual_dividends = dividends.groupby(dividends.index.year)['Amount'].sum()
        latest_annual_dividend = annual_dividends.iloc[-1] if not annual_dividends.empty else 0
        dividend_yield = (latest_annual_dividend / current_price * 100) if current_price > 0 else 0
        
        # Dividend growth rate
        if len(annual_dividends) > 1:
            dividend_growth_rates = annual_dividends.pct_change().dropna()
            avg_dividend_growth = dividend_growth_rates.mean() * 100
        else:
            avg_dividend_growth = 0
        
        # Dividend frequency
        dividend_frequency = len(dividends) / len(annual_dividends) if len(annual_dividends) > 0 else 0
        
        # Total dividends received
        total_dividends = dividends['Amount'].sum()
        
        return {
            'current_yield': dividend_yield,
            'annual_dividend': latest_annual_dividend,
            'dividend_growth_rate': avg_dividend_growth,
            'dividend_frequency': dividend_frequency,
            'total_dividends': total_dividends,
            'dividend_history': annual_dividends.to_dict()
        }
    
    def calculate_portfolio_metrics(self, holdings: List[Dict], current_prices: Dict[str, float]) -> Dict[str, Any]:
        """Calculate portfolio performance metrics"""
        if not holdings:
            return {}
        
        total_investment = 0
        total_current_value = 0
        total_dividends_received = 0
        
        for holding in holdings:
            symbol = holding['symbol']
            shares = holding['shares']
            purchase_price = holding['purchase_price']
            current_price = current_prices.get(symbol, purchase_price)
            
            investment = shares * purchase_price
            current_value = shares * current_price
            
            total_investment += investment
            total_current_value += current_value
        
        # Calculate returns
        capital_gain = total_current_value - total_investment
        capital_gain_percent = (capital_gain / total_investment * 100) if total_investment > 0 else 0
        total_return_percent = ((total_current_value + total_dividends_received) / total_investment - 1) * 100 if total_investment > 0 else 0
        
        return {
            'total_investment': total_investment,
            'current_value': total_current_value,
            'capital_gain': capital_gain,
            'capital_gain_percent': capital_gain_percent,
            'total_return_percent': total_return_percent,
            'dividends_received': total_dividends_received
        }