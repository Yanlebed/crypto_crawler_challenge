"""
Storage for the crypto crawler exercise.
Supports both CSV and SQLite.
"""

import csv
import sqlite3
import os
from typing import List, Dict, Any
from datetime import datetime
import logging

from .core.interfaces import IStorage


class Storage(IStorage):
    """Storage implementation supporting CSV and SQLite"""

    def __init__(self, storage_type: str = "csv", file_path: str = "data"):
        self.storage_type = storage_type.lower()
        self.file_path = file_path
        self.logger = logging.getLogger(__name__)

        # Ensure directory structure exists
        self._ensure_directory_exists()

        if self.storage_type == "sqlite":
            self.db_path = f"{file_path}.db"
            self._init_sqlite()
        elif self.storage_type == "csv":
            self.csv_prices = f"{file_path}_prices.csv"
            self.csv_listings = f"{file_path}_listings.csv"
            self._init_csv()

    def _ensure_directory_exists(self):
        """Ensure the directory structure exists for file storage"""
        if self.storage_type == "sqlite":
            file_dir = os.path.dirname(f"{self.file_path}.db")
        else:
            # Both CSV files use the same base path, the same directory
            file_dir = os.path.dirname(f"{self.file_path}_prices.csv")

        # Create directory if it doesn't exist and is not empty
        if file_dir and not os.path.exists(file_dir):
            try:
                os.makedirs(file_dir, exist_ok=True)
                self.logger.info(f"Created directory: {file_dir}")
            except OSError as e:
                self.logger.error(f"Failed to create directory {file_dir}: {e}")
                raise RuntimeError(f"Cannot create storage directory: {file_dir}") from e

    def _init_sqlite(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create price table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                timestamp TEXT NOT NULL,
                source TEXT DEFAULT 'coingecko'
            )
        """
        )

        # Create listing table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rank INTEGER NOT NULL,
                name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                change_24h REAL NOT NULL,
                market_cap REAL NOT NULL,
                timestamp TEXT NOT NULL
            )
        """
        )

        conn.commit()
        conn.close()

    def _init_csv(self):
        """Initialize CSV files with headers only when needed"""
        # Files will be created when the first data is stored
        pass

    async def store_price(
        self, symbol: str, price: float, timestamp: datetime
    ) -> None:
        """Store price data"""
        if self.storage_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO prices (symbol, price, timestamp) "
                "VALUES (?, ?, ?)",
                (symbol, price, timestamp.isoformat()),
            )
            conn.commit()
            conn.close()
        else:
            # Create prices CSV with header if it doesn't exist
            if not os.path.exists(self.csv_prices):
                with open(self.csv_prices, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["symbol", "price", "timestamp", "source"])

            with open(self.csv_prices, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    symbol, price, timestamp.isoformat(), "coingecko"
                ])

    async def store_listings(self, listings: List[Dict[str, Any]]) -> None:
        """Store coin listings"""
        timestamp = datetime.now().isoformat()

        if self.storage_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            for listing in listings:
                cursor.execute(
                    (
                        "INSERT INTO listings (rank, name, symbol, price, "
                        "change_24h, market_cap, timestamp) VALUES "
                        "(?, ?, ?, ?, ?, ?, ?)"
                    ),
                    (
                        listing["rank"],
                        listing["name"],
                        listing["symbol"],
                        listing["price"],
                        listing["change_24h"],
                        listing["market_cap"],
                        timestamp,
                    ),
                )
            conn.commit()
            conn.close()
        else:
            # Create listings CSV with header if it doesn't exist
            if not os.path.exists(self.csv_listings):
                with open(self.csv_listings, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "rank", "name", "symbol", "price", "change_24h",
                        "market_cap", "timestamp"
                    ])

            with open(self.csv_listings, "a", newline="") as f:
                writer = csv.writer(f)
                for listing in listings:
                    writer.writerow(
                        [
                            listing["rank"],
                            listing["name"],
                            listing["symbol"],
                            listing["price"],
                            listing["change_24h"],
                            listing["market_cap"],
                            timestamp,
                        ]
                    )

    async def get_recent_prices(
        self, symbol: str, count: int
    ) -> List[Dict[str, Any]]:
        """Get recent prices for moving average calculation"""
        if self.storage_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                (
                    "SELECT price, timestamp FROM prices WHERE symbol = ? "
                    "ORDER BY timestamp DESC LIMIT ?"
                ),
                (symbol, count),
            )
            rows = cursor.fetchall()
            conn.close()
            return [{"price": row[0], "timestamp": row[1]} for row in rows]
        else:
            prices = []
            if os.path.exists(self.csv_prices):
                with open(self.csv_prices, "r") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row["symbol"] == symbol:
                            prices.append({
                                "price": float(row["price"]),
                                "timestamp": row["timestamp"]
                            })
            return prices[-count:] if prices else []
