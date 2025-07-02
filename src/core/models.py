"""
Data models for the crypto crawler exercise.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class PriceData:
    """Bitcoin price data"""

    symbol: str
    price: float
    timestamp: datetime
    source: str = "coingecko"
    
    def __str__(self):
        return (
            f"[{self.timestamp.strftime('%Y-%m-%dT%H:%M:%S')}] "
            f"{self.symbol.upper()} → USD: ${self.price:,.2f}"
        )


@dataclass
class CoinData:
    """Coin listing data from CoinMarketCap"""

    rank: int
    name: str
    symbol: str
    price: float
    change_24h: float
    market_cap: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "name": self.name,
            "symbol": self.symbol,
            "price": self.price,
            "change_24h": self.change_24h,
            "market_cap": self.market_cap,
        }


@dataclass
class MovingAverage:
    """Moving average calculator"""

    window_size: int
    values: List[float]
    
    def __post_init__(self):
        self.values = []
    
    def add_value(self, value: float) -> None:
        """Add a new value and maintain window size"""
        self.values.append(value)
        if len(self.values) > self.window_size:
            self.values.pop(0)
    
    def get_average(self) -> Optional[float]:
        """Calculate moving average"""
        if not self.values:
            return None
        return sum(self.values) / len(self.values)
    
    def is_ready(self) -> bool:
        """Check if we have enough values for a meaningful average"""
        return len(self.values) >= self.window_size 
