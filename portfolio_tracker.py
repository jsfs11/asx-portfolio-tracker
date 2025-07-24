#!/usr/bin/env python3
"""
ASX Paper Trading Portfolio Tracker
Tracks portfolio performance with real-time prices, dividends, and fees
Enhanced with franking credit analysis for Australian investors
"""

import csv
import json
import sqlite3
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests

# Import franking calculator
try:
    from franking_calculator import (FrankingTaxCalculator,
                                     StaticFrankingDatabase,
                                     get_yahoo_dividend_data)

    FRANKING_AVAILABLE = True
except ImportError:
    print("Warning: Franking calculator not available. Some features may be limited.")
    FRANKING_AVAILABLE = False


@dataclass
class Transaction:
    date: str
    stock: str
    action: str  # 'buy' or 'sell'
    quantity: int
    price: float
    total: float
    status: str
    fees: float = 0.0


@dataclass
class Position:
    stock: str
    quantity: int
    avg_cost: float
    current_price: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    dividend_yield: float = 0.0
    total_dividends: float = 0.0


class ASXPortfolioTracker:
    def __init__(self, db_path: str = "portfolio.db", starting_cash: float = 25000.0):
        self.db_path = db_path
        self.starting_cash = starting_cash
        self.init_database()
        self.api_calls_today = 0
        self.last_api_reset = datetime.now().date()

        # ASX brokerage fee structure (typical)
        self.min_brokerage = 19.95
        self.brokerage_rate = 0.001  # 0.1%

        # Initialize franking calculator if available
        if FRANKING_AVAILABLE:
            self.franking_calculator: Optional[
                FrankingTaxCalculator
            ] = FrankingTaxCalculator(self.db_path)
            self.franking_db: Optional[
                StaticFrankingDatabase
            ] = StaticFrankingDatabase()
        else:
            self.franking_calculator = None
            self.franking_db = None

    def init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Transactions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                stock TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                total REAL NOT NULL,
                fees REAL NOT NULL,
                status TEXT NOT NULL
            )
        """
        )

        # Price history table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock TEXT NOT NULL,
                date TEXT NOT NULL,
                price REAL NOT NULL,
                source TEXT NOT NULL,
                UNIQUE(stock, date)
            )
        """
        )

        # Enhanced dividends table with franking information
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS dividends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock TEXT NOT NULL,
                ex_date TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'AUD',
                franking_credit REAL DEFAULT 0.0,
                franking_percentage REAL DEFAULT 0.0,
                tax_benefit REAL DEFAULT 0.0
            )
        """
        )

        # Franking static data table
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

        # Tax settings table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tax_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tax_year TEXT NOT NULL,
                taxable_income REAL NOT NULL,
                tax_bracket REAL NOT NULL,
                medicare_levy REAL DEFAULT 2.0,
                is_resident BOOLEAN DEFAULT 1,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # User settings and onboarding table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setup_completed BOOLEAN DEFAULT 0,
                starting_cash REAL DEFAULT 25000.0,
                portfolio_name TEXT DEFAULT 'My Portfolio',
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.commit()
        conn.close()

    def calculate_brokerage(self, total_value: float) -> float:
        """Calculate brokerage fees based on transaction value"""
        calculated_fee = total_value * self.brokerage_rate
        return max(calculated_fee, self.min_brokerage)

    def import_transactions_from_csv(self, csv_data: str):
        """Import transactions from CSV string"""
        lines = csv_data.strip().split("\n")
        reader = csv.DictReader(lines)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for row in reader:
            if row["Date"] == "Date":  # Skip header if present again
                continue

            total_value = float(row["Total"])
            fees = self.calculate_brokerage(total_value)

            cursor.execute(
                """
                INSERT OR REPLACE INTO transactions 
                (date, stock, action, quantity, price, total, fees, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    row["Date"],
                    row["Stock"],
                    row["Action"].lower(),
                    int(row["Quantity"]),
                    float(row["Price"]),
                    total_value,
                    fees,
                    row["Status"],
                ),
            )

        conn.commit()
        conn.close()
        print(f"Imported {len(list(csv.DictReader(lines)))} transactions")

    def get_current_price_eodhd(
        self, stock_symbol: str, api_key: str = "demo", force: bool = False
    ) -> Optional[float]:
        """Get current price from EODHD API"""
        if not force and self.api_calls_today >= 20:
            print(
                f"⚠️  API limit reached for today ({self.api_calls_today}/20). Using stored prices."
            )
            return None

        # Reset daily counter if new day
        if datetime.now().date() > self.last_api_reset:
            self.api_calls_today = 0
            self.last_api_reset = datetime.now().date()

        # Try real-time API first
        try:
            url = f"https://eodhd.com/api/real-time/{stock_symbol}.AU"
            params = {"api_token": api_key, "fmt": "json"}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            self.api_calls_today += 1

            if "close" in data:
                close_price = data["close"]
                # Handle 'NA' values from API
                if close_price == "NA" or close_price is None:
                    print(f"No real-time data for {stock_symbol}, trying EOD data...")
                    return self.get_eod_price_eodhd(stock_symbol, api_key)

                try:
                    price = float(close_price)
                    self.store_price_history(stock_symbol, price, "eodhd_realtime")
                    print(f"✅ {stock_symbol}: ${price:.4f} (real-time)")
                    return price
                except (ValueError, TypeError):
                    print(f"Invalid price format for {stock_symbol}: {close_price}")
                    return self.get_eod_price_eodhd(stock_symbol, api_key)

        except Exception as e:
            print(f"Real-time API error for {stock_symbol}: {e}")
            return self.get_eod_price_eodhd(stock_symbol, api_key)

        return None

    def get_eod_price_eodhd(
        self, stock_symbol: str, api_key: str = "demo"
    ) -> Optional[float]:
        """Get end-of-day price from EODHD API as fallback"""
        try:
            # Try end-of-day data for the last trading day
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            url = f"https://eodhd.com/api/eod/{stock_symbol}.AU"
            params = {
                "api_token": api_key,
                "fmt": "json",
                "from": yesterday,
                "to": yesterday,
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            self.api_calls_today += 1

            if data and len(data) > 0 and "close" in data[0]:
                close_price = data[0]["close"]
                if close_price != "NA" and close_price is not None:
                    try:
                        price = float(close_price)
                        self.store_price_history(stock_symbol, price, "eodhd_eod")
                        print(f"✅ {stock_symbol}: ${price:.4f} (EOD)")
                        return price
                    except (ValueError, TypeError):
                        pass

            print(f"❌ No valid EOD data for {stock_symbol}")

        except Exception as e:
            print(f"EOD API error for {stock_symbol}: {e}")

        return None

    def get_fallback_price(self, stock_symbol: str) -> Optional[float]:
        """Get price from stored history as fallback"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT price FROM price_history 
            WHERE stock = ? 
            ORDER BY date DESC 
            LIMIT 1
        """,
            (stock_symbol,),
        )

        result = cursor.fetchone()
        conn.close()

        if result:
            return result[0]

        # If no stored price, try sample price for demo
        try:
            from sample_prices import get_sample_price

            sample_price = get_sample_price(stock_symbol)
            if sample_price > 0:
                self.store_price_history(stock_symbol, sample_price, "sample")
                return sample_price
        except ImportError:
            pass

        return None

    def store_price_history(self, stock: str, price: float, source: str):
        """Store price in history table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        today = datetime.now().strftime("%Y-%m-%d")

        cursor.execute(
            """
            INSERT OR REPLACE INTO price_history (stock, date, price, source)
            VALUES (?, ?, ?, ?)
        """,
            (stock, today, price, source),
        )

        conn.commit()
        conn.close()

    def get_positions(self) -> Dict[str, Position]:
        """Calculate current positions from transaction history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT stock, action, quantity, price, total, fees
            FROM transactions 
            WHERE status = 'executed'
            ORDER BY date ASC
        """
        )

        transactions = cursor.fetchall()
        conn.close()

        positions = {}

        for stock, action, quantity, price, total, fees in transactions:
            if stock not in positions:
                positions[stock] = {"quantity": 0, "total_cost": 0.0, "total_fees": 0.0}

            if action == "buy":
                positions[stock]["quantity"] += quantity
                positions[stock]["total_cost"] += total
                positions[stock]["total_fees"] += fees
            elif action == "sell":
                # Handle partial sells
                if positions[stock]["quantity"] > 0:
                    sell_ratio = quantity / positions[stock]["quantity"]
                    positions[stock]["quantity"] -= quantity
                    positions[stock]["total_cost"] *= 1 - sell_ratio
                    positions[stock]["total_fees"] += fees

        # Convert to Position objects
        result = {}
        for stock, data in positions.items():
            if data["quantity"] > 0:
                avg_cost = (data["total_cost"] + data["total_fees"]) / data["quantity"]
                result[stock] = Position(
                    stock=stock, quantity=int(data["quantity"]), avg_cost=avg_cost
                )

        return result

    def update_current_prices(
        self, api_key: str = "demo", use_api: bool = False, force: bool = False
    ):
        """Update current prices for all positions"""
        positions = self.get_positions()

        for stock in positions.keys():
            price: Optional[float]
            if use_api:
                # Check if we already have fresh data from today first (unless forced)
                stored_price = self.get_stored_price_today(stock) if not force else None
                if stored_price:
                    price = stored_price
                    print(f"📋 {stock}: ${price:.4f} (cached from today)")
                else:
                    price = self.get_current_price_eodhd(stock, api_key, force)
                    if price is None:
                        price = self.get_fallback_price(stock)
                    # Small delay to respect API limits
                    time.sleep(0.1)
            else:
                # Use fallback/sample prices by default
                price = self.get_fallback_price(stock)

            if price:
                positions[stock].current_price = price
                positions[stock].market_value = price * positions[stock].quantity
                cost_basis = positions[stock].avg_cost * positions[stock].quantity
                positions[stock].unrealized_pnl = (
                    positions[stock].market_value - cost_basis
                )

        return positions

    def get_stored_price_today(self, stock_symbol: str) -> Optional[float]:
        """Get price stored today to avoid duplicate API calls"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            """
            SELECT price FROM price_history 
            WHERE stock = ? AND date = ? AND source LIKE 'eodhd%'
            ORDER BY id DESC 
            LIMIT 1
        """,
            (stock_symbol, today),
        )

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

    def calculate_cash_balance(self) -> float:
        """Calculate cash balance from all transactions starting with initial cash"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT action, total, fees
            FROM transactions 
            WHERE status = 'executed'
            ORDER BY date ASC
        """
        )

        transactions = cursor.fetchall()

        # Get starting cash from user settings (fallback to instance variable for backward compatibility)
        cursor.execute(
            "SELECT starting_cash FROM user_settings ORDER BY id DESC LIMIT 1"
        )
        user_cash_result = cursor.fetchone()
        starting_cash = user_cash_result[0] if user_cash_result else self.starting_cash

        conn.close()

        # Start with initial cash balance
        cash_balance = starting_cash

        for action, total, fees in transactions:
            if action == "buy":
                # Subtract money spent (total + fees)
                cash_balance -= total + fees
            elif action == "sell":
                # Add money received (total - fees)
                cash_balance += total - fees

        return cash_balance

    def get_portfolio_summary(
        self, api_key: str = "demo", use_api: bool = False, force: bool = False
    ) -> Dict:
        """Get complete portfolio summary with franking analysis"""
        positions = self.update_current_prices(api_key, use_api, force)

        total_cost = sum(pos.avg_cost * pos.quantity for pos in positions.values())
        total_market_value = sum(pos.market_value for pos in positions.values())
        total_unrealized_pnl = total_market_value - total_cost

        # Calculate total fees paid
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT SUM(fees) FROM transactions WHERE status = "executed"')
        total_fees = cursor.fetchone()[0] or 0.0
        conn.close()

        # Calculate cash balance
        cash_balance = self.calculate_cash_balance()

        # Calculate total portfolio value (stocks + cash)
        total_portfolio_value = total_market_value + cash_balance

        # Basic portfolio summary
        summary = {
            "positions": positions,
            "total_cost": total_cost,
            "total_market_value": total_market_value,
            "total_unrealized_pnl": total_unrealized_pnl,
            "total_fees": total_fees,
            "cash_balance": cash_balance,
            "total_portfolio_value": total_portfolio_value,
            "return_percentage": (
                (total_unrealized_pnl / total_cost * 100) if total_cost > 0 else 0
            ),
            "api_calls_used": self.api_calls_today,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Add franking analysis if available
        if FRANKING_AVAILABLE and self.franking_calculator:
            try:
                franking_analysis = self.get_franking_summary()
                summary.update(
                    {
                        "franking_credits": franking_analysis.get(
                            "total_franking_credits", 0
                        ),
                        "tax_benefit": franking_analysis.get("tax_benefit", 0),
                        "franking_efficiency": franking_analysis.get(
                            "franking_efficiency", 0
                        ),
                        "effective_tax_rate": franking_analysis.get(
                            "effective_tax_rate", 0
                        ),
                    }
                )
            except Exception as e:
                print(f"Warning: Franking analysis failed: {e}")

        return summary

    def get_franking_summary(
        self, taxable_income: float = 85000, estimated_yield: float = 0.04
    ) -> Dict:
        """Get franking credit analysis for current portfolio"""
        if not FRANKING_AVAILABLE or not self.franking_calculator:
            return {
                "error": "Franking calculator not available",
                "total_franking_credits": 0,
                "tax_benefit": 0,
                "franking_efficiency": 0,
            }

        # Get positions with updated prices
        positions = self.update_current_prices(use_api=False)
        return self.franking_calculator.calculate_franking_benefit(
            positions, taxable_income, estimated_yield
        )

    def get_franking_optimization_suggestions(
        self, taxable_income: float = 85000
    ) -> List[Dict]:
        """Get suggestions for optimizing franking credits"""
        if not FRANKING_AVAILABLE or not self.franking_calculator:
            return []

        positions = self.get_positions()
        return self.franking_calculator.get_optimization_suggestions(
            positions, taxable_income
        )

    def get_stock_franking_info(self, stock: str) -> Dict:
        """Get franking information for a specific stock"""
        if not FRANKING_AVAILABLE or not self.franking_db:
            return {
                "franking_rate": 0,
                "sector": "Unknown",
                "reliability": "unavailable",
            }

        return self.franking_db.get_franking_info(stock)

    def save_tax_settings(self, settings: Dict):
        """Save tax settings to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO tax_settings 
            (tax_year, taxable_income, tax_bracket, medicare_levy, is_resident)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                settings.get("tax_year", "2024-25"),
                settings.get("taxable_income", 85000),
                settings.get("tax_bracket", 32.5),
                settings.get("medicare_levy", 2.0),
                settings.get("is_resident", True),
            ),
        )

        conn.commit()
        conn.close()

    def get_tax_settings(self) -> Dict:
        """Get latest tax settings from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT tax_year, taxable_income, tax_bracket, medicare_levy, is_resident
            FROM tax_settings 
            ORDER BY created_date DESC 
            LIMIT 1
        """
        )

        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                "tax_year": result[0],
                "taxable_income": result[1],
                "tax_bracket": result[2],
                "medicare_levy": result[3],
                "is_resident": bool(result[4]),
            }
        else:
            # Default settings
            return {
                "tax_year": "2024-25",
                "taxable_income": 85000,
                "tax_bracket": 32.5,
                "medicare_levy": 2.0,
                "is_resident": True,
            }

    def export_portfolio_csv(
        self, filename: Optional[str] = None, include_franking: bool = True
    ):
        """Export current portfolio to CSV with optional franking data"""
        if filename is None:
            filename = (
                f"portfolio_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )

        summary = self.get_portfolio_summary()

        with open(filename, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)

            # Headers
            headers = [
                "Stock",
                "Quantity",
                "Avg Cost",
                "Current Price",
                "Market Value",
                "Unrealized P&L",
                "P&L %",
            ]

            if include_franking and FRANKING_AVAILABLE:
                headers.extend(["Franking Rate", "Sector", "Effective Yield"])

            writer.writerow(headers)

            for pos in summary["positions"].values():
                pnl_pct = (
                    ((pos.current_price / pos.avg_cost - 1) * 100)
                    if pos.avg_cost > 0
                    else 0
                )
                row = [
                    pos.stock,
                    pos.quantity,
                    f"${pos.avg_cost:.4f}",
                    f"${pos.current_price:.4f}",
                    f"${pos.market_value:.2f}",
                    f"${pos.unrealized_pnl:.2f}",
                    f"{pnl_pct:.2f}%",
                ]

                if include_franking and FRANKING_AVAILABLE:
                    franking_info = self.get_stock_franking_info(pos.stock)
                    effective_yield = (
                        pos.market_value
                        * 0.04
                        * (1 + franking_info["franking_rate"] / 100 * 0.3)
                        / pos.market_value
                        * 100
                        if pos.market_value > 0
                        else 0
                    )
                    row.extend(
                        [
                            f"{franking_info['franking_rate']:.0f}%",
                            franking_info["sector"],
                            f"{effective_yield:.2f}%",
                        ]
                    )

                writer.writerow(row)

        print(f"Portfolio exported to {filename}")
        return filename

    def is_new_user(self) -> bool:
        """Check if this is a new user (no setup completed)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if user_settings table has any records with setup_completed=1
        cursor.execute(
            "SELECT setup_completed FROM user_settings WHERE setup_completed = 1 LIMIT 1"
        )
        result = cursor.fetchone()
        conn.close()

        return result is None

    def has_any_data(self) -> bool:
        """Check if there's any existing portfolio data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check for any transactions
        cursor.execute("SELECT COUNT(*) FROM transactions")
        transaction_count = cursor.fetchone()[0]

        conn.close()
        return transaction_count > 0

    def initialize_user_settings(
        self, starting_cash: float = 25000.0, portfolio_name: str = "My Portfolio"
    ):
        """Initialize user settings for a new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Insert initial user settings
        cursor.execute(
            """
            INSERT INTO user_settings (setup_completed, starting_cash, portfolio_name)
            VALUES (1, ?, ?)
        """,
            (starting_cash, portfolio_name),
        )

        # Update the instance starting_cash to match
        self.starting_cash = starting_cash

        conn.commit()
        conn.close()

    def get_user_settings(self) -> Dict:
        """Get current user settings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT setup_completed, starting_cash, portfolio_name, created_date FROM user_settings ORDER BY id DESC LIMIT 1"
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                "setup_completed": bool(result[0]),
                "starting_cash": result[1],
                "portfolio_name": result[2],
                "created_date": result[3],
            }
        else:
            # Return defaults for backward compatibility
            return {
                "setup_completed": False,
                "starting_cash": 25000.0,
                "portfolio_name": "My Portfolio",
                "created_date": None,
            }


def main():
    """Example usage with franking analysis"""
    tracker = ASXPortfolioTracker()

    # Sample transaction data from user
    csv_data = """Date,Stock,Action,Quantity,Price,Total,Status
2025-07-10,WAX,buy,872,1.175,1044.5500000000002,executed
2025-07-10,WAM,buy,910,1.63,1503.25,executed
2025-07-10,HLI,buy,349,4.97,1754.48,executed
2025-07-10,YMAX,buy,260,7.69,2019.3500000000001,executed
2025-07-10,WOW,buy,40,31.16,1266.3500000000001,executed
2025-07-10,CBA,buy,8,180.37,1462.91,executed
2025-07-10,CSL,buy,8,242.41,1959.23,executed
2025-07-10,LNW,buy,13,152.16,1998.03,executed
2025-07-10,DTR,buy,16580,0.089,1495.57,executed
2025-07-10,SDR,buy,562,4.44,2515.23,executed
2025-07-10,BHP,buy,65,38.3,2509.45,executed
2025-07-10,NXT,buy,192,13.59,2629.2299999999996,executed
2025-07-10,XRO,buy,16,176.33,2841.23,executed"""

    # Import transactions
    tracker.import_transactions_from_csv(csv_data)

    # Get portfolio summary with franking analysis
    print("=== ASX Portfolio Summary ===")
    summary = tracker.get_portfolio_summary(
        use_api=False
    )  # Use sample prices by default

    print(f"Total Cost Basis: ${summary['total_cost']:.2f}")
    print(f"Current Market Value: ${summary['total_market_value']:.2f}")
    print(f"Unrealized P&L: ${summary['total_unrealized_pnl']:.2f}")
    print(f"Return: {summary['return_percentage']:.2f}%")
    print(f"Total Fees Paid: ${summary['total_fees']:.2f}")
    print(f"Cash Balance: ${summary['cash_balance']:.2f}")
    print(f"API Calls Used Today: {summary['api_calls_used']}/20")
    print(f"Last Updated: {summary['last_updated']}")

    # Franking analysis
    if FRANKING_AVAILABLE:
        print(f"\n=== Franking Credit Analysis ===")
        print(f"Annual Franking Credits: ${summary.get('franking_credits', 0):.2f}")
        print(f"Tax Benefit: ${summary.get('tax_benefit', 0):.2f}")
        print(f"Franking Efficiency: {summary.get('franking_efficiency', 0):.1f}%")
        print(f"Effective Tax Rate: {summary.get('effective_tax_rate', 0):.1f}%")

        # Get detailed franking analysis
        franking_details = tracker.get_franking_summary()
        if "stock_details" in franking_details:
            print(f"\n=== Stock-by-Stock Franking Analysis ===")
            for stock in franking_details["stock_details"]:
                print(
                    f"{stock['stock']}: {stock['franking_rate']:.0f}% franked, "
                    f"${stock['franking_credit']:.2f} annual credits, "
                    f"{stock['effective_yield']:.2f}% effective yield"
                )

    print("\n=== Individual Positions ===")
    for pos in summary["positions"].values():
        pnl_pct = (
            ((pos.current_price / pos.avg_cost - 1) * 100) if pos.avg_cost > 0 else 0
        )
        franking_info = tracker.get_stock_franking_info(pos.stock)
        print(
            f"{pos.stock}: {pos.quantity} shares @ ${pos.avg_cost:.4f} "
            f"| Current: ${pos.current_price:.4f} | P&L: ${pos.unrealized_pnl:.2f} ({pnl_pct:.2f}%) "
            f"| Franking: {franking_info['franking_rate']:.0f}%"
        )


if __name__ == "__main__":
    main()
