#!/usr/bin/env python3
"""
Demo for the crypto crawler exercise.
"""

import asyncio
import argparse
import logging
import os
from src.service import CryptoCrawlerService
from src.storage import Storage
from src.core.config import load_config


async def run_phase1(storage_type: str = "csv", config=None):
    """Run Phase 1: Bitcoin price poller with moving average"""
    if config is None:
        config = load_config()

    logger = logging.getLogger(__name__)
    logger.info(f"Starting Phase 1 with {storage_type} storage")

    file_path = os.path.join(config.data_directory, "phase1_data")
    storage = Storage(storage_type, file_path)
    service = CryptoCrawlerService(storage, config)

    try:
        await service.start_price_poller()
    finally:
        await service.close()


async def run_phase2(storage_type: str = "csv", config=None):
    """Run Phase 2: CoinMarketCap scraping"""
    if config is None:
        config = load_config()

    logger = logging.getLogger(__name__)
    logger.info(f"Starting Phase 2 with {storage_type} storage")

    file_path = os.path.join(config.data_directory, "phase2_data")
    storage = Storage(storage_type, file_path)
    service = CryptoCrawlerService(storage, config)

    try:
        print("=== Phase 2.1: HTML Scraping ===")
        await service.crawl_coinmarketcap_html(
            pages=config.cmc_pages_per_scrape
        )

        print("\n=== Phase 2.2: JSON API ===")
        await service.crawl_coinmarketcap_json(
            pages=config.cmc_pages_per_scrape,
            per_page=config.cmc_coins_per_page
        )

        print("\n=== Performance Comparison ===")
        await service.compare_methods()

    finally:
        await service.close()


async def main():
    parser = argparse.ArgumentParser(description="Crypto Crawler Exercise")
    parser.add_argument(
        "--phase",
        choices=["1", "2", "both"],
        default="both",
        help="Which phase to run"
    )
    parser.add_argument(
        "--storage",
        choices=["csv", "sqlite"],
        default="csv",
        help="Storage type"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=None,
        help="Set logging level",
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config()

    # Override log level if specified
    if args.log_level:
        config.log_level = args.log_level
        config.setup_logging()
    elif args.verbose:
        config.log_level = "DEBUG"
        config.setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("Crypto Crawler Demo Starting")
    logger.info(
        f"Configuration: timeout={config.http_timeout}s, "
        f"retries={config.http_max_retries}"
    )

    try:
        if args.phase in ["1", "both"]:
            print("=== PHASE 1: Price Pulse ===")
            await run_phase1(args.storage, config)

        if args.phase in ["2", "both"]:
            print("\n=== PHASE 2: CoinMarketCap Watchlist ===")
            await run_phase2(args.storage, config)

        logger.info("Demo completed successfully")

    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
        print("\nDemo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
