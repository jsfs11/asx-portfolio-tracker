#!/usr/bin/env python3
"""
ASX Dividend Tracker Module
Tracks dividend payments and yields for portfolio positions
"""

import sqlite3
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Dividend:
    stock: str
    ex_date: str
    amount: float
    currency: str = 'AUD'
    record_date: str = None
    payment_date: str = None


class DividendTracker:
    def __init__(self, db_path: str = "portfolio.db"):
        self.db_path = db_path
        self.init_dividend_tables()
    
    def init_dividend_tables(self):
        """Initialize dividend-related database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enhanced dividends table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dividends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock TEXT NOT NULL,
                ex_date TEXT NOT NULL,
                record_date TEXT,
                payment_date TEXT,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'AUD',
                franking_credit REAL DEFAULT 0.0,
                type TEXT DEFAULT 'ordinary',
                UNIQUE(stock, ex_date)
            )
        ''')
        
        # Dividend payments received table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dividend_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock TEXT NOT NULL,
                payment_date TEXT NOT NULL,
                shares_held INTEGER NOT NULL,
                dividend_per_share REAL NOT NULL,
                total_payment REAL NOT NULL,
                franking_credits REAL DEFAULT 0.0,
                withholding_tax REAL DEFAULT 0.0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_dividend(self, stock: str, ex_date: str, amount: float):
        """Add a dividend record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO dividends 
            (stock, ex_date, amount, currency)
            VALUES (?, ?, ?, ?)
        ''', (stock, ex_date, amount, 'AUD'))
        
        conn.commit()
        conn.close()
        print(f"Added dividend: {stock} ${amount:.4f} ex-date {ex_date}")
    
    def get_stock_dividends(self, stock: str, from_date: str = None) -> List[Dividend]:
        """Get all dividends for a specific stock"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if from_date:
            cursor.execute('''
                SELECT stock, ex_date, amount, currency
                FROM dividends 
                WHERE stock = ? AND ex_date >= ?
                ORDER BY ex_date DESC
            ''', (stock, from_date))
        else:
            cursor.execute('''
                SELECT stock, ex_date, amount, currency
                FROM dividends 
                WHERE stock = ?
                ORDER BY ex_date DESC
            ''', (stock,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [Dividend(
            stock=row[0], ex_date=row[1], amount=row[2], currency=row[3]
        ) for row in results]
    
    def calculate_dividend_yield(self, stock: str, current_price: float, 
                               period_months: int = 12) -> float:
        """Calculate dividend yield over specified period"""
        from_date = (datetime.now() - timedelta(days=period_months * 30)).strftime('%Y-%m-%d')
        dividends = self.get_stock_dividends(stock, from_date)
        
        total_dividends = sum(div.amount for div in dividends)
        
        if current_price > 0:
            return (total_dividends / current_price) * 100
        return 0.0
    
    def calculate_portfolio_dividends(self, positions: Dict) -> Dict:
        """Calculate dividend information for entire portfolio"""
        results = {}
        
        for stock, position in positions.items():
            dividends = self.get_stock_dividends(stock)
            annual_yield = self.calculate_dividend_yield(stock, position.current_price)
            
            # Calculate expected annual dividends based on current holding
            annual_dividend_estimate = (annual_yield / 100) * position.current_price * position.quantity
            
            results[stock] = {
                'dividend_history': dividends,
                'annual_yield_percent': annual_yield,
                'estimated_annual_dividends': annual_dividend_estimate,
                'total_historical_dividends': sum(div.amount for div in dividends)
            }
        
        return results
    
    def record_dividend_payment(self, stock: str, payment_date: str, 
                              shares_held: int, dividend_per_share: float,
                              franking_credits: float = 0.0, withholding_tax: float = 0.0):
        """Record an actual dividend payment received"""
        total_payment = shares_held * dividend_per_share
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO dividend_payments 
            (stock, payment_date, shares_held, dividend_per_share, 
             total_payment, franking_credits, withholding_tax)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (stock, payment_date, shares_held, dividend_per_share, 
              total_payment, franking_credits, withholding_tax))
        
        conn.commit()
        conn.close()
        
        print(f"Recorded dividend payment: {stock} {shares_held} shares × ${dividend_per_share:.4f} = ${total_payment:.2f}")
    
    def get_total_dividends_received(self, from_date: str = None) -> float:
        """Get total dividends received in portfolio"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if from_date:
            cursor.execute('''
                SELECT SUM(total_payment) FROM dividend_payments 
                WHERE payment_date >= ?
            ''', (from_date,))
        else:
            cursor.execute('SELECT SUM(total_payment) FROM dividend_payments')
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result[0] else 0.0
    
    def fetch_dividend_data_eodhd(self, stock: str, api_key: str = "demo") -> List[Dividend]:
        """Fetch dividend data from EODHD API"""
        try:
            url = f"https://eodhd.com/api/div/{stock}.AX"
            params = {
                'api_token': api_key,
                'fmt': 'json',
                'from': (datetime.now() - timedelta(days=365*2)).strftime('%Y-%m-%d')  # 2 years
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            dividends = []
            
            for div_data in data:
                dividend = Dividend(
                    stock=stock,
                    ex_date=div_data.get('date', ''),
                    amount=float(div_data.get('value', 0)),
                    currency='AUD'
                )
                dividends.append(dividend)
                
                # Store in database
                self.add_dividend(
                    stock=stock,
                    ex_date=dividend.ex_date,
                    amount=dividend.amount
                )
            
            return dividends
            
        except Exception as e:
            print(f"Error fetching dividend data for {stock}: {e}")
            return []


# Example ASX dividend data for your stocks (you would need to verify/update these)
ASX_DIVIDEND_DATA = {
    'WAM': [
        {'ex_date': '2024-12-16', 'amount': 0.035, 'franking': 0.015},
        {'ex_date': '2024-06-17', 'amount': 0.035, 'franking': 0.015},
    ],
    'CBA': [
        {'ex_date': '2024-08-15', 'amount': 2.40, 'franking': 1.029},
        {'ex_date': '2024-02-15', 'amount': 2.40, 'franking': 1.029},
    ],
    'WOW': [
        {'ex_date': '2024-08-29', 'amount': 0.55, 'franking': 0.236},
        {'ex_date': '2024-02-29', 'amount': 0.55, 'franking': 0.236},
    ],
    'BHP': [
        {'ex_date': '2024-08-22', 'amount': 1.90, 'franking': 0.0},  # Unfranked
        {'ex_date': '2024-02-22', 'amount': 1.70, 'franking': 0.0},
    ],
    # Add more as needed - these would need to be verified with actual ASX data
}


def populate_sample_dividends(tracker: DividendTracker):
    """Populate database with sample dividend data"""
    for stock, dividends in ASX_DIVIDEND_DATA.items():
        for div in dividends:
            tracker.add_dividend(
                stock=stock,
                ex_date=div['ex_date'],
                amount=div['amount']
            )


if __name__ == "__main__":
    # Example usage
    tracker = DividendTracker()
    populate_sample_dividends(tracker)
    
    # Test dividend calculations
    cba_dividends = tracker.get_stock_dividends('CBA')
    print(f"CBA Dividends: {len(cba_dividends)} records")
    
    for div in cba_dividends:
        print(f"  {div.ex_date}: ${div.amount:.4f}")
    
    # Calculate yield (would need current price)
    cba_yield = tracker.calculate_dividend_yield('CBA', 180.0)  # Assume $180 current price
    print(f"CBA Estimated Annual Yield: {cba_yield:.2f}%")