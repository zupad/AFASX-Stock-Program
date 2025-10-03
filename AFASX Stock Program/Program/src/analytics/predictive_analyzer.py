"""
Predictive analysis and trend forecasting
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class PredictiveAnalyzer:
    """Predictive analysis and trend forecasting"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scaler = StandardScaler()
    
    def predict_price_trend(self, prices: pd.Series, days_ahead: int = 30) -> Dict[str, Any]:
        """Predict price trend using linear regression"""
        try:
            if len(prices) < 30:
                return {'error': 'Insufficient data for prediction'}
            
            # Prepare data
            prices_clean = prices.dropna()
            if len(prices_clean) < 10:
                return {'error': 'Not enough valid price data'}
            
            X = np.arange(len(prices_clean)).reshape(-1, 1)
            y = prices_clean.values
            
            # Fit linear regression model
            model = LinearRegression()
            model.fit(X, y)
            
            # Make predictions
            future_X = np.arange(len(prices_clean), len(prices_clean) + days_ahead).reshape(-1, 1)
            predictions = model.predict(future_X)
            
            # Calculate trend strength
            r_squared = model.score(X, y)
            trend_direction = 'bullish' if model.coef_[0] > 0 else 'bearish'
            trend_strength = abs(model.coef_[0]) / prices_clean.mean() * 100  # Normalized slope
            
            # Generate prediction dates
            last_date = prices.index[-1]
            prediction_dates = pd.date_range(start=last_date + timedelta(days=1), periods=days_ahead, freq='D')
            
            return {
                'trend_direction': trend_direction,
                'trend_strength': trend_strength,
                'r_squared': r_squared,
                'predictions': {
                    'dates': prediction_dates.tolist(),
                    'prices': predictions.tolist()
                },
                'current_price': prices_clean.iloc[-1],
                'predicted_price_30d': predictions[-1],
                'predicted_change_percent': ((predictions[-1] / prices_clean.iloc[-1]) - 1) * 100
            }
        
        except Exception as e:
            self.logger.error(f"Price trend prediction error: {e}")
            return {'error': str(e)}
    
    def analyze_support_resistance(self, prices: pd.Series, window: int = 20) -> Dict[str, List[float]]:
        """Identify support and resistance levels"""
        try:
            if len(prices) < window * 2:
                return {'support_levels': [], 'resistance_levels': []}
            
            # Find local minima (support) and maxima (resistance)
            support_levels = []
            resistance_levels = []
            
            for i in range(window, len(prices) - window):
                current_window = prices.iloc[i-window:i+window+1]
                current_price = prices.iloc[i]
                
                # Check if current price is local minimum (support)
                if current_price == current_window.min():
                    support_levels.append(current_price)
                
                # Check if current price is local maximum (resistance)
                if current_price == current_window.max():
                    resistance_levels.append(current_price)
            
            # Remove duplicates and sort
            support_levels = sorted(list(set(support_levels)))
            resistance_levels = sorted(list(set(resistance_levels)), reverse=True)
            
            # Keep only the most significant levels (top 5 of each)
            return {
                'support_levels': support_levels[:5],
                'resistance_levels': resistance_levels[:5]
            }
        
        except Exception as e:
            self.logger.error(f"Support/resistance analysis error: {e}")
            return {'support_levels': [], 'resistance_levels': []}
    
    def calculate_volatility_forecast(self, prices: pd.Series, window: int = 30) -> Dict[str, float]:
        """Forecast volatility using historical data"""
        try:
            if len(prices) < window:
                return {}
            
            returns = prices.pct_change().dropna()
            
            # Rolling volatility
            rolling_vol = returns.rolling(window=window).std() * np.sqrt(252) * 100
            
            # Current volatility
            current_vol = rolling_vol.iloc[-1]
            
            # Average historical volatility
            avg_vol = rolling_vol.mean()
            
            # Volatility trend
            vol_trend = rolling_vol.iloc[-5:].mean() - rolling_vol.iloc[-15:-5].mean()
            
            return {
                'current_volatility': current_vol,
                'average_volatility': avg_vol,
                'volatility_trend': vol_trend,
                'volatility_percentile': stats.percentileofscore(rolling_vol.dropna(), current_vol)
            }
        
        except Exception as e:
            self.logger.error(f"Volatility forecast error: {e}")
            return {}