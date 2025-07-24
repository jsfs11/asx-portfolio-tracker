#!/usr/bin/env python3
"""
Automated ASX Ticker Addition Script
Fetches and populates all missing data for a new ASX ticker
"""

import argparse
import sqlite3
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import yfinance as yf

from config import EODHD_API_KEY
from portfolio_tracker import ASXPortfolioTracker

# Sector mapping from Yahoo Finance to our system
SECTOR_MAPPING = {
    "Basic Materials": "Materials",
    "Communication Services": "Communication Services",
    "Consumer Cyclical": "Consumer Discretionary",
    "Consumer Defensive": "Consumer Staples",
    "Energy": "Energy",
    "Financial Services": "Financials",
    "Healthcare": "Health Care",
    "Industrials": "Industrials",
    "Real Estate": "Real Estate",
    "Technology": "Information Technology",
    "Utilities": "Utilities",
}

# Default franking rates by sector (Australian typical values)
DEFAULT_FRANKING_RATES = {
    "Financials": 100,
    "Materials": 100,
    "Consumer Staples": 100,
    "Consumer Discretionary": 90,
    "Industrials": 90,
    "Energy": 80,
    "Utilities": 80,
    "Health Care": 50,
    "Information Technology": 0,
    "Communication Services": 30,
    "Real Estate": 0,  # REITs don't pay franking credits
}


class ASXTickerIntegrator:
    """Automated integration of new ASX tickers"""

    def __init__(self, db_path: str = "portfolio.db"):
        self.db_path = db_path
        self.tracker = ASXPortfolioTracker()

    def fetch_yahoo_data(self, ticker: str) -> Dict[str, Any]:
        """Fetch comprehensive data from Yahoo Finance"""
        try:
            # Add .AX suffix for ASX stocks
            yahoo_ticker = f"{ticker}.AX"
            stock = yf.Ticker(yahoo_ticker)

            # Get basic info
            info = stock.info

            # Get dividend history
            try:
                dividends = stock.dividends
                dividend_history = dividends.tail(10) if not dividends.empty else None
            except:
                dividend_history = None

            # Get recent price data
            try:
                hist = stock.history(period="1mo")
                recent_price = hist["Close"].iloc[-1] if not hist.empty else None
            except:
                recent_price = None

            return {
                "info": info,
                "dividend_history": dividend_history,
                "recent_price": recent_price,
                "success": True,
            }

        except Exception as e:
            print(f"❌ Error fetching Yahoo Finance data for {ticker}: {e}")
            return {"success": False, "error": str(e)}

    def determine_franking_rate(self, sector: str, dividend_yield: float) -> int:
        """Determine estimated franking rate based on sector and dividend yield"""

        # If no dividends, no franking
        if dividend_yield == 0:
            return 0

        # Get default rate by sector
        sector_rate = DEFAULT_FRANKING_RATES.get(sector, 50)

        # Special cases
        if "REIT" in sector or "Real Estate" in sector:
            return 0  # REITs don't frank

        if "Technology" in sector or "Information Technology" in sector:
            return 0  # Tech companies typically don't frank

        return sector_rate

    def add_to_franking_database(self, ticker: str, sector: str, franking_rate: int):
        """Add ticker to franking database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create table if it doesn't exist
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS franking_static_data (
                    stock TEXT PRIMARY KEY,
                    typical_franking_rate REAL,
                    sector TEXT,
                    reliability TEXT,
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Insert or update
            cursor.execute(
                """
                INSERT OR REPLACE INTO franking_static_data 
                (stock, typical_franking_rate, sector, reliability, last_updated)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    ticker,
                    franking_rate,
                    sector,
                    "estimated",
                    datetime.now().isoformat(),
                ),
            )

            conn.commit()
            conn.close()
            print(
                f"✅ Added {ticker} to franking database: {franking_rate}% franked, {sector} sector"
            )

        except Exception as e:
            print(f"❌ Error adding to franking database: {e}")

    def add_dividend_history(self, ticker: str, dividend_history):
        """Add dividend history to database"""
        if dividend_history is None or dividend_history.empty:
            print(f"ℹ️  No dividend history found for {ticker}")
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create table if it doesn't exist
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS dividends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock TEXT,
                    ex_date TEXT,
                    amount REAL,
                    currency TEXT DEFAULT 'AUD',
                    announcement_date TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Add each dividend
            for date, amount in dividend_history.items():
                ex_date = date.strftime("%Y-%m-%d")
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO dividends 
                    (stock, ex_date, amount, currency)
                    VALUES (?, ?, ?, ?)
                """,
                    (ticker, ex_date, float(amount), "AUD"),
                )

            conn.commit()
            conn.close()
            print(f"✅ Added {len(dividend_history)} dividend records for {ticker}")

        except Exception as e:
            print(f"❌ Error adding dividend history: {e}")

    def fetch_current_price(self, ticker: str) -> Optional[float]:
        """Fetch current price and add to price history"""
        try:
            # Try EODHD API first
            price = self.tracker.get_current_price_eodhd(
                ticker, EODHD_API_KEY, force=False
            )

            if price is not None:
                # Store the price in history
                self.tracker.store_price_history(ticker, price, "EODHD")
                print(f"✅ Updated {ticker} price: ${price:.3f}")
                return price
            else:
                # Try fallback price
                fallback_price = self.tracker.get_fallback_price(ticker)
                if fallback_price is not None:
                    self.tracker.store_price_history(ticker, fallback_price, "fallback")
                    print(
                        f"⚠️  Using fallback price for {ticker}: ${fallback_price:.3f}"
                    )
                    return fallback_price
                else:
                    print(f"❌ Could not fetch price for {ticker}")
                    return None

        except Exception as e:
            print(f"❌ Error fetching current price: {e}")
            return None

    def validate_ticker(self, ticker: str) -> bool:
        """Validate ASX ticker format and existence"""
        if not ticker or len(ticker) < 2 or len(ticker) > 5:
            print(f"❌ Invalid ticker format: {ticker}")
            return False

        # Check if ticker already exists in database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check transactions table
            cursor.execute(
                "SELECT COUNT(*) FROM transactions WHERE stock = ?", (ticker,)
            )
            if cursor.fetchone()[0] > 0:
                print(f"⚠️  {ticker} already exists in portfolio")
                return True  # Exists but that's okay

            # Check franking database
            cursor.execute(
                "SELECT COUNT(*) FROM franking_static_data WHERE stock = ?", (ticker,)
            )
            exists = cursor.fetchone()[0] > 0

            conn.close()

            if exists:
                print(f"ℹ️  {ticker} already in franking database")

            return True

        except Exception as e:
            print(f"❌ Error validating ticker: {e}")
            return False

    def integrate_ticker(self, ticker: str, verbose: bool = True) -> bool:
        """Complete integration of a new ASX ticker"""
        ticker = ticker.upper()

        if verbose:
            print(f"\n🔄 Integrating {ticker} into ASX Portfolio Tracker")
            print("=" * 50)

        # 1. Validate ticker
        if not self.validate_ticker(ticker):
            return False

        # 2. Fetch Yahoo Finance data
        if verbose:
            print(f"📡 Fetching data for {ticker} from Yahoo Finance...")

        yahoo_data = self.fetch_yahoo_data(ticker)
        if not yahoo_data["success"]:
            print(f"❌ Failed to fetch data for {ticker}")
            return False

        info = yahoo_data["info"]

        # Extract key information
        company_name = info.get("longName", ticker)
        sector_raw = info.get("sector", "Unknown")
        sector = SECTOR_MAPPING.get(sector_raw, sector_raw)
        dividend_yield = info.get("dividendYield", 0.0) or 0.0
        dividend_yield_pct = dividend_yield * 100

        if verbose:
            print(f"📊 Company: {company_name}")
            print(f"📊 Sector: {sector} ({sector_raw})")
            print(f"📊 Dividend Yield: {dividend_yield_pct:.2f}%")

        # 3. Determine franking rate
        franking_rate = self.determine_franking_rate(sector, dividend_yield_pct)
        if verbose:
            print(f"📊 Estimated Franking Rate: {franking_rate}%")

        # 4. Add to franking database
        self.add_to_franking_database(ticker, sector, franking_rate)

        # 5. Add dividend history
        self.add_dividend_history(ticker, yahoo_data.get("dividend_history"))

        # 6. Fetch current price
        if verbose:
            print(f"💰 Fetching current price for {ticker}...")
        self.fetch_current_price(ticker)

        if verbose:
            print(f"\n✅ {ticker} successfully integrated!")
            print(f"📈 You can now add {ticker} transactions via:")
            print(f"   python3 portfolio_dashboard.py --add")
            print(f"📊 Current price: ${yahoo_data.get('recent_price', 'N/A'):.3f}")

        return True


def main():
    parser = argparse.ArgumentParser(
        description="Add new ASX ticker with automated data population"
    )
    parser.add_argument("ticker", help="ASX ticker symbol (e.g., CHN, CBA)")
    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output")
    parser.add_argument("--batch", "-b", nargs="+", help="Process multiple tickers")

    args = parser.parse_args()

    integrator = ASXTickerIntegrator()

    if args.batch:
        # Batch processing
        tickers = args.batch
        successful = 0

        print(f"🔄 Processing {len(tickers)} tickers...")

        for ticker in tickers:
            try:
                if integrator.integrate_ticker(ticker, verbose=not args.quiet):
                    successful += 1
                print()  # Spacing between tickers
            except Exception as e:
                print(f"❌ Failed to process {ticker}: {e}")

        print(f"✅ Successfully processed {successful}/{len(tickers)} tickers")

    else:
        # Single ticker
        ticker = args.ticker
        try:
            success = integrator.integrate_ticker(ticker, verbose=not args.quiet)
            if success:
                sys.exit(0)
            else:
                sys.exit(1)
        except Exception as e:
            print(f"❌ Error processing {ticker}: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
