"""
Service for the crypto crawler exercise.
"""

import asyncio
import logging
import signal
from datetime import datetime
from typing import Optional, List, Dict, Any

from .core.models import PriceData, MovingAverage
from .core.interfaces import IStorage
from .core.config import CrawlerConfig, load_config
from .providers import CoinGeckoProvider, CoinMarketCapProvider
from .http_client import HttpClient


class CryptoCrawlerService:
    """Service handling all crypto crawler functionality"""

    def __init__(
        self, storage: IStorage, config: Optional[CrawlerConfig] = None
    ):
        if config is None:
            config = load_config()

        self.config = config
        self.storage = storage
        self.http_client = HttpClient(
            timeout=config.http_timeout,
            max_retries=config.http_max_retries,
            requests_per_second=config.requests_per_second,
        )
        self.coingecko = CoinGeckoProvider(self.http_client, config)
        self.coinmarketcap = CoinMarketCapProvider(self.http_client, config)
        self.moving_average = MovingAverage(
            window_size=config.moving_average_window, values=[]
        )
        self.running = False
        self.consecutive_failures = 0
        self.logger = logging.getLogger(__name__)

    async def start_price_poller(self) -> None:
        """Start Phase 1: Bitcoin price polling with moving average"""
        self.logger.info("Starting Bitcoin price poller...")
        print("Starting Bitcoin price poller...")
        print("Press Ctrl-C to stop")

        self.running = True

        # Setup signal handler for graceful shutdown
        def signal_handler(signum, frame):
            self.logger.info("Shutdown signal received")
            print("\nShutting down...")
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)

        while self.running:
            try:
                # Fetch Bitcoin price
                price_data = await self.coingecko.get_price("bitcoin")
                timestamp = datetime.now()

                # Create a price object
                btc_price = PriceData(
                    symbol="BTC",
                    price=price_data["price"],
                    timestamp=timestamp
                )

                # Store price
                await self.storage.store_price(
                    btc_price.symbol, btc_price.price, btc_price.timestamp
                )

                # Update moving average
                self.moving_average.add_value(btc_price.price)

                # Print price info
                output = str(btc_price)
                if self.moving_average.is_ready():
                    sma = self.moving_average.get_average()
                    output += f" SMA(10): ${sma:,.2f}"

                print(output)
                self.logger.debug(f"Bitcoin price: ${btc_price.price:,.2f}")

                # Reset failure counter on success
                self.consecutive_failures = 0

                # Wait configured interval before the next poll
                await asyncio.sleep(self.config.poll_interval)

            except Exception as e:
                self.consecutive_failures += 1
                self.logger.warning(
                    f"Price fetch failed "
                    f"(attempt {self.consecutive_failures}): {e}"
                )

                if (
                    self.consecutive_failures
                    >= self.config.max_consecutive_failures
                ):
                    error_msg = (
                        f"ERROR: {self.config.max_consecutive_failures} "
                        f"consecutive failures. Last error: {e}"
                    )
                    self.logger.error(error_msg)
                    print(error_msg)
                    print("Stopping price poller due to repeated failures.")
                    self.running = False
                    break

                # Wait before retry with exponential backoff
                wait_time = min(2 ** (self.consecutive_failures - 1), 30)
                self.logger.info(f"Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)

        await self.http_client.close()
        self.logger.info("Price poller stopped")
        print("Price poller stopped.")

    async def crawl_coinmarketcap_html(
        self, pages: int = 5
    ) -> List[Dict[str, Any]]:
        """Phase 2.1: Scrape CoinMarketCap using HTML parsing"""
        self.logger.info(f"Starting HTML scraping for {pages} pages")
        print(f"Scraping CoinMarketCap HTML (pages 1-{pages})...")

        all_listings = []
        for page in range(1, pages + 1):
            self.logger.debug(f"Scraping HTML page {page}")
            print(f"Scraping page {page}...")
            try:
                listings = await self.coinmarketcap.get_listings_html(page)
                all_listings.extend(listings)
                # Be nice to the server
                await asyncio.sleep(self.config.html_scraping_delay)
            except Exception as e:
                error_msg = f"Error scraping page {page}: {e}"
                self.logger.error(error_msg)
                print(error_msg)

        # Store results
        await self.storage.store_listings(all_listings)
        result_msg = f"Scraped {len(all_listings)} coins via HTML"
        self.logger.info(result_msg)
        print(result_msg)
        return all_listings

    async def crawl_coinmarketcap_json(
        self, pages: int = 5, per_page: int = 20
    ) -> List[Dict[str, Any]]:
        """Phase 2.2: Scrape CoinMarketCap using JSON API"""
        self.logger.info(f"Starting JSON API scraping for {pages} pages")
        print(f"Scraping CoinMarketCap JSON API (pages 1-{pages})...")

        all_listings = []
        for page in range(1, pages + 1):
            self.logger.debug(f"Fetching JSON page {page}")
            print(f"Fetching page {page}...")
            try:
                listings = await self.coinmarketcap.get_listings(
                    page, per_page
                )
                all_listings.extend(listings)
                # Faster with JSON API
                await asyncio.sleep(self.config.json_api_delay)
            except Exception as e:
                error_msg = f"Error fetching page {page}: {e}"
                self.logger.error(error_msg)
                print(error_msg)

        # Store results
        await self.storage.store_listings(all_listings)
        result_msg = f"Scraped {len(all_listings)} coins via JSON API"
        self.logger.info(result_msg)
        print(result_msg)
        return all_listings

    async def compare_methods(self) -> Dict[str, Any]:
        """Compare HTML vs. JSON scraping methods"""
        print("Comparing HTML vs JSON methods...")

        # Measure HTML method
        start_time = datetime.now()
        # Smaller sample for comparison
        html_results = await self.crawl_coinmarketcap_html(2)
        html_duration = (datetime.now() - start_time).total_seconds()

        # Wait a bit between methods
        await asyncio.sleep(2)

        # Measure JSON method
        start_time = datetime.now()
        json_results = await self.crawl_coinmarketcap_json(
            2, 50
        )  # 2 pages, 50 per page = 100 total
        json_duration = (datetime.now() - start_time).total_seconds()

        # Calculate throughput
        html_rps = (
            len(html_results) / html_duration if html_duration > 0 else 0
        )
        json_rps = (
            len(json_results) / json_duration if json_duration > 0 else 0
        )

        comparison = {
            "html_method": {
                "records": len(html_results),
                "duration": html_duration,
                "records_per_second": html_rps,
            },
            "json_method": {
                "records": len(json_results),
                "duration": json_duration,
                "records_per_second": json_rps,
            },
        }

        print("\nPerformance Comparison:")
        print(
            f"HTML Method: {len(html_results)} records in "
            f"{html_duration:.2f}s ({html_rps:.2f} records/sec)"
        )
        print(
            f"JSON Method: {len(json_results)} records in "
            f"{json_duration:.2f}s ({json_rps:.2f} records/sec)"
        )
        print(
            f"JSON is {json_rps / html_rps:.1f}x faster"
            if html_rps > 0
            else "JSON method succeeded"
        )

        return comparison

    async def close(self):
        """Cleanup resources"""
        await self.http_client.close()
