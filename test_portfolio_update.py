#!/usr/bin/env python3
"""
Test portfolio update with limited stocks to avoid API limit
"""

from portfolio_tracker import ASXPortfolioTracker
from config import EODHD_API_KEY

def test_limited_update():
    tracker = ASXPortfolioTracker()
    
    # Test with just a few major stocks first
    test_stocks = ['CBA', 'BHP', 'WOW']
    
    for stock in test_stocks:
        print(f"\nTesting {stock}...")
        price = tracker.get_current_price_eodhd(stock, EODHD_API_KEY)
        if price:
            print(f"✅ {stock}: ${price:.4f}")
        else:
            # Try fallback
            fallback_price = tracker.get_fallback_price(stock)
            print(f"🔄 {stock}: ${fallback_price:.4f} (fallback)")

if __name__ == "__main__":
    test_limited_update()