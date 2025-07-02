"""
Interfaces for the crypto crawler exercise.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime


class IDataProvider(ABC):
    """Interface for data providers (CoinGecko, CoinMarketCap)"""

    @abstractmethod
    async def get_price(self, symbol: str) -> Dict[str, Any]:
        """Get the current price for a symbol"""
        pass

    @abstractmethod
    async def get_listings(
        self, page: int = 1, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get cryptocurrency listings"""
        pass


class IStorage(ABC):
    """Interface for storage implementations (CSV, SQLite)"""

    @abstractmethod
    async def store_price(
        self, symbol: str, price: float, timestamp: datetime
    ) -> None:
        """Store price data"""
        pass

    @abstractmethod
    async def store_listings(self, listings: List[Dict[str, Any]]) -> None:
        """Store cryptocurrency listings"""
        pass

    @abstractmethod
    async def get_recent_prices(
        self, symbol: str, count: int
    ) -> List[Dict[str, Any]]:
        """Get recent prices"""
        pass


class IHttpClient(ABC):
    """Interface for HTTP client implementations"""

    @abstractmethod
    async def get(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make GET request"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close HTTP session"""
        pass
