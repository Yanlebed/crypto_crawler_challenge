"""
Configuration management for the crypto crawler.
Supports both environment variables and configuration files.
"""

import os
import logging
from dataclasses import dataclass
from typing import List

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class CrawlerConfig:
    """Configuration settings for the crypto crawler"""

    # HTTP Client settings
    http_timeout: int = 30
    http_max_retries: int = 5

    # Polling settings
    poll_interval: float = 1.0
    max_consecutive_failures: int = 5

    # Rate limiting
    html_scraping_delay: float = 0.5
    json_api_delay: float = 0.2

    # Moving average
    moving_average_window: int = 10

    # Storage settings
    storage_type: str = "csv"
    data_directory: str = "data"

    # Rate limiting
    requests_per_second: float = 2.0

    # API URLs
    coingecko_base_url: str = "https://api.coingecko.com/api/v3"
    coinmarketcap_base_url: str = "https://coinmarketcap.com"
    coinmarketcap_api_url: str = (
        "https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listing"
    )

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # CoinMarketCap settings
    cmc_pages_per_scrape: int = 5
    cmc_coins_per_page: int = 20

    @classmethod
    def from_env(cls) -> "CrawlerConfig":
        """Create configuration from environment variables"""
        return cls(
            http_timeout=int(os.getenv("CRYPTO_HTTP_TIMEOUT", "30")),
            http_max_retries=int(os.getenv("CRYPTO_HTTP_MAX_RETRIES", "5")),
            poll_interval=float(os.getenv("CRYPTO_POLL_INTERVAL", "1.0")),
            max_consecutive_failures=int(
                os.getenv("CRYPTO_MAX_FAILURES", "5")
            ),
            html_scraping_delay=float(os.getenv("CRYPTO_HTML_DELAY", "0.5")),
            json_api_delay=float(os.getenv("CRYPTO_JSON_DELAY", "0.2")),
            moving_average_window=int(os.getenv("CRYPTO_MA_WINDOW", "10")),
            storage_type=os.getenv("CRYPTO_STORAGE_TYPE", "csv"),
            data_directory=os.getenv("CRYPTO_DATA_DIR", "data"),
            requests_per_second=float(
                os.getenv("CRYPTO_REQUESTS_PER_SECOND", "2.0")
            ),
            coingecko_base_url=os.getenv(
                "COINGECKO_BASE_URL", "https://api.coingecko.com/api/v3"
            ),
            coinmarketcap_base_url=os.getenv(
                "COINMARKETCAP_BASE_URL", "https://coinmarketcap.com"
            ),
            coinmarketcap_api_url=os.getenv(
                "COINMARKETCAP_API_URL",
                "https://api.coinmarketcap.com/data-api/v3/"
                "cryptocurrency/listing"
            ),
            log_level=os.getenv("CRYPTO_LOG_LEVEL", "INFO"),
            log_format=os.getenv(
                "CRYPTO_LOG_FORMAT",
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ),
            cmc_pages_per_scrape=int(os.getenv("CRYPTO_CMC_PAGES", "5")),
            cmc_coins_per_page=int(os.getenv("CRYPTO_CMC_PER_PAGE", "20")),
        )

    def setup_logging(self) -> None:
        """Configure logging based on settings"""
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format=self.log_format,
            force=True,  # Override existing configuration
        )

        # Set specific loggers
        logging.getLogger("aiohttp").setLevel(
            logging.WARNING
        )  # Reduce aiohttp noise
        logging.getLogger("urllib3").setLevel(
            logging.WARNING
        )  # Reduce urllib3 noise

    def validate(self) -> List[str]:
        """Validate configuration settings"""
        errors = []

        if self.http_timeout <= 0:
            errors.append("http_timeout must be positive")

        if self.http_max_retries <= 0:
            errors.append("http_max_retries must be positive")

        if self.poll_interval <= 0:
            errors.append("poll_interval must be positive")

        if self.moving_average_window <= 0:
            errors.append("moving_average_window must be positive")

        if self.storage_type not in ["csv", "sqlite"]:
            errors.append("storage_type must be 'csv' or 'sqlite'")

        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            errors.append("log_level must be a valid logging level")

        return errors


def load_config() -> CrawlerConfig:
    """Load configuration from environment variables"""
    config = CrawlerConfig.from_env()

    # Validate configuration
    errors = config.validate()
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")

    # Setup logging
    config.setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("Configuration loaded successfully")
    logger.debug(f"HTTP timeout: {config.http_timeout}s")
    logger.debug(f"Max retries: {config.http_max_retries}")
    logger.debug(f"Poll interval: {config.poll_interval}s")

    return config
