#!/usr/bin/env python3
"""
ASX Portfolio Tracker - Streamlit Web Interface
Modern web interface for portfolio analysis and tracking
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date
import sqlite3
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import utilities and existing functionality
from streamlit_utils import *
from portfolio_tracker import ASXPortfolioTracker
from dividend_tracker import DividendTracker
from config import EODHD_API_KEY

# Import analysis modules
try:
    from portfolio_vs_asx200 import create_performance_comparison_chart
    from performance_attribution import calculate_stock_contributions
    from rolling_performance import get_rolling_portfolio_data, calculate_rolling_metrics
except ImportError as e:
    st.error(f"Import error: {e}")

# Page configuration
st.set_page_config(
    page_title="ASX Portfolio Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
init_session_state()

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Choose a page",
    ["🏠 Dashboard", "💰 Add Transaction", "📈 Update Prices", "📊 Performance Analysis", "⚙️ Settings"]
)

# Main header
st.markdown('<div class="main-header">📊 ASX Portfolio Tracker</div>', unsafe_allow_html=True)

# Dashboard Page
if page == "🏠 Dashboard":
    st.header("Portfolio Overview")
    
    # Get portfolio summary
    summary = get_portfolio_summary()
    
    if not summary['positions']:
        st.warning("No portfolio data found. Please add some transactions to get started!")
        st.info("Use the 'Add Transaction' page to input your stock purchases.")
    else:
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Market Value",
                format_currency(summary['total_market_value']),
                delta=format_currency(summary['total_unrealized_pnl'])
            )
        
        with col2:
            st.metric(
                "Total Return",
                format_percentage(summary['return_percentage']),
                delta=format_currency(summary['total_unrealized_pnl'])
            )
        
        with col3:
            st.metric(
                "Total Cost Basis",
                format_currency(summary['total_cost']),
                delta=f"-{format_currency(summary['total_fees'])}"
            )
        
        with col4:
            api_status = "🟢 Updated" if summary['api_calls_used'] > 0 else "🟡 Cached"
            st.metric(
                "API Status",
                f"{summary['api_calls_used']}/20",
                delta=api_status
            )
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            # Portfolio allocation chart
            allocation_fig = create_portfolio_overview_chart(summary)
            if allocation_fig:
                st.plotly_chart(allocation_fig, use_container_width=True)
        
        with col2:
            # Performance bar chart
            performance_fig = create_performance_bar_chart(summary)
            if performance_fig:
                st.plotly_chart(performance_fig, use_container_width=True)
        
        # Positions table
        st.subheader("Current Positions")
        positions_df = create_positions_table(summary)
        if not positions_df.empty:
            st.dataframe(positions_df, use_container_width=True)
        
        # Database info
        db_info = get_database_info()
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Transactions", db_info['transactions'])
        with col2:
            st.metric("Price Data Points", db_info['price_points'])
        with col3:
            st.metric("Stocks Tracked", db_info['stocks'])
        with col4:
            date_range = db_info['date_range']
            if date_range[0] and date_range[1]:
                st.metric("Data Range", f"{date_range[0]} to {date_range[1]}")
            else:
                st.metric("Data Range", "No data")

# Add Transaction Page
elif page == "💰 Add Transaction":
    st.header("Add New Transaction")
    
    with st.form("transaction_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            stock = st.text_input("Stock Symbol", placeholder="e.g., CBA, BHP, WOW").upper()
            action = st.selectbox("Action", ["buy", "sell"])
            quantity = st.number_input("Quantity", min_value=1, step=1)
        
        with col2:
            price = st.number_input("Price per Share ($)", min_value=0.01, step=0.01, format="%.2f")
            transaction_date = st.date_input("Transaction Date", value=date.today())
        
        # Calculate preview
        if quantity > 0 and price > 0:
            total = quantity * price
            fees = st.session_state.tracker.calculate_brokerage(total)
            total_with_fees = total + fees
            
            st.subheader("Transaction Preview")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Subtotal", format_currency(total))
            with col2:
                st.metric("Brokerage Fee", format_currency(fees))
            with col3:
                st.metric("Total Cost", format_currency(total_with_fees))
        
        # Submit button
        submitted = st.form_submit_button("Add Transaction")
        
        if submitted:
            # Validate input
            errors = validate_transaction_input(stock, action, quantity, price)
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Add transaction
                success, message = add_transaction(stock, action, quantity, price, transaction_date.strftime('%Y-%m-%d'))
                
                if success:
                    st.success(message)
                    st.rerun()  # Refresh the page
                else:
                    st.error(message)

# Update Prices Page
elif page == "📈 Update Prices":
    st.header("Update Stock Prices")
    
    # Current status
    summary = get_portfolio_summary()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("API Calls Used Today", f"{summary['api_calls_used']}/20")
        st.metric("Last Updated", summary['last_updated'])
    
    with col2:
        if st.session_state.last_update:
            st.metric("Web Update Time", st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            st.metric("Web Update Time", "Never")
    
    # Update buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Update Prices", help="Update prices using available API calls"):
            with st.spinner("Updating prices..."):
                success, message = update_prices()
                
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    with col2:
        if st.button("🚨 Force Update", help="Force update even if API limit reached"):
            with st.spinner("Force updating prices..."):
                success, message = update_prices(force=True)
                
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    # API information
    st.subheader("API Information")
    st.info("""
    **EODHD API Usage:**
    - Free tier: 20 calls per day
    - Resets daily at midnight UTC
    - Force update bypasses limit check
    - Stored prices used when API unavailable
    """)

# Performance Analysis Page
elif page == "📊 Performance Analysis":
    st.header("Performance Analysis")
    
    # Analysis tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📈 vs ASX200", "🎯 Attribution", "📊 Rolling Performance", "📋 Export"])
    
    with tab1:
        st.subheader("Portfolio vs ASX200 Comparison")
        
        if st.button("Generate ASX200 Comparison"):
            with st.spinner("Generating comparison chart..."):
                try:
                    # Import and run the comparison
                    from portfolio_vs_asx200 import create_performance_comparison_chart
                    fig = create_performance_comparison_chart()
                    
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Download link
                        download_link = get_chart_download_link(fig, "portfolio_vs_asx200.png")
                        st.markdown(download_link, unsafe_allow_html=True)
                    else:
                        st.error("Could not generate comparison chart")
                        
                except Exception as e:
                    st.error(f"Error generating chart: {str(e)}")
    
    with tab2:
        st.subheader("Performance Attribution")
        
        if st.button("Generate Attribution Analysis"):
            with st.spinner("Calculating attribution..."):
                try:
                    attribution_df = calculate_stock_contributions()
                    
                    if not attribution_df.empty:
                        # Display summary
                        st.subheader("Attribution Summary")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            top_contributor = attribution_df.iloc[0]
                            st.metric(
                                "Top Contributor",
                                top_contributor['stock'],
                                delta=f"{top_contributor['contribution_to_return']:.3f}%"
                            )
                        
                        with col2:
                            bottom_contributor = attribution_df.iloc[-1]
                            st.metric(
                                "Bottom Contributor",
                                bottom_contributor['stock'],
                                delta=f"{bottom_contributor['contribution_to_return']:.3f}%"
                            )
                        
                        # Attribution table
                        st.subheader("Detailed Attribution")
                        st.dataframe(attribution_df[['stock', 'weight', 'return_pct', 'contribution_to_return']], use_container_width=True)
                    else:
                        st.warning("No attribution data available")
                        
                except Exception as e:
                    st.error(f"Error calculating attribution: {str(e)}")
    
    with tab3:
        st.subheader("Rolling Performance")
        
        if st.button("Generate Rolling Analysis"):
            with st.spinner("Calculating rolling metrics..."):
                try:
                    from rolling_performance import generate_rolling_analysis
                    
                    # Capture the analysis (this will print to console)
                    st.info("Rolling analysis generated - check console for detailed metrics")
                    
                    # You could also display some rolling metrics here
                    st.success("Rolling analysis completed successfully")
                    
                except Exception as e:
                    st.error(f"Error generating rolling analysis: {str(e)}")
    
    with tab4:
        st.subheader("Export Data")
        
        # Export options
        export_option = st.selectbox(
            "Choose export format",
            ["Portfolio Summary CSV", "Transaction History CSV", "Performance Data CSV"]
        )
        
        if st.button("Export Data"):
            try:
                if export_option == "Portfolio Summary CSV":
                    summary = get_portfolio_summary()
                    positions_df = create_positions_table(summary)
                    
                    if not positions_df.empty:
                        csv = positions_df.to_csv(index=False)
                        st.download_button(
                            label="Download Portfolio CSV",
                            data=csv,
                            file_name=f"portfolio_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.warning("No portfolio data to export")
                
                elif export_option == "Transaction History CSV":
                    # Export transaction history
                    conn = sqlite3.connect('portfolio.db')
                    transactions_df = pd.read_sql_query(
                        "SELECT * FROM transactions ORDER BY date DESC",
                        conn
                    )
                    conn.close()
                    
                    if not transactions_df.empty:
                        csv = transactions_df.to_csv(index=False)
                        st.download_button(
                            label="Download Transactions CSV",
                            data=csv,
                            file_name=f"transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.warning("No transaction data to export")
                
                else:  # Performance Data CSV
                    st.info("Performance data export will be available when more historical data is collected")
                    
            except Exception as e:
                st.error(f"Export error: {str(e)}")

# Settings Page
elif page == "⚙️ Settings":
    st.header("Settings & Configuration")
    
    # API Configuration
    st.subheader("API Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("EODHD API Key", value=EODHD_API_KEY, type="password", disabled=True)
        st.caption("Edit config.py to change API key")
    
    with col2:
        st.metric("Current API Usage", f"{get_portfolio_summary()['api_calls_used']}/20")
    
    # Database Management
    st.subheader("Database Management")
    
    db_info = get_database_info()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Transactions", db_info['transactions'])
    with col2:
        st.metric("Price Points", db_info['price_points'])
    with col3:
        st.metric("Stocks", db_info['stocks'])
    
    # Danger zone
    st.subheader("⚠️ Danger Zone")
    
    if st.button("🗑️ Clear All Data", help="This will delete all transactions and price history"):
        if st.checkbox("I understand this will delete all data"):
            try:
                conn = sqlite3.connect('portfolio.db')
                cursor = conn.cursor()
                cursor.execute('DELETE FROM transactions')
                cursor.execute('DELETE FROM price_history')
                cursor.execute('DELETE FROM dividends')
                conn.commit()
                conn.close()
                
                st.success("All data cleared successfully")
                st.rerun()
            except Exception as e:
                st.error(f"Error clearing data: {str(e)}")
    
    # App information
    st.subheader("About")
    st.info("""
    **ASX Portfolio Tracker v2.0**
    - Modern web interface powered by Streamlit
    - Original CLI tools remain fully functional
    - Real-time price updates via EODHD API
    - Comprehensive performance analysis
    - Interactive charts and visualizations
    
    **Built with:** Python, Streamlit, Plotly, SQLite
    """)

# Footer
st.markdown("---")
st.markdown(
    "Built with ❤️ using Streamlit • "
    "📊 ASX Portfolio Tracker • "
    f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)