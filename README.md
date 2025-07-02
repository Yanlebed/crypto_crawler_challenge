# Crypto Crawler Exercise

This is a implementation of the crypto crawler.

## Architecture

This implementation uses a clean, focused architecture:
- **3 essential interfaces** (IDataProvider, IStorage, IHttpClient)  
- **Focused data models**
- **1 service class** handling all functionality
- **Direct provider implementations** for CoinGecko and CoinMarketCap

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables (optional):
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your preferred settings (optional - defaults work fine)
nano .env
```

The application works perfectly with default settings - no configuration needed!

## Usage

### Run Both Phases:
```bash
python demo.py
```

### Run Specific Phase:
```bash
# Phase 1: Bitcoin price poller
python demo.py --phase 1

# Phase 2: CoinMarketCap scraping
python demo.py --phase 2
```

### Choose Storage Type:
```bash
# Use CSV storage (default)
python demo.py --storage csv

# Use SQLite storage
python demo.py --storage sqlite
```

## Phase 1: Price Pulse

- Polls Bitcoin price from CoinGecko every 1 second
- Calculates 10-period simple moving average
- Handles network errors with exponential backoff (1s → 2s → 4s → 8s → max 30s)
- **Stops automatically after 5 consecutive failures** (e.g., rate limit errors)
- Graceful shutdown with Ctrl-C

Output format:
```
[2025-01-17T10:30:45] BTC → USD: $70,123.45 SMA(10): $69,980.12
```

**Note:** CoinGecko's free API tier typically allows 5-6 requests before rate limiting. The poller will stop gracefully when this occurs.

## Phase 2: CoinMarketCap Watchlist

- Scrapes top 100 coins from CoinMarketCap (pages 1-5)
- Supports both HTML scraping and JSON API methods
- Stores data in CSV or SQLite format
- Compares performance between methods
- **Performance**: JSON API achieves ~100-135 records/second (HTML scraping currently returns 0 results)

## File Structure

```
├── src/
│   ├── core/
│   │   ├── interfaces.py           # 3 essential interfaces
│   │   ├── models.py               # Focused data models
│   │   └── config.py               # Configuration management
│   ├── http_client.py              # HTTP client with retry logic
│   ├── storage.py                  # CSV/SQLite storage
│   ├── providers.py                # CoinGecko & CoinMarketCap providers
│   └── service.py                  # Main service class
├── demo.py                         # Demo script
└── requirements.txt                # Dependencies
```

## Key Features

- **Exponential backoff retry** for network failures (1s → 2s → 4s → 8s → max 30s)
- **Automatic stopping** after 5 consecutive failures (protects against rate limiting)
- **Moving average calculation** with configurable window (shows SMA after 10 values)
- **Graceful shutdown** handling (Ctrl-C with cleanup)
- **Both CSV and SQLite storage** options
- **Performance comparison** between HTML and JSON methods
- **Focused on exercise requirements** without unnecessary complexity

## Example Output Files

After running the exercises, you'll see:
- `phase1_data_prices.csv` - Bitcoin price data with timestamps
- `phase2_data_listings.csv` - Top 100 cryptocurrency listings
- `phase2_data.db` - SQLite database (when using --storage sqlite)

This focused implementation maintains all exercise functionality without unnecessary complexity.

## Configuration

The application uses environment variables for configuration. All settings have sensible defaults.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CRYPTO_HTTP_TIMEOUT` | 30 | HTTP request timeout in seconds |
| `CRYPTO_HTTP_MAX_RETRIES` | 5 | Maximum number of retry attempts |
| `CRYPTO_REQUESTS_PER_SECOND` | 2.0 | Rate limit for API requests |
| `CRYPTO_POLL_INTERVAL` | 1.0 | Polling interval in seconds |
| `CRYPTO_MAX_FAILURES` | 5 | Max consecutive failures before stopping |
| `CRYPTO_HTML_DELAY` | 0.5 | Delay between HTML scraping requests |
| `CRYPTO_JSON_DELAY` | 0.2 | Delay between JSON API requests |
| `CRYPTO_MA_WINDOW` | 10 | Moving average window size |
| `CRYPTO_STORAGE_TYPE` | csv | Storage type (csv or sqlite) |
| `CRYPTO_DATA_DIR` | data | Directory for data files |
| `CRYPTO_LOG_LEVEL` | INFO | Logging level |
| `CRYPTO_CMC_PAGES` | 5 | Number of CoinMarketCap pages to scrape |
| `CRYPTO_CMC_PER_PAGE` | 20 | Number of coins per page |
| `COINGECKO_BASE_URL` | api.coingecko.com/api/v3 | CoinGecko API base URL |
| `COINMARKETCAP_BASE_URL` | coinmarketcap.com | CoinMarketCap base URL |
| `COINMARKETCAP_API_URL` | api.coinmarketcap.com/... | CoinMarketCap API URL |

### Configuration Files

- `.env` - Your local environment configuration (created from .env.example)
- `.env.example` - Template with default values

### Customizing Settings

You can customize the behavior by editing `.env`:

```bash
# Example: Change polling interval to 2 seconds
CRYPTO_POLL_INTERVAL=2.0

# Example: Use SQLite instead of CSV
CRYPTO_STORAGE_TYPE=sqlite

# Example: Increase moving average window
CRYPTO_MA_WINDOW=20

# Example: Enable debug logging
CRYPTO_LOG_LEVEL=DEBUG

# Example: Change API rate limit
CRYPTO_REQUESTS_PER_SECOND=1.0

# Example: Use custom API endpoint (for testing)
COINGECKO_BASE_URL=https://api.coingecko.com/api/v3
```

**Note:** You can run the application without any configuration changes - the defaults work perfectly for the exercise requirements. 