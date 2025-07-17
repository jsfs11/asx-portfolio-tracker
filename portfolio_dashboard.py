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

# CGT imports - handle gracefully if not available
try:
    from cgt_calculator import CGTCalculator, generate_cgt_report
    CGT_AVAILABLE = True
except ImportError:
    CGT_AVAILABLE = False
    CGTCalculator = None
    generate_cgt_report = None


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
    print(f"  Cash Balance:         ${summary['cash_balance']:>12,.2f}")
    print(f"  Total Portfolio:      ${summary['total_portfolio_value']:>12,.2f}")
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


def print_franking_summary(tracker: ASXPortfolioTracker, positions: dict):
    """Print franking credits analysis"""
    print("\nFRANKING CREDITS ANALYSIS:")
    print("-" * 60)
    
    # Check if franking is available
    try:
        from franking_calculator import FrankingTaxCalculator, StaticFrankingDatabase
        franking_available = True
    except ImportError:
        print("Franking calculator not available. Install required dependencies.")
        return
    
    # Get franking summary
    franking_summary = tracker.get_franking_summary()
    
    if franking_summary:
        print(f"Annual Franking Credits:  ${franking_summary.get('total_franking_credits', 0):>12,.2f}")
        print(f"Tax Benefit:             ${franking_summary.get('tax_benefit', 0):>12,.2f}")
        print(f"Franking Efficiency:     {franking_summary.get('franking_efficiency', 0):>11.1f}%")
        print(f"Effective Tax Rate:      {franking_summary.get('effective_tax_rate', 0):>11.1f}%")
        
        # Show stock-by-stock franking analysis
        if 'stock_details' in franking_summary:
            print(f"\nSTOCK-BY-STOCK FRANKING ANALYSIS:")
            print(f"{'Stock':<6} {'Franking':<8} {'Credits':<10} {'Effective':<10} {'Sector':<12}")
            print("-" * 60)
            
            for stock in franking_summary['stock_details']:
                print(f"{stock['stock']:<6} {stock['franking_rate']:>6.0f}%  "
                      f"${stock['franking_credit']:>8.2f}  "
                      f"{stock['effective_yield']:>8.2f}%  "
                      f"{stock.get('sector', 'Unknown'):<12}")
    else:
        print("No franking analysis available.")


def print_cgt_summary(tracker: ASXPortfolioTracker, positions: dict, tax_year: str = None):
    """Print CGT analysis"""
    print("\nCAPITAL GAINS TAX ANALYSIS:")
    print("-" * 60)
    
    if not CGT_AVAILABLE:
        print("CGT calculator not available. Please ensure cgt-calculator.py is in the directory.")
        return
    
    try:
        cgt_calc = CGTCalculator(tracker.db_path)
        
        # Initialize tax parcels if needed
        cgt_calc.create_tax_parcels_from_transactions()
        
        # Use current tax year if not specified
        if not tax_year:
            from datetime import datetime
            now = datetime.now()
            if now.month >= 7:
                tax_year = f"{now.year}-{now.year + 1}"
            else:
                tax_year = f"{now.year - 1}-{now.year}"
        
        # Get current prices for unrealised gains
        current_prices = {}
        for stock, pos in positions.items():
            current_prices[stock] = pos.current_price
        
        # Show unrealised gains
        unrealised = cgt_calc.get_unrealised_gains(current_prices)
        
        if unrealised:
            print(f"UNREALISED CAPITAL GAINS (as at {datetime.now().strftime('%Y-%m-%d')}):")
            print(f"{'Stock':<6} {'Qty':<6} {'Cost Base':<12} {'Current Val':<12} {'Gain/Loss':<12} {'After Disc.':<12} {'Held':<8}")
            print("-" * 80)
            
            total_unrealised = 0
            total_after_discount = 0
            
            for holding in unrealised:
                total_unrealised += holding['unrealised_gain']
                total_after_discount += holding['after_discount']
                
                discount_indicator = "✓" if holding['discount_eligible'] else ""
                
                print(f"{holding['stock']:<6} {holding['quantity']:<6} "
                      f"${holding['cost_base']:<11.2f} ${holding['current_value']:<11.2f} "
                      f"${holding['unrealised_gain']:<11.2f} ${holding['after_discount']:<11.2f} "
                      f"{holding['holding_period_days']:>5}d {discount_indicator}")
            
            print("-" * 80)
            print(f"{'TOTAL':<19} ${sum(h['cost_base'] for h in unrealised):<11.2f} "
                  f"${sum(h['current_value'] for h in unrealised):<11.2f} "
                  f"${total_unrealised:<11.2f} ${total_after_discount:<11.2f}")
            
            print(f"\nPOTENTIAL CGT LIABILITY: ${max(0, total_after_discount):,.2f}")
            
            # Show savings from CGT discount
            discount_savings = total_unrealised - total_after_discount
            if discount_savings > 0:
                print(f"CGT Discount Savings:    ${discount_savings:,.2f}")
        
        # Show realised gains for current tax year
        try:
            summary = cgt_calc.calculate_annual_cgt(tax_year)
            
            if summary.total_capital_gains > 0 or summary.total_capital_losses > 0:
                print(f"\nREALISED GAINS/LOSSES ({tax_year}):")
                print(f"Total Capital Gains:     ${summary.total_capital_gains:,.2f}")
                print(f"Total Capital Losses:    ${summary.total_capital_losses:,.2f}")
                print(f"Discount Eligible Gains: ${summary.discount_eligible_gains:,.2f}")
                print(f"After CGT Discount:      ${summary.discounted_gains:,.2f}")
                print(f"Carried Forward Losses:  ${summary.carried_forward_losses:,.2f}")
                print(f"\nNET CAPITAL GAIN:       ${summary.net_capital_gain:,.2f}")
        except:
            # No realised events yet
            pass
            
    except Exception as e:
        print(f"CGT analysis error: {e}")
        print("Run with --update-cgt to initialize CGT tracking")


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
    parser.add_argument('--franking', action='store_true', help='Show franking credits analysis')
    parser.add_argument('--update-franking', action='store_true', help='Update franking data from API')
    parser.add_argument('--cgt', action='store_true', help='Show CGT analysis')
    parser.add_argument('--cgt-report', type=str, help='Generate detailed CGT report for tax year (e.g. 2024-2025)')
    parser.add_argument('--update-cgt', action='store_true', help='Initialize/update CGT tracking from transactions')
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
    
    if args.franking:
        print_franking_summary(tracker, summary['positions'])
    
    if args.cgt:
        print_cgt_summary(tracker, summary['positions'])
    
    if args.cgt_report:
        if not CGT_AVAILABLE:
            print("\n❌ CGT calculator not available. Please ensure cgt-calculator.py is in the directory.")
        else:
            try:
                cgt_calc = CGTCalculator(tracker.db_path)
                cgt_calc.create_tax_parcels_from_transactions()
                generate_cgt_report(cgt_calc, args.cgt_report)
            except Exception as e:
                print(f"Error generating CGT report: {e}")
    
    if args.update_cgt:
        if not CGT_AVAILABLE:
            print("\n❌ CGT calculator not available. Please ensure cgt-calculator.py is in the directory.")
        else:
            print("\nInitializing CGT tracking...")
            try:
                cgt_calc = CGTCalculator(tracker.db_path)
                cgt_calc.create_tax_parcels_from_transactions()
                print("✅ CGT tracking initialized from transaction history")
            except Exception as e:
                print(f"❌ Error initializing CGT tracking: {e}")
    
    if args.update_franking:
        print("\nUpdating franking data from API...")
        try:
            from franking_calculator import StaticFrankingDatabase
            franking_db = StaticFrankingDatabase()
            
            # Get stocks from current portfolio
            stocks = list(summary['positions'].keys())
            if stocks:
                results = franking_db.bulk_update_franking_from_api(stocks, args.api_key)
                if results:
                    print(f"✅ Updated franking data for {len(results)} stocks")
                else:
                    print("❌ No franking updates available")
            else:
                print("❌ No stocks in portfolio to update")
                
        except ImportError:
            print("❌ Franking calculator not available")
        except Exception as e:
            print(f"❌ Error updating franking data: {e}")
    
    # Interactive menu if no specific action requested
    if not any([args.update, args.add, args.export, args.details, args.dividends, args.franking, args.update_franking, args.cgt, args.cgt_report, args.update_cgt]):
        print("\nOptions:")
        print("  --update       Update current prices from API")
        print("  --update-major Update only major stocks (saves API calls)")
        print("  --details      Show detailed positions") 
        print("  --dividends    Show dividend analysis")
        print("  --franking     Show franking credits analysis")
        print("  --update-franking Update franking data from API")
        print("  --cgt          Show CGT analysis (unrealised gains)")
        print("  --cgt-report YEAR Generate detailed CGT report (e.g. 2024-2025)")
        print("  --update-cgt   Initialize CGT tracking from transactions")
        print("  --add          Add new transaction")
        print("  --export       Export portfolio data")
        print("  --help         Show all options")


if __name__ == "__main__":
    main()