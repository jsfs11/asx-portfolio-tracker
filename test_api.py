#!/usr/bin/env python3
"""
Test EODHD API with correct AU symbol format
"""

import requests
from config import EODHD_API_KEY

def test_stock_price(symbol, api_key):
    """Test fetching price for a single stock"""
    print(f"Testing {symbol} with API key: {api_key[:10]}...")
    
    # Test real-time API
    try:
        url = f"https://eodhd.com/api/real-time/{symbol}.AU"
        params = {'api_token': api_key, 'fmt': 'json'}
        
        response = requests.get(url, params=params, timeout=10)
        print(f"Real-time API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Real-time data: {data}")
            if 'close' in data and data['close'] != 'NA':
                print(f"✅ {symbol}: ${data['close']} (real-time)")
                return float(data['close'])
        else:
            print(f"Real-time API error: {response.text}")
            
    except Exception as e:
        print(f"Real-time API exception: {e}")
    
    # Test EOD API
    try:
        from datetime import datetime, timedelta
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        url = f"https://eodhd.com/api/eod/{symbol}.AU"
        params = {
            'api_token': api_key, 
            'fmt': 'json',
            'from': yesterday,
            'to': yesterday
        }
        
        response = requests.get(url, params=params, timeout=10)
        print(f"EOD API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"EOD data: {data}")
            if data and len(data) > 0 and 'close' in data[0]:
                print(f"✅ {symbol}: ${data[0]['close']} (EOD)")
                return float(data[0]['close'])
        else:
            print(f"EOD API error: {response.text}")
            
    except Exception as e:
        print(f"EOD API exception: {e}")
    
    return None

if __name__ == "__main__":
    # Test with a few major ASX stocks
    test_stocks = ['CBA', 'BHP', 'WOW']
    
    for stock in test_stocks:
        print(f"\n{'='*50}")
        result = test_stock_price(stock, EODHD_API_KEY)
        if result:
            break  # Stop after first successful test to save API calls