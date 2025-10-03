"""
API clients package initialization
"""

from .base_client import BaseAPIClient
from .yahoo_client import YahooFinanceClient

# Optional imports - only import if dependencies are available
try:
    from .alpha_vantage_client import AlphaVantageClient
except ImportError:
    AlphaVantageClient = None

try:
    from .news_client import NewsClient
except ImportError:
    NewsClient = None

__all__ = ['BaseAPIClient', 'YahooFinanceClient']

# Add optional clients to __all__ if available
if AlphaVantageClient:
    __all__.append('AlphaVantageClient')
if NewsClient:
    __all__.append('NewsClient')