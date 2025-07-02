"""
Providers for the crypto crawler exercise.
"""

import re
import jmespath
from typing import Dict, Any, List
from bs4 import BeautifulSoup

from .core.interfaces import IDataProvider
from .http_client import HttpClient


class CoinGeckoProvider(IDataProvider):
    """CoinGecko provider for Bitcoin price polling"""

    def __init__(self, http_client: HttpClient, config=None):
        self.http_client = http_client
        if config:
            self.base_url = config.coingecko_base_url
        else:
            self.base_url = "https://api.coingecko.com/api/v3"

    async def get_price(self, symbol: str = "bitcoin") -> Dict[str, Any]:
        """Get current Bitcoin price from CoinGecko"""
        url = (
            f"{self.base_url}/simple/price?ids={symbol}"
            "&vs_currencies=usd&include_last_updated_at=true"
        )
        data = await self.http_client.get(url)

        price = jmespath.search(f"{symbol}.usd", data)
        last_updated = jmespath.search(f"{symbol}.last_updated_at", data)

        if price is None:
            raise ValueError(f"Price data not found for {symbol}")

        return {"symbol": "BTC", "price": price, "last_updated": last_updated}

    async def get_listings(
        self, page: int = 1, limit: int = 100
    ) -> List[Dict[str, Any]]:
        return []


class CoinMarketCapProvider(IDataProvider):
    """CoinMarketCap provider for scraping and JSON API"""

    def __init__(self, http_client: HttpClient, config=None):
        self.http_client = http_client
        if config:
            self.base_url = config.coinmarketcap_base_url
            self.api_url = config.coinmarketcap_api_url
        else:
            self.base_url = "https://coinmarketcap.com"
            self.api_url = (
                "https://api.coinmarketcap.com/data-api/v3/"
                "cryptocurrency/listing"
            )

    async def get_price(self, symbol: str) -> Dict[str, Any]:
        return {}

    async def get_listings(
        self, page: int = 1, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get coin listings from CoinMarketCap (JSON API method)"""
        start = (page - 1) * limit + 1
        url = (
            f"{self.api_url}?start={start}&limit={limit}"
            "&sortBy=market_cap&sortType=desc&convert=USD"
        )

        data = await self.http_client.get(url)
        listings = []

        crypto_list = jmespath.search("data.cryptoCurrencyList", data) or []

        for item in crypto_list:
            # Extract data using JMESPath expressions for better error handling
            rank = jmespath.search("cmcRank", item)
            name = jmespath.search("name", item)
            symbol = jmespath.search("symbol", item)
            price = jmespath.search("quotes[0].price", item)
            change_24h = jmespath.search("quotes[0].percentChange24h", item)
            market_cap = jmespath.search("quotes[0].marketCap", item)

            # Only add if we have the essential data
            if all(x is not None for x in [rank, name, symbol, price]):
                listings.append(
                    {
                        "rank": rank,
                        "name": name,
                        "symbol": symbol,
                        "price": price,
                        "change_24h": change_24h or 0.0,
                        "market_cap": market_cap or 0.0,
                    }
                )

        return listings

    async def get_listings_html(self, page: int = 1) -> List[Dict[str, Any]]:
        """Get coin listings by scraping HTML (for comparison)"""
        if page > 1:
            url = f"{self.base_url}/page/{page}/"
        else:
            url = f"{self.base_url}/"

        # For HTML scraping, we need to get the raw HTML, not JSON
        session = await self.http_client._get_session()
        async with session.get(url) as response:
            html = await response.text()

        soup = BeautifulSoup(html, "html.parser")
        listings = []

        # Find the crypto table rows
        rows = soup.find_all("tr", class_="cmc-table-row")

        for row in rows:
            try:
                rank_elem = row.find("p", class_="coin-item-symbol")
                if not rank_elem:
                    continue

                rank_match = re.search(r"\d+", rank_elem.get_text())
                if not rank_match:
                    continue
                rank = int(rank_match.group())

                name_elem = row.find("p", class_="sc-4984dd93-0")
                symbol_elem = row.find("p", class_="coin-item-symbol")
                price_elem = row.find("div", class_="sc-b3fc6b7-0")
                change_elem = row.find("span", string=re.compile(r"%"))

                if all([name_elem, symbol_elem, price_elem]):
                    name = name_elem.get_text().strip()
                    symbol = symbol_elem.get_text().strip()
                    price_text = price_elem.get_text().strip()
                    price = float(re.sub(r"[^\d.]", "", price_text))

                    change_24h = 0.0
                    if change_elem:
                        change_text = change_elem.get_text().strip()
                        change_24h = float(re.sub(r"[^\d.-]", "", change_text))

                    # Market cap extraction (simplified)
                    market_cap = price * 1000000  # Placeholder calculation

                    listings.append(
                        {
                            "rank": rank,
                            "name": name,
                            "symbol": symbol,
                            "price": price,
                            "change_24h": change_24h,
                            "market_cap": market_cap,
                        }
                    )
            except Exception:
                continue  # Skip malformed rows

        return listings
