#!/usr/bin/env python3
"""
OHLC Data Collector for ASX Portfolio Tracker
Completely separate module that enhances existing functionality without breaking it
"""

import sqlite3
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OHLCData:
    """Open, High, Low, Close data structure"""
    stock: str
    date: str
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    source: str

@dataclass
class OptimalPricing:
    """Optimal pricing analysis for a trading day"""
    stock: str
    date: str
    actual_close: float
    optimal_buy_price: float    # Lowest price of day
    optimal_sell_price: float   # Highest price of day
    vwap: float                 # Volume Weighted Average Price
    price_range_pct: float      # (High - Low) / Close * 100
    missed_opportunity_buy: float   # Close - Low
    missed_opportunity_sell: float  # High - Close


class OHLCCollector:
    """
    Standalone OHLC data collector that doesn't interfere with existing portfolio tracking
    """
    
    def __init__(self, db_path: str = 'portfolio.db'):
        self.db_path = db_path
        self.setup_ohlc_tables()
    
    def setup_ohlc_tables(self) -> bool:
        """Create OHLC tables if they don't exist (safe - doesn't modify existing tables)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # OHLC data storage
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_ohlc (
                    stock TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open_price REAL NOT NULL,
                    high_price REAL NOT NULL,
                    low_price REAL NOT NULL,
                    close_price REAL NOT NULL,
                    volume INTEGER DEFAULT 0,
                    source TEXT DEFAULT 'unknown',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (stock, date)
                )
            ''')
            
            # Optimal pricing analysis
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS optimal_pricing_analysis (
                    stock TEXT NOT NULL,
                    date TEXT NOT NULL,
                    actual_close REAL NOT NULL,
                    optimal_buy_price REAL NOT NULL,
                    optimal_sell_price REAL NOT NULL,
                    vwap REAL,
                    price_range_pct REAL,
                    missed_opportunity_buy REAL,
                    missed_opportunity_sell REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (stock, date)
                )
            ''')
            
            # Feature configuration
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ohlc_config (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Set default configuration
            cursor.execute('INSERT OR IGNORE INTO ohlc_config (key, value) VALUES (?, ?)',
                          ('enabled', 'true'))
            cursor.execute('INSERT OR IGNORE INTO ohlc_config (key, value) VALUES (?, ?)',
                          ('retention_days', '90'))
            cursor.execute('INSERT OR IGNORE INTO ohlc_config (key, value) VALUES (?, ?)',
                          ('auto_collect', 'false'))
            
            conn.commit()
            conn.close()
            
            logger.info("✅ OHLC tables initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup OHLC tables: {e}")
            return False
    
    def is_enabled(self) -> bool:
        """Check if OHLC collection is enabled"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM ohlc_config WHERE key = ?', ('enabled',))
            result = cursor.fetchone()
            conn.close()
            return result and result[0].lower() == 'true'
        except:
            return False
    
    def fetch_ohlc_eodhd(self, stock: str, api_key: str, date: str = None) -> Optional[OHLCData]:
        """Fetch OHLC data from EODHD API"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            url = f"https://eodhd.com/api/eod/{stock}.AX"
            params = {
                'api_token': api_key,
                'fmt': 'json',
                'from': date,
                'to': date
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    day_data = data[0]
                    return OHLCData(
                        stock=stock,
                        date=date,
                        open_price=float(day_data.get('open', 0)),
                        high_price=float(day_data.get('high', 0)),
                        low_price=float(day_data.get('low', 0)),
                        close_price=float(day_data.get('close', 0)),
                        volume=int(day_data.get('volume', 0)),
                        source='eodhd'
                    )
            
            logger.warning(f"⚠️  No EODHD OHLC data for {stock} on {date}")
            return None
            
        except Exception as e:
            logger.error(f"❌ EODHD OHLC fetch failed for {stock}: {e}")
            return None
    
    def fetch_historical_ohlc_eodhd(self, stock: str, api_key: str, from_date: str, to_date: str = None) -> List[OHLCData]:
        """Fetch historical OHLC data from EODHD API for date range"""
        if not to_date:
            to_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            url = f"https://eodhd.com/api/eod/{stock}.AX"
            params = {
                'api_token': api_key,
                'fmt': 'json',
                'from': from_date,
                'to': to_date
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                ohlc_list = []
                for day_data in data:
                    ohlc_list.append(OHLCData(
                        stock=stock,
                        date=day_data.get('date'),
                        open_price=float(day_data.get('open', 0)),
                        high_price=float(day_data.get('high', 0)),
                        low_price=float(day_data.get('low', 0)),
                        close_price=float(day_data.get('close', 0)),
                        volume=int(day_data.get('volume', 0)),
                        source='eodhd'
                    ))
                
                logger.info(f"✅ Fetched {len(ohlc_list)} historical OHLC records for {stock}")
                return ohlc_list
            
            logger.warning(f"⚠️  No historical EODHD data for {stock} from {from_date} to {to_date}")
            return []
            
        except Exception as e:
            logger.error(f"❌ Historical EODHD fetch failed for {stock}: {e}")
            return []
    
    def fetch_ohlc_yfinance(self, stock: str, date: str = None) -> Optional[OHLCData]:
        """Fetch OHLC data from Yahoo Finance (fallback)"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            ticker = f"{stock}.AX"
            yf_stock = yf.Ticker(ticker)
            
            # Get data for the specific date
            start_date = date
            end_date = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
            
            hist = yf_stock.history(start=start_date, end=end_date)
            
            if not hist.empty:
                day_data = hist.iloc[0]
                return OHLCData(
                    stock=stock,
                    date=date,
                    open_price=float(day_data['Open']),
                    high_price=float(day_data['High']),
                    low_price=float(day_data['Low']),
                    close_price=float(day_data['Close']),
                    volume=int(day_data['Volume']),
                    source='yfinance'
                )
            
            logger.warning(f"⚠️  No Yahoo Finance OHLC data for {stock} on {date}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Yahoo Finance OHLC fetch failed for {stock}: {e}")
            return None
    
    def fetch_historical_ohlc_yfinance(self, stock: str, from_date: str, to_date: str = None, period: str = None) -> List[OHLCData]:
        """Fetch historical OHLC data from Yahoo Finance for date range"""
        if not to_date and not period:
            to_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            ticker = f"{stock}.AX"
            yf_stock = yf.Ticker(ticker)
            
            if period:
                # Use period-based fetching (more reliable)
                hist = yf_stock.history(period=period)
            else:
                # Use date range
                hist = yf_stock.history(start=from_date, end=to_date)
            
            if hist.empty:
                logger.warning(f"⚠️  No historical Yahoo Finance data for {stock}")
                return []
            
            ohlc_list = []
            for date_idx, day_data in hist.iterrows():
                date_str = date_idx.strftime('%Y-%m-%d')
                ohlc_list.append(OHLCData(
                    stock=stock,
                    date=date_str,
                    open_price=float(day_data['Open']),
                    high_price=float(day_data['High']),
                    low_price=float(day_data['Low']),
                    close_price=float(day_data['Close']),
                    volume=int(day_data['Volume']),
                    source='yfinance'
                ))
            
            logger.info(f"✅ Fetched {len(ohlc_list)} historical OHLC records for {stock} from Yahoo Finance")
            return ohlc_list
            
        except Exception as e:
            logger.error(f"❌ Historical Yahoo Finance fetch failed for {stock}: {e}")
            return []
    
    def store_ohlc_data(self, ohlc: OHLCData) -> bool:
        """Store OHLC data in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO daily_ohlc 
                (stock, date, open_price, high_price, low_price, close_price, volume, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                ohlc.stock, ohlc.date, ohlc.open_price, ohlc.high_price,
                ohlc.low_price, ohlc.close_price, ohlc.volume, ohlc.source
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Stored OHLC data for {ohlc.stock} on {ohlc.date}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to store OHLC data: {e}")
            return False
    
    def calculate_optimal_pricing(self, ohlc: OHLCData) -> OptimalPricing:
        """Calculate optimal pricing analysis from OHLC data"""
        
        # Calculate VWAP (simplified - would need intraday data for true VWAP)
        # Using approximation: (High + Low + Close) / 3
        vwap = (ohlc.high_price + ohlc.low_price + ohlc.close_price) / 3
        
        # Price range as percentage of close
        price_range_pct = ((ohlc.high_price - ohlc.low_price) / ohlc.close_price) * 100
        
        # Missed opportunities
        missed_buy = ohlc.close_price - ohlc.low_price    # Could have bought cheaper
        missed_sell = ohlc.high_price - ohlc.close_price  # Could have sold higher
        
        return OptimalPricing(
            stock=ohlc.stock,
            date=ohlc.date,
            actual_close=ohlc.close_price,
            optimal_buy_price=ohlc.low_price,
            optimal_sell_price=ohlc.high_price,
            vwap=vwap,
            price_range_pct=price_range_pct,
            missed_opportunity_buy=missed_buy,
            missed_opportunity_sell=missed_sell
        )
    
    def store_optimal_pricing(self, optimal: OptimalPricing) -> bool:
        """Store optimal pricing analysis"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO optimal_pricing_analysis
                (stock, date, actual_close, optimal_buy_price, optimal_sell_price, 
                 vwap, price_range_pct, missed_opportunity_buy, missed_opportunity_sell)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                optimal.stock, optimal.date, optimal.actual_close,
                optimal.optimal_buy_price, optimal.optimal_sell_price,
                optimal.vwap, optimal.price_range_pct,
                optimal.missed_opportunity_buy, optimal.missed_opportunity_sell
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to store optimal pricing: {e}")
            return False
    
    def collect_stock_ohlc(self, stock: str, api_key: str = "demo", date: str = None, prefer_yfinance: bool = True) -> bool:
        """Collect OHLC data for a single stock"""
        if not self.is_enabled():
            logger.info("OHLC collection is disabled")
            return False
        
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"🔄 Collecting OHLC data for {stock} on {date}")
        
        if prefer_yfinance:
            # Try Yahoo Finance first (unlimited API calls)
            ohlc_data = self.fetch_ohlc_yfinance(stock, date)
            
            # Fallback to EODHD if Yahoo Finance fails
            if not ohlc_data and api_key != "demo":
                logger.info(f"⚠️  Yahoo Finance failed for {stock}, trying EODHD...")
                ohlc_data = self.fetch_ohlc_eodhd(stock, api_key, date)
        else:
            # Original order: EODHD first, then Yahoo Finance
            ohlc_data = self.fetch_ohlc_eodhd(stock, api_key, date)
            
            if not ohlc_data:
                ohlc_data = self.fetch_ohlc_yfinance(stock, date)
        
        if ohlc_data:
            # Store OHLC data
            if self.store_ohlc_data(ohlc_data):
                # Calculate and store optimal pricing analysis
                optimal = self.calculate_optimal_pricing(ohlc_data)
                self.store_optimal_pricing(optimal)
                
                logger.info(f"📊 {stock}: Open=${ohlc_data.open_price:.3f}, "
                           f"High=${ohlc_data.high_price:.3f}, "
                           f"Low=${ohlc_data.low_price:.3f}, "
                           f"Close=${ohlc_data.close_price:.3f}")
                
                return True
        
        logger.warning(f"❌ No OHLC data collected for {stock}")
        return False
    
    def collect_portfolio_ohlc(self, stocks: List[str], api_key: str = "demo", date: str = None, prefer_yfinance: bool = True) -> Dict[str, bool]:
        """Collect OHLC data for multiple stocks"""
        results = {}
        eodhd_calls_used = 0
        
        logger.info(f"🔄 Starting OHLC collection for {len(stocks)} stocks (Priority: {'Yahoo Finance' if prefer_yfinance else 'EODHD'})")
        
        for stock in stocks:
            results[stock] = self.collect_stock_ohlc(stock, api_key, date, prefer_yfinance)
            
            # Track EODHD usage for reporting
            if not prefer_yfinance or (prefer_yfinance and not results[stock]):
                eodhd_calls_used += 1
        
        successful = sum(1 for success in results.values() if success)
        
        if prefer_yfinance:
            logger.info(f"📈 OHLC collection complete: {successful}/{len(stocks)} successful")
            logger.info(f"💡 EODHD API calls saved: {len(stocks) - eodhd_calls_used}/20 (Yahoo Finance primary)")
        else:
            logger.info(f"📈 OHLC collection complete: {successful}/{len(stocks)} successful (EODHD primary)")
        
        return results
    
    def get_portfolio_stocks_from_db(self) -> List[str]:
        """Get list of stocks from existing portfolio (safe read-only operation)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT DISTINCT stock FROM transactions ORDER BY stock')
            stocks = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return stocks
            
        except Exception as e:
            logger.error(f"❌ Failed to get portfolio stocks: {e}")
            return []
    
    def get_ohlc_data(self, stock: str, days: int = 30) -> List[OHLCData]:
        """Retrieve stored OHLC data for analysis"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT stock, date, open_price, high_price, low_price, close_price, volume, source
                FROM daily_ohlc
                WHERE stock = ? 
                ORDER BY date DESC
                LIMIT ?
            ''', (stock, days))
            
            results = []
            for row in cursor.fetchall():
                results.append(OHLCData(
                    stock=row[0], date=row[1], open_price=row[2],
                    high_price=row[3], low_price=row[4], close_price=row[5],
                    volume=row[6], source=row[7]
                ))
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve OHLC data: {e}")
            return []
    
    def get_optimal_pricing_analysis(self, stock: str, days: int = 30) -> List[OptimalPricing]:
        """Retrieve optimal pricing analysis"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT stock, date, actual_close, optimal_buy_price, optimal_sell_price,
                       vwap, price_range_pct, missed_opportunity_buy, missed_opportunity_sell
                FROM optimal_pricing_analysis
                WHERE stock = ?
                ORDER BY date DESC
                LIMIT ?
            ''', (stock, days))
            
            results = []
            for row in cursor.fetchall():
                results.append(OptimalPricing(
                    stock=row[0], date=row[1], actual_close=row[2],
                    optimal_buy_price=row[3], optimal_sell_price=row[4],
                    vwap=row[5], price_range_pct=row[6],
                    missed_opportunity_buy=row[7], missed_opportunity_sell=row[8]
                ))
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve optimal pricing analysis: {e}")
            return []
    
    def collect_historical_data(self, stock: str, days: int = 30, api_key: str = "demo", prefer_yfinance: bool = True) -> int:
        """Collect historical OHLC data for a stock"""
        
        if not self.is_enabled():
            logger.info("OHLC collection is disabled")
            return 0
        
        from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"🔄 Collecting {days} days of historical OHLC data for {stock}")
        
        if prefer_yfinance:
            # Use Yahoo Finance periods for efficiency
            if days <= 7:
                period = "7d"
            elif days <= 30:
                period = "1mo"
            elif days <= 90:
                period = "3mo"
            elif days <= 180:
                period = "6mo"
            else:
                period = "1y"
            
            ohlc_list = self.fetch_historical_ohlc_yfinance(stock, from_date, to_date, period=period)
            
            # Fallback to EODHD if Yahoo Finance fails
            if not ohlc_list and api_key != "demo":
                logger.info(f"⚠️  Yahoo Finance failed for {stock}, trying EODHD...")
                ohlc_list = self.fetch_historical_ohlc_eodhd(stock, api_key, from_date, to_date)
        
        else:
            # EODHD first
            ohlc_list = self.fetch_historical_ohlc_eodhd(stock, api_key, from_date, to_date)
            
            if not ohlc_list:
                ohlc_list = self.fetch_historical_ohlc_yfinance(stock, from_date, to_date)
        
        # Store all data and calculate optimal pricing
        stored_count = 0
        for ohlc in ohlc_list:
            if self.store_ohlc_data(ohlc):
                optimal = self.calculate_optimal_pricing(ohlc)
                self.store_optimal_pricing(optimal)
                stored_count += 1
        
        logger.info(f"✅ Stored {stored_count}/{len(ohlc_list)} historical records for {stock}")
        return stored_count
    
    def collect_portfolio_historical_data(self, days: int = 30, api_key: str = "demo", prefer_yfinance: bool = True) -> Dict[str, int]:
        """Collect historical OHLC data for entire portfolio"""
        
        stocks = self.get_portfolio_stocks_from_db()
        if not stocks:
            logger.warning("No portfolio stocks found")
            return {}
        
        logger.info(f"🔄 Collecting {days} days of historical data for {len(stocks)} stocks")
        
        results = {}
        total_records = 0
        
        for stock in stocks:
            try:
                count = self.collect_historical_data(stock, days, api_key, prefer_yfinance)
                results[stock] = count
                total_records += count
            except Exception as e:
                logger.error(f"❌ Failed to collect historical data for {stock}: {e}")
                results[stock] = 0
        
        successful_stocks = [s for s, c in results.items() if c > 0]
        logger.info(f"🎉 Historical collection complete: {len(successful_stocks)}/{len(stocks)} stocks, {total_records} total records")
        
        return results
    
    def get_missing_dates(self, stock: str, days: int = 30) -> List[str]:
        """Get list of dates where OHLC data is missing for a stock"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get existing dates
            cursor.execute(
                'SELECT DISTINCT date FROM daily_ohlc WHERE stock = ? ORDER BY date',
                (stock,)
            )
            existing_dates = set(row[0] for row in cursor.fetchall())
            conn.close()
            
            # Generate expected date range (excluding weekends)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            expected_dates = []
            current_date = start_date
            
            while current_date <= end_date:
                # Skip weekends (ASX closed Saturday=5, Sunday=6)
                if current_date.weekday() < 5:
                    date_str = current_date.strftime('%Y-%m-%d')
                    if date_str not in existing_dates:
                        expected_dates.append(date_str)
                current_date += timedelta(days=1)
            
            return expected_dates
            
        except Exception as e:
            logger.error(f"❌ Error checking missing dates for {stock}: {e}")
            return []
    
    def fill_missing_data(self, api_key: str = "demo", prefer_yfinance: bool = True) -> Dict[str, int]:
        """Fill in missing OHLC data for all portfolio stocks"""
        
        stocks = self.get_portfolio_stocks_from_db()
        results = {}
        total_filled = 0
        
        logger.info(f"🔍 Checking for missing OHLC data across {len(stocks)} stocks")
        
        for stock in stocks:
            missing_dates = self.get_missing_dates(stock, 30)  # Check last 30 days
            
            if missing_dates:
                logger.info(f"📥 Filling {len(missing_dates)} missing dates for {stock}")
                filled_count = 0
                
                for date in missing_dates:
                    try:
                        success = self.collect_stock_ohlc(stock, api_key, date, prefer_yfinance)
                        if success:
                            filled_count += 1
                    except Exception as e:
                        logger.error(f"❌ Failed to fill {stock} on {date}: {e}")
                
                results[stock] = filled_count
                total_filled += filled_count
                
                if filled_count > 0:
                    logger.info(f"✅ Filled {filled_count}/{len(missing_dates)} missing dates for {stock}")
            else:
                results[stock] = 0
        
        logger.info(f"🎉 Gap filling complete: {total_filled} missing records filled")
        return results
    
    def cleanup_old_data(self, retention_days: int = 90):
        """Clean up old OHLC data to prevent database bloat"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=retention_days)).strftime('%Y-%m-%d')
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM daily_ohlc WHERE date < ?', (cutoff_date,))
            ohlc_deleted = cursor.rowcount
            
            cursor.execute('DELETE FROM optimal_pricing_analysis WHERE date < ?', (cutoff_date,))
            analysis_deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.info(f"🧹 Cleaned up {ohlc_deleted} OHLC records and {analysis_deleted} analysis records older than {retention_days} days")
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")


def main():
    """Standalone OHLC collection for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='OHLC Data Collector for ASX Portfolio Tracker')
    parser.add_argument('--stock', '-s', help='Collect OHLC for specific stock')
    parser.add_argument('--all', '-a', action='store_true', help='Collect OHLC for all portfolio stocks')
    parser.add_argument('--api-key', default='demo', help='EODHD API key')
    parser.add_argument('--date', help='Specific date (YYYY-MM-DD)')
    parser.add_argument('--enable', action='store_true', help='Enable OHLC collection')
    parser.add_argument('--disable', action='store_true', help='Disable OHLC collection')
    parser.add_argument('--status', action='store_true', help='Show OHLC collection status')
    parser.add_argument('--prefer-eodhd', action='store_true', help='Use EODHD as primary (default: Yahoo Finance primary)')
    parser.add_argument('--save-api-calls', action='store_true', help='Use Yahoo Finance only (save all EODHD calls)')
    
    # Historical data collection
    parser.add_argument('--historical', '-H', type=int, metavar='DAYS', help='Collect historical OHLC data for N days')
    parser.add_argument('--fill-gaps', action='store_true', help='Fill missing OHLC data gaps')
    parser.add_argument('--cleanup', type=int, metavar='DAYS', help='Clean up OHLC data older than N days')
    
    args = parser.parse_args()
    
    collector = OHLCCollector()
    
    if args.enable:
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE ohlc_config SET value = ? WHERE key = ?', ('true', 'enabled'))
        conn.commit()
        conn.close()
        print("✅ OHLC collection enabled")
        return
    
    if args.disable:
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE ohlc_config SET value = ? WHERE key = ?', ('false', 'enabled'))
        conn.commit()
        conn.close()
        print("❌ OHLC collection disabled")
        return
    
    if args.status:
        enabled = collector.is_enabled()
        print(f"OHLC Collection Status: {'✅ Enabled' if enabled else '❌ Disabled'}")
        return
    
    # Determine API priority
    if args.save_api_calls:
        prefer_yfinance = True
        print("💡 API Saver Mode: Using Yahoo Finance exclusively")
    elif args.prefer_eodhd:
        prefer_yfinance = False
        print("🔄 Using EODHD as primary data source")
    else:
        prefer_yfinance = True
        print("📊 Using Yahoo Finance as primary (saves EODHD API calls)")
    
    if args.stock:
        if args.save_api_calls:
            # Yahoo Finance only mode
            success = collector.collect_stock_ohlc(args.stock.upper(), "demo", args.date, prefer_yfinance=True)
        else:
            success = collector.collect_stock_ohlc(args.stock.upper(), args.api_key, args.date, prefer_yfinance)
        
        if success:
            print(f"✅ OHLC data collected for {args.stock}")
        else:
            print(f"❌ Failed to collect OHLC data for {args.stock}")
    
    elif args.all:
        stocks = collector.get_portfolio_stocks_from_db()
        if stocks:
            print(f"🔄 Collecting OHLC data for {len(stocks)} portfolio stocks...")
            
            if args.save_api_calls:
                # Yahoo Finance only mode
                results = collector.collect_portfolio_ohlc(stocks, "demo", args.date, prefer_yfinance=True)
            else:
                results = collector.collect_portfolio_ohlc(stocks, args.api_key, args.date, prefer_yfinance)
            
            successful = [stock for stock, success in results.items() if success]
            failed = [stock for stock, success in results.items() if not success]
            
            print(f"✅ Success: {', '.join(successful)}")
            if failed:
                print(f"❌ Failed: {', '.join(failed)}")
        else:
            print("❌ No portfolio stocks found")
    
    elif args.historical:
        days = args.historical
        print(f"🔄 Collecting {days} days of historical OHLC data...")
        
        if args.stock:
            # Single stock historical collection
            count = collector.collect_historical_data(
                args.stock.upper(), days, args.api_key, prefer_yfinance=prefer_yfinance
            )
            print(f"✅ Collected {count} historical records for {args.stock}")
        else:
            # Portfolio-wide historical collection
            results = collector.collect_portfolio_historical_data(
                days, args.api_key, prefer_yfinance=prefer_yfinance
            )
            
            successful = [stock for stock, count in results.items() if count > 0]
            total_records = sum(results.values())
            
            print(f"✅ Historical collection complete:")
            print(f"   Stocks: {len(successful)}/{len(results)}")
            print(f"   Records: {total_records}")
            
            if successful:
                print(f"   Success: {', '.join(successful)}")
    
    elif args.fill_gaps:
        print("🔍 Filling missing OHLC data gaps...")
        
        results = collector.fill_missing_data(args.api_key, prefer_yfinance=prefer_yfinance)
        
        filled_stocks = [stock for stock, count in results.items() if count > 0]
        total_filled = sum(results.values())
        
        if total_filled > 0:
            print(f"✅ Gap filling complete: {total_filled} records filled")
            print(f"   Stocks updated: {', '.join(filled_stocks)}")
        else:
            print("✅ No gaps found - all data is up to date")
    
    elif args.cleanup:
        days = args.cleanup
        print(f"🧹 Cleaning up OHLC data older than {days} days...")
        
        collector.cleanup_old_data(days)
        print("✅ Cleanup complete")
    
    else:
        print("Use --help for usage instructions")


if __name__ == "__main__":
    main()