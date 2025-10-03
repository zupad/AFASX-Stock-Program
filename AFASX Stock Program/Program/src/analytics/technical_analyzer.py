"""
Technical analysis calculations and indicators
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import logging
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class TechnicalAnalyzer:
    """Technical analysis calculations and indicators"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_sma(self, prices: pd.Series, window: int = 20) -> pd.Series:
        """Calculate Simple Moving Average"""
        return prices.rolling(window=window).mean()
    
    def calculate_ema(self, prices: pd.Series, window: int = 20) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return prices.ewm(span=window).mean()
    
    def calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        ema_fast = self.calculate_ema(prices, fast)
        ema_slow = self.calculate_ema(prices, slow)
        macd_line = ema_fast - ema_slow
        signal_line = self.calculate_ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def calculate_bollinger_bands(self, prices: pd.Series, window: int = 20, num_std: float = 2) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands"""
        sma = self.calculate_sma(prices, window)
        std = prices.rolling(window=window).std()
        
        return {
            'middle': sma,
            'upper': sma + (std * num_std),
            'lower': sma - (std * num_std)
        }
    
    def calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, k_window: int = 14, d_window: int = 3) -> Dict[str, pd.Series]:
        """Calculate Stochastic Oscillator"""
        lowest_low = low.rolling(window=k_window).min()
        highest_high = high.rolling(window=k_window).max()
        
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_window).mean()
        
        return {
            'k_percent': k_percent,
            'd_percent': d_percent
        }
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        
        true_range = pd.DataFrame({'hl': high_low, 'hc': high_close, 'lc': low_close}).max(axis=1)
        return true_range.rolling(window=window).mean()
    
    def calculate_williams_r(self, high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
        """Calculate Williams %R"""
        highest_high = high.rolling(window=window).max()
        lowest_low = low.rolling(window=window).min()
        
        return -100 * ((highest_high - close) / (highest_high - lowest_low))
    
    def calculate_momentum(self, prices: pd.Series, window: int = 10) -> pd.Series:
        """Calculate Momentum"""
        return prices.diff(window)
    
    def calculate_roc(self, prices: pd.Series, window: int = 10) -> pd.Series:
        """Calculate Rate of Change"""
        return ((prices - prices.shift(window)) / prices.shift(window)) * 100
    
    def detect_patterns(self, df: pd.DataFrame) -> Dict[str, List[datetime]]:
        """Detect common chart patterns"""
        patterns = {
            'bullish_engulfing': [],
            'bearish_engulfing': [],
            'hammer': [],
            'shooting_star': [],
            'doji': [],
            'golden_cross': [],
            'death_cross': []
        }
        
        if len(df) < 50:
            return patterns
        
        try:
            # Calculate moving averages for cross patterns
            df_copy = df.copy()
            df_copy['SMA_50'] = self.calculate_sma(df_copy['Close'], 50)
            df_copy['SMA_200'] = self.calculate_sma(df_copy['Close'], 200)
            
            for i in range(1, min(len(df_copy), 100)):  # Limit to avoid performance issues
                current = df_copy.iloc[i]
                previous = df_copy.iloc[i-1]
                
                # Candlestick patterns
                body_size = abs(current['Close'] - current['Open'])
                
                # Hammer (bullish reversal)
                if 'High' in df_copy.columns and 'Low' in df_copy.columns:
                    upper_shadow = current['High'] - max(current['Open'], current['Close'])
                    lower_shadow = min(current['Open'], current['Close']) - current['Low']
                    
                    if lower_shadow > body_size * 2 and upper_shadow < body_size * 0.1:
                        patterns['hammer'].append(current.name)
                    
                    # Shooting Star (bearish reversal)
                    if upper_shadow > body_size * 2 and lower_shadow < body_size * 0.1:
                        patterns['shooting_star'].append(current.name)
                
                # Doji (indecision)
                if body_size < (current['High'] - current['Low']) * 0.1:
                    patterns['doji'].append(current.name)
                
                # Moving Average Crosses (if we have enough data)
                if (not pd.isna(current.get('SMA_50')) and not pd.isna(current.get('SMA_200')) and
                    not pd.isna(previous.get('SMA_50')) and not pd.isna(previous.get('SMA_200'))):
                    
                    # Golden Cross (bullish)
                    if (previous['SMA_50'] <= previous['SMA_200'] and 
                        current['SMA_50'] > current['SMA_200']):
                        patterns['golden_cross'].append(current.name)
                    
                    # Death Cross (bearish)
                    if (previous['SMA_50'] >= previous['SMA_200'] and 
                        current['SMA_50'] < current['SMA_200']):
                        patterns['death_cross'].append(current.name)
        
        except Exception as e:
            self.logger.error(f"Pattern detection error: {e}")
        
        return patterns