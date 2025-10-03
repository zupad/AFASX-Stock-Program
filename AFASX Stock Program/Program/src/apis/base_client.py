"""
Base API client with common functionality
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class BaseAPIClient(ABC):
    """Base class for all API clients"""
    
    def __init__(self, api_key: str, base_url: str, rate_limit: float = 1.0):
        self.api_key = api_key
        self.base_url = base_url
        self.rate_limit = rate_limit  # Minimum seconds between requests
        self.last_request_time = 0
        
        # Setup session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Setup logging
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _rate_limit_check(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit:
            time.sleep(self.rate_limit - time_since_last)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make API request with rate limiting and error handling"""
        self._rate_limit_check()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            raise
    
    @abstractmethod
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for symbol"""
        pass
    
    @abstractmethod
    def get_historical_data(self, symbol: str, period: str) -> Optional[Dict[str, Any]]:
        """Get historical price data"""
        pass