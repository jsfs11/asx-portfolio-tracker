#!/usr/bin/env python3
"""
Portfolio Dashboard - Command line interface for ASX portfolio tracking
"""

import argparse
import sys
from datetime import datetime
from portfolio_tracker import ASXPortfolioTracker
from dividend_tracker import DividendTracker, populate_sample_dividends
from config import EODHD_API_KEY


def print_portfolio_summary(tracker: ASXPortfolioTracker, show_details: bool = False, use_api: bool = False, force_update: bool = False):
    """Print formatted portfolio summary"""
    summary = tracker.get_portfolio_summary(EODHD_API_KEY, use_api, force_update)
    
    print("=" * 60)
    print("           ASX PAPER TRADING PORTFOLIO")
    print("=" * 60)
    print(f"Last Updated: {summary['last_updated']}")
    print(f"API Calls Used Today: {summary['api_calls_used']}/20")
    print()
    
    print("PORTFOLIO OVERVIEW:")
    print(f"  Total Cost Basis:     ${summary['total_cost']:>12,.2f}")
    print(f"  Current Market Value: ${summary['total_market_value']:>12,.2f}")
    print(f"  Total Fees Paid:      ${summary['total_fees']:>12,.2f}")
    print(f"  Unrealized P&L:       ${summary['total_unrealized_pnl']:>12,.2f}")
    
    return_color = "📈" if summary['return_percentage'] >= 0 else "📉"
    print(f"  Total Return:         {summary['return_percentage']:>11.2f}% {return_color}")
    print()
    
    if show_details and summary['positions']:
        print("INDIVIDUAL POSITIONS:")
        print(f"{'Stock':<6} {'Qty':<6} {'Avg Cost':<10} {'Current':<10} {'Market Val':<12} {'P&L':<12} {'P&L %':<8}")
        print("-" * 70)
        
        for pos in summary['positions'].values():
            pnl_pct = ((pos.current_price / pos.avg_cost - 1) * 100) if pos.avg_cost > 0 else 0
            pnl_indicator = "🟢" if pos.unrealized_pnl >= 0 else "🔴"
            
            print(f"{pos.stock:<6} {pos.quantity:<6} ${pos.avg_cost:<9.4f} "
                  f"${pos.current_price:<9.4f} ${pos.market_value:<11.2f} "
                  f"${pos.unrealized_pnl:<11.2f} {pnl_pct:<7.2f}% {pnl_indicator}")


def print_dividend_summary(dividend_tracker: DividendTracker, positions: dict):
    """Print dividend information"""
    print("\nDIVIDEND ANALYSIS:")
    print("-" * 60)
    
    dividend_info = dividend_tracker.calculate_portfolio_dividends(positions)
    total_estimated_annual = 0
    
    for stock, info in dividend_info.items():
        if info['annual_yield_percent'] > 0:
            total_estimated_annual += info['estimated_annual_dividends']
            print(f"{stock:<6} Yield: {info['annual_yield_percent']:>5.2f}%  "
                  f"Est. Annual: ${info['estimated_annual_dividends']:>8.2f}")
    
    if total_estimated_annual > 0:
        print(f"\nTotal Estimated Annual Dividends: ${total_estimated_annual:.2f}")
        
        # Calculate portfolio yield
        total_market_value = sum(pos.market_value for pos in positions.values())
        if total_market_value > 0:
            portfolio_yield = (total_estimated_annual / total_market_value) * 100
            print(f"Portfolio Dividend Yield: {portfolio_yield:.2f}%")


def add_transaction(tracker: ASXPortfolioTracker):
    """Interactive transaction addition"""
    print("\nAdd New Transaction:")
    print("-" * 20)
    
    stock = input("Stock Symbol: ").upper()
    action = input("Action (buy/sell): ").lower()
    
    try:
        quantity = int(input("Quantity: "))
        price = float(input("Price per share: $"))
        
        total = quantity * price
        fees = tracker.calculate_brokerage(total)
        
        print(f"\nTransaction Summary:")
        print(f"  {action.title()} {quantity} shares of {stock}")
        print(f"  Price: ${price:.4f} per share")
        print(f"  Subtotal: ${total:.2f}")
        print(f"  Brokerage: ${fees:.2f}")
        print(f"  Total: ${total + fees:.2f}")
        
        confirm = input("\nConfirm transaction? (y/N): ").lower()
        
        if confirm == 'y':
            # Create CSV format for import
            date = datetime.now().strftime('%Y-%m-%d')
            csv_data = f"Date,Stock,Action,Quantity,Price,Total,Status\n{date},{stock},{action},{quantity},{price},{total},executed"
            
            tracker.import_transactions_from_csv(csv_data)
            print("✅ Transaction added successfully!")
        else:
            print("Transaction cancelled.")
            
    except ValueError:
        print("❌ Invalid input. Please enter numeric values for quantity and price.")


def export_data(tracker: ASXPortfolioTracker):
    """Export portfolio data"""
    print("\nExport Options:")
    print("1. Portfolio CSV")
    print("2. Transaction History")
    
    choice = input("Select export option (1-2): ")
    
    if choice == '1':
        filename = tracker.export_portfolio_csv()
        print(f"✅ Portfolio exported to {filename}")
    elif choice == '2':
        # Export transaction history
        import sqlite3
        conn = sqlite3.connect(tracker.db_path)
        
        import pandas as pd
        df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
        
        filename = f"transactions_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        
        conn.close()
        print(f"✅ Transaction history exported to {filename}")
    else:
        print("❌ Invalid option.")


def main():
    parser = argparse.ArgumentParser(description='ASX Paper Trading Portfolio Tracker')
    parser.add_argument('--update', action='store_true', help='Update current prices from EODHD API')
    parser.add_argument('--update-major', action='store_true', help='Update only major stocks (CBA, BHP, WOW, etc.) to save API calls')
    parser.add_argument('--force', action='store_true', help='Force API update even if daily limit reached (use with --update)')
    parser.add_argument('--add', action='store_true', help='Add new transaction')
    parser.add_argument('--export', action='store_true', help='Export portfolio data')
    parser.add_argument('--details', action='store_true', help='Show detailed positions')
    parser.add_argument('--dividends', action='store_true', help='Show dividend information')
    parser.add_argument('--api-key', default=EODHD_API_KEY, help='EODHD API key')
    
    args = parser.parse_args()
    
    # Initialize trackers
    tracker = ASXPortfolioTracker()
    dividend_tracker = DividendTracker()
    
    # Check if we have any transactions
    summary = tracker.get_portfolio_summary(args.api_key, False)  # Don't use API for initial check
    if not summary['positions']:
        print("No portfolio data found. Import your initial transactions:")
        
        # Load sample data for demo
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
        
        tracker.import_transactions_from_csv(csv_data)
        populate_sample_dividends(dividend_tracker)
        print("✅ Sample portfolio data loaded!")
        summary = tracker.get_portfolio_summary(args.api_key, False)  # Don't use API by default
    
    # Handle command line arguments
    if args.add:
        add_transaction(tracker)
        return
    
    if args.export:
        export_data(tracker)
        return
    
    if args.update:
        print("Updating current prices from API...")
        if args.force:
            print("🚨 Force mode enabled - bypassing API limit check")
        summary = tracker.get_portfolio_summary(args.api_key, True, args.force)  # Use API when --update is specified
        print("✅ Prices updated from API!")
    elif args.update_major:
        print("Updating major stocks only (to save API calls)...")
        # Update only major stocks
        major_stocks = ['CBA', 'BHP', 'WOW', 'CSL', 'XRO']
        positions = tracker.get_positions()
        
        for stock in positions.keys():
            if stock in major_stocks:
                price = tracker.get_current_price_eodhd(stock, args.api_key)
                if price:
                    print(f"✅ {stock}: ${price:.4f}")
        
        summary = tracker.get_portfolio_summary(args.api_key, False)  # Use stored/sample prices
        print("✅ Major stocks updated!")
    else:
        # No update requested, just get summary without API
        summary = tracker.get_portfolio_summary(args.api_key, False)
    
    # Display portfolio summary
    print_portfolio_summary(tracker, args.details, False, False)  # Never use API for display - already fetched
    
    if args.dividends:
        print_dividend_summary(dividend_tracker, summary['positions'])
    
    # Interactive menu if no specific action requested
    if not any([args.update, args.add, args.export, args.details, args.dividends]):
        print("\nOptions:")
        print("  --update       Update current prices from API")
        print("  --update-major Update only major stocks (saves API calls)")
        print("  --details      Show detailed positions") 
        print("  --dividends    Show dividend analysis")
        print("  --add          Add new transaction")
        print("  --export       Export portfolio data")
        print("  --help         Show all options")


if __name__ == "__main__":
    main()