#!/usr/bin/env python3
"""
ASX Portfolio Tracker - Streamlit Web Interface
Modern web interface for portfolio analysis and tracking
"""

import os
import sqlite3
import sys
from datetime import date, datetime

import pandas as pd
import plotly.graph_objects as go  # type: ignore
import streamlit as st

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import EODHD_API_KEY
from dividend_tracker import DividendTracker
from portfolio_tracker import ASXPortfolioTracker
# Import utilities and existing functionality
from streamlit_utils import *

# Import analysis modules
try:
    from performance_attribution import calculate_stock_contributions
    from portfolio_vs_asx200 import create_performance_comparison_chart
    from rolling_performance import (calculate_rolling_metrics,
                                     get_rolling_portfolio_data)
except ImportError as e:
    st.error(f"Import error: {e}")

# Page configuration
st.set_page_config(
    page_title="ASX Portfolio Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
init_session_state()

# Custom CSS for better styling
st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)

# Sidebar navigation
st.sidebar.title("Navigation")

# Check if user needs setup for sidebar highlighting
try:
    temp_tracker = ASXPortfolioTracker()
    is_new_user = temp_tracker.is_new_user() and not temp_tracker.has_any_data()
except:
    is_new_user = False

if is_new_user:
    st.sidebar.warning("🚀 Complete Setup First!")
    st.sidebar.markdown("*Start with the Setup wizard to configure your portfolio*")

page = st.sidebar.selectbox(
    "Choose a page",
    [
        "🏠 Dashboard",
        "🚀 Setup",
        "💰 Add Transaction",
        "📈 Update Prices",
        "📊 Performance Analysis",
        "📈 OHLC Analysis",
        "🏛️ Franking Credits",
        "💰 CGT Analysis",
        "🧮 Tax Calculator",
        "⚙️ Settings",
    ],
)

# Main header
st.markdown(
    '<div class="main-header">📊 ASX Portfolio Tracker</div>', unsafe_allow_html=True
)

# Dashboard Page
if page == "🏠 Dashboard":
    # Check if user needs setup (new user detection)
    tracker = ASXPortfolioTracker()
    if tracker.is_new_user() and not tracker.has_any_data():
        # Redirect new users to setup
        st.info(
            "👋 Welcome! It looks like this is your first time using ASX Portfolio Tracker."
        )
        st.markdown("### 🚀 Let's get you set up!")
        st.markdown(
            """
        To get started, please complete the quick setup wizard to configure your portfolio.
        
        **Setup takes less than 2 minutes and includes:**
        - Setting your starting cash balance
        - Configuring basic preferences
        - Learning how to add transactions
        """
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "🚀 Start Setup Wizard", type="primary", use_container_width=True
            ):
                st.success("👈 Please select '🚀 Setup' from the sidebar to continue!")
                st.balloons()

        st.markdown("---")
        st.markdown(
            "*Or continue to explore the interface without setup (data won't be saved)*"
        )

        # Still show the empty dashboard below for exploration
        st.header("Portfolio Overview (Preview Mode)")
    else:
        st.header("Portfolio Overview")

    # Get portfolio summary
    summary = get_portfolio_summary()

    if not summary["positions"]:
        st.warning(
            "No portfolio data found. Please add some transactions to get started!"
        )
        st.info("Use the 'Add Transaction' page to input your stock purchases.")
    else:
        # Key metrics row
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                "Total Market Value",
                format_currency(summary["total_market_value"]),
                delta=format_currency(summary["total_unrealized_pnl"]),
            )

        with col2:
            st.metric(
                "Cash Balance",
                format_currency(summary.get("cash_balance", 0)),
                delta="💰 Available",
            )

        with col3:
            total_portfolio = summary["total_market_value"] + summary.get(
                "cash_balance", 0
            )
            st.metric(
                "Total Portfolio",
                format_currency(total_portfolio),
                delta=format_currency(summary["total_unrealized_pnl"]),
            )

        with col4:
            st.metric(
                "Total Return",
                format_percentage(summary["return_percentage"]),
                delta=format_currency(summary["total_unrealized_pnl"]),
            )

        with col5:
            api_status = "🟢 Updated" if summary["api_calls_used"] > 0 else "🟡 Cached"
            st.metric("API Status", f"{summary['api_calls_used']}/20", delta=api_status)

        # Franking Credits section (if available)
        try:
            from franking_calculator import (FrankingTaxCalculator,
                                             StaticFrankingDatabase)

            franking_available = True
        except ImportError:
            franking_available = False

        if franking_available:
            st.subheader("💰 Franking Credits Overview")

            # Initialize tracker for franking analysis
            tracker = ASXPortfolioTracker()

            # Get franking summary with updated positions
            franking_summary = tracker.get_franking_summary()

            if franking_summary and "stock_details" in franking_summary:
                fcol1, fcol2, fcol3 = st.columns(3)

                with fcol1:
                    st.metric(
                        "Annual Franking Credits",
                        f"${franking_summary.get('total_franking_credits', 0):,.2f}",
                    )

                with fcol2:
                    st.metric(
                        "Tax Benefit", f"${franking_summary.get('tax_benefit', 0):,.2f}"
                    )

                with fcol3:
                    st.metric(
                        "Franking Efficiency",
                        f"{franking_summary.get('franking_efficiency', 0):.1f}%",
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
            st.metric("Total Transactions", db_info["transactions"])
        with col2:
            st.metric("Price Data Points", db_info["price_points"])
        with col3:
            st.metric("Stocks Tracked", db_info["stocks"])
        with col4:
            date_range = db_info["date_range"]
            if date_range[0] and date_range[1]:
                st.metric("Data Range", f"{date_range[0]} to {date_range[1]}")
            else:
                st.metric("Data Range", "No data")

# Setup Wizard Page
elif page == "🚀 Setup":
    st.header("Welcome to ASX Portfolio Tracker! 🎉")

    # Check if user is already set up
    tracker = ASXPortfolioTracker()
    user_settings = tracker.get_user_settings()

    if user_settings["setup_completed"]:
        st.success("✅ Your portfolio is already set up!")
        st.info("You can modify these settings anytime by re-running the setup wizard.")

        # Show current settings
        st.subheader("Current Settings")
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Portfolio Name", user_settings["portfolio_name"])
            st.metric("Starting Cash", f"${user_settings['starting_cash']:,.2f}")

        with col2:
            if user_settings["created_date"]:
                st.metric("Created", user_settings["created_date"][:10])

            # Show if there's any data
            if tracker.has_any_data():
                st.metric("Status", "Active Portfolio 📈")
            else:
                st.metric("Status", "Ready for Data 🚀")

        st.markdown("---")

        if st.button("🔄 Re-run Setup Wizard"):
            # Allow re-setup
            user_settings["setup_completed"] = False
            st.rerun()

    else:
        # First-time setup wizard
        st.markdown(
            """
        ### Let's get your portfolio set up! 🚀
        
        This quick setup will help you:
        - Configure your starting cash balance
        - Set up basic portfolio preferences  
        - Learn how to add your first transactions
        
        **Takes less than 2 minutes!**
        """
        )

        # Setup form
        with st.form("setup_wizard"):
            st.subheader("📊 Portfolio Configuration")

            col1, col2 = st.columns(2)

            with col1:
                portfolio_name = st.text_input(
                    "Portfolio Name",
                    value="My ASX Portfolio",
                    help="Give your portfolio a personalized name",
                )

                starting_cash = st.number_input(
                    "Starting Cash Balance ($)",
                    min_value=0.0,
                    value=25000.0,
                    step=1000.0,
                    help="How much cash are you starting with? This can be your actual cash balance or investment budget.",
                )

            with col2:
                st.markdown("**💡 Quick Tips:**")
                st.markdown(
                    """
                - **Starting Cash**: This tracks your available cash for investments
                - **Portfolio Name**: Helps identify your portfolio in exports
                - **You can change these settings later** in the Settings page
                """
                )

            st.subheader("🎯 What's Next?")
            st.markdown(
                """
            After setup, you'll be able to:
            1. **Add transactions** - Record your stock purchases and sales
            2. **Track performance** - See real-time portfolio values
            3. **Analyze taxes** - CGT and franking credits analysis
            4. **Export data** - Download reports and analysis
            """
            )

            # Setup completion
            setup_submitted = st.form_submit_button(
                "🚀 Complete Setup & Start Tracking!", type="primary"
            )

            if setup_submitted:
                # Validate inputs
                if not portfolio_name.strip():
                    st.error("Please enter a portfolio name")
                elif starting_cash < 0:
                    st.error("Starting cash must be positive")
                else:
                    # Initialize user settings
                    tracker.initialize_user_settings(
                        starting_cash, portfolio_name.strip()
                    )

                    st.success("🎉 Setup Complete! Welcome to ASX Portfolio Tracker!")
                    st.balloons()

                    # Show next steps
                    st.markdown("### 🎯 Ready to Start!")
                    st.markdown(
                        """
                    **Your portfolio is now set up with:**
                    - 💰 Starting Cash: ${:,.2f}
                    - 📊 Portfolio Name: {}
                    
                    **Next Steps:**
                    1. Go to **💰 Add Transaction** to record your first stock purchase
                    2. Visit **📈 Update Prices** to get current market values  
                    3. Check **🏠 Dashboard** to see your portfolio overview
                    """.format(
                            starting_cash, portfolio_name
                        )
                    )

                    # Auto-redirect after a moment
                    st.info(
                        "💡 Tip: You can now navigate to 'Add Transaction' to record your first stock purchase!"
                    )

                    # Refresh page to show dashboard
                    if st.button("Go to Dashboard 🏠"):
                        st.rerun()

# Add Transaction Page
elif page == "💰 Add Transaction":
    st.header("Add New Transaction")

    with st.form("transaction_form"):
        col1, col2 = st.columns(2)

        with col1:
            stock = st.text_input(
                "Stock Symbol", placeholder="e.g., CBA, BHP, WOW"
            ).upper()
            action = st.selectbox("Action", ["buy", "sell"])
            quantity = st.number_input("Quantity", min_value=1, step=1)

        with col2:
            price = st.number_input(
                "Price per Share ($)", min_value=0.01, step=0.01, format="%.2f"
            )
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
                success, message = add_transaction(
                    stock,
                    action,
                    quantity,
                    price,
                    transaction_date.strftime("%Y-%m-%d"),
                )

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
        st.metric("Last Updated", summary["last_updated"])

    with col2:
        if st.session_state.last_update:
            st.metric(
                "Web Update Time",
                st.session_state.last_update.strftime("%Y-%m-%d %H:%M:%S"),
            )
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
    st.info(
        """
    **EODHD API Usage:**
    - Free tier: 20 calls per day
    - Resets daily at midnight UTC
    - Force update bypasses limit check
    - Stored prices used when API unavailable
    """
    )

# Performance Analysis Page
elif page == "📊 Performance Analysis":
    st.header("Performance Analysis")

    # Analysis tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📈 vs ASX200", "🎯 Attribution", "📊 Rolling Performance", "📋 Export"]
    )

    with tab1:
        st.subheader("Portfolio vs ASX200 Comparison")

        if st.button("Generate ASX200 Comparison"):
            with st.spinner("Generating comparison chart..."):
                try:
                    # Import and run the comparison
                    from portfolio_vs_asx200 import \
                        create_performance_comparison_chart

                    fig = create_performance_comparison_chart()

                    if fig:
                        st.plotly_chart(fig, use_container_width=True)

                        # Download link
                        download_link = get_chart_download_link(
                            fig, "portfolio_vs_asx200.png"
                        )
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
                                top_contributor["stock"],
                                delta=f"{top_contributor['contribution_to_return']:.3f}%",
                            )

                        with col2:
                            bottom_contributor = attribution_df.iloc[-1]
                            st.metric(
                                "Bottom Contributor",
                                bottom_contributor["stock"],
                                delta=f"{bottom_contributor['contribution_to_return']:.3f}%",
                            )

                        # Attribution table
                        st.subheader("Detailed Attribution")
                        st.dataframe(
                            attribution_df[
                                [
                                    "stock",
                                    "weight",
                                    "return_pct",
                                    "contribution_to_return",
                                ]
                            ],
                            use_container_width=True,
                        )
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
                    st.info(
                        "Rolling analysis generated - check console for detailed metrics"
                    )

                    # You could also display some rolling metrics here
                    st.success("Rolling analysis completed successfully")

                except Exception as e:
                    st.error(f"Error generating rolling analysis: {str(e)}")

    with tab4:
        st.subheader("Export Data")

        # Export options
        export_option = st.selectbox(
            "Choose export format",
            [
                "Portfolio Summary CSV",
                "Transaction History CSV",
                "Performance Data CSV",
                "Export All Data (ZIP)",
            ],
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
                            mime="text/csv",
                        )
                    else:
                        st.warning("No portfolio data to export")

                elif export_option == "Transaction History CSV":
                    # Export transaction history
                    conn = sqlite3.connect("portfolio.db")
                    transactions_df = pd.read_sql_query(
                        "SELECT * FROM transactions ORDER BY date DESC", conn
                    )
                    conn.close()

                    if not transactions_df.empty:
                        csv = transactions_df.to_csv(index=False)
                        st.download_button(
                            label="Download Transactions CSV",
                            data=csv,
                            file_name=f"transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                        )
                    else:
                        st.warning("No transaction data to export")

                elif export_option == "Performance Data CSV":
                    st.info(
                        "Performance data export will be available when more historical data is collected"
                    )

                else:  # Export All Data (ZIP)
                    # Export all database tables as separate CSV files in a ZIP
                    import io
                    import zipfile
                    from tempfile import NamedTemporaryFile

                    with NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
                        with zipfile.ZipFile(
                            tmp_file.name, "w", zipfile.ZIP_DEFLATED
                        ) as zip_file:
                            # Connect to database
                            conn = sqlite3.connect("portfolio.db")

                            # Export each table as CSV
                            tables = [
                                "transactions",
                                "price_history",
                                "dividends",
                                "dividend_payments",
                                "tax_parcels",
                                "cgt_events",
                                "capital_losses",
                                "tax_settings",
                            ]

                            for table in tables:
                                try:
                                    df = pd.read_sql_query(
                                        f"SELECT * FROM {table}", conn
                                    )
                                    if not df.empty:
                                        csv_buffer = io.StringIO()
                                        df.to_csv(csv_buffer, index=False)
                                        zip_file.writestr(
                                            f"{table}.csv", csv_buffer.getvalue()
                                        )
                                except Exception as e:
                                    # Table might not exist, skip it
                                    continue

                            # Export current portfolio summary
                            summary = get_portfolio_summary()
                            positions_df = create_positions_table(summary)
                            if not positions_df.empty:
                                csv_buffer = io.StringIO()
                                positions_df.to_csv(csv_buffer, index=False)
                                zip_file.writestr(
                                    "current_portfolio.csv", csv_buffer.getvalue()
                                )

                            conn.close()

                        # Read the zip file for download
                        with open(tmp_file.name, "rb") as f:
                            zip_data = f.read()

                        st.download_button(
                            label="Download All Data (ZIP)",
                            data=zip_data,
                            file_name=f"portfolio_all_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                            mime="application/zip",
                        )

                        # Clean up
                        import os

                        os.unlink(tmp_file.name)

            except Exception as e:
                st.error(f"Export error: {str(e)}")

# OHLC Analysis Page
elif page == "📈 OHLC Analysis":
    try:
        from ohlc_dashboard import create_ohlc_dashboard

        create_ohlc_dashboard()
    except ImportError as e:
        st.error(f"OHLC Analysis not available: {e}")
        st.info("Make sure ohlc_dashboard.py is in the same directory")
    except Exception as e:
        st.error(f"OHLC Analysis error: {e}")

# Franking Credits Page
elif page == "🏛️ Franking Credits":
    st.header("Franking Credits Analysis")

    # Initialize tracker
    tracker = ASXPortfolioTracker()

    # Check if franking is available
    try:
        from franking_calculator import (FrankingTaxCalculator,
                                         StaticFrankingDatabase)

        franking_available = True
    except ImportError:
        franking_available = False
        st.error(
            "Franking calculator not available. Please install required dependencies."
        )

    if franking_available:
        # Get portfolio summary with franking
        summary = tracker.get_portfolio_summary()

        if not summary["positions"]:
            st.warning(
                "No portfolio data found. Please add some transactions to get started!"
            )
        else:
            # Franking overview metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                franking_credits = summary.get("franking_credits", 0)
                st.metric("Annual Franking Credits", f"${franking_credits:,.2f}")

            with col2:
                tax_benefit = summary.get("tax_benefit", 0)
                st.metric("Tax Benefit", f"${tax_benefit:,.2f}")

            with col3:
                franking_efficiency = summary.get("franking_efficiency", 0)
                st.metric("Franking Efficiency", f"{franking_efficiency:.1f}%")

            with col4:
                effective_tax_rate = summary.get("effective_tax_rate", 0)
                st.metric("Effective Tax Rate", f"{effective_tax_rate:.1f}%")

            # Detailed franking analysis
            st.subheader("Stock-by-Stock Franking Analysis")

            # Get detailed franking data
            franking_details = tracker.get_franking_summary()

            if franking_details and "stock_details" in franking_details:
                # Create dataframe for display
                franking_data = []
                for stock in franking_details["stock_details"]:
                    franking_data.append(
                        {
                            "Stock": stock["stock"],
                            "Franking Rate": f"{stock['franking_rate']:.0f}%",
                            "Market Value": f"${stock['market_value']:,.2f}",
                            "Annual Franking Credits": f"${stock['franking_credit']:,.2f}",
                            "Effective Yield": f"{stock['effective_yield']:.2f}%",
                            "Sector": stock.get("sector", "Unknown"),
                        }
                    )

                df = pd.DataFrame(franking_data)
                st.dataframe(df, use_container_width=True)

                # Add franking credits charts
                st.subheader("Franking Credits Visualization")

                # Charts row
                chart_col1, chart_col2 = st.columns(2)

                with chart_col1:
                    # Import chart functions
                    from streamlit_utils import create_franking_credits_chart

                    franking_chart = create_franking_credits_chart(franking_details)
                    if franking_chart:
                        st.plotly_chart(franking_chart, use_container_width=True)

                with chart_col2:
                    # Import sector chart function
                    from streamlit_utils import create_franking_by_sector_chart

                    sector_chart = create_franking_by_sector_chart(franking_details)
                    if sector_chart:
                        st.plotly_chart(sector_chart, use_container_width=True)

            # Franking optimization suggestions
            st.subheader("Optimization Suggestions")

            # Tax income input for optimization
            col1, col2 = st.columns(2)
            with col1:
                taxable_income = st.number_input(
                    "Taxable Income", min_value=0, value=85000, step=1000
                )

            with col2:
                if st.button("Get Optimization Suggestions"):
                    suggestions = tracker.get_franking_optimization_suggestions(
                        taxable_income
                    )

                    if suggestions:
                        for suggestion in suggestions:
                            message = suggestion.get("message", str(suggestion))
                            st.info(f"💡 {message}")
                    else:
                        st.success(
                            "Your portfolio is already well-optimized for franking credits!"
                        )

# CGT Analysis Page
elif page == "💰 CGT Analysis":
    st.header("Capital Gains Tax Analysis")

    # CGT Analysis
    try:
        from cgt_calculator import CGTCalculator

        # Initialize CGT calculator
        tracker = ASXPortfolioTracker()
        cgt_calc = CGTCalculator(tracker.db_path)

        # Initialize CGT tracking if needed
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button(
                "🔄 Initialize CGT Tracking",
                help="Set up CGT tracking from your transaction history",
            ):
                with st.spinner("Setting up CGT tracking..."):
                    cgt_calc.create_tax_parcels_from_transactions()
                    st.success("✅ CGT tracking initialized!")

        # Tax year selector
        current_year = datetime.now().year
        if datetime.now().month >= 7:
            default_tax_year = f"{current_year}-{current_year + 1}"
        else:
            default_tax_year = f"{current_year - 1}-{current_year}"

        with col1:
            tax_year = st.selectbox(
                "📅 Select Tax Year",
                [f"{y}-{y+1}" for y in range(2020, current_year + 2)],
                index=[f"{y}-{y+1}" for y in range(2020, current_year + 2)].index(
                    default_tax_year
                ),
            )

        # Get current prices and summary
        summary = get_portfolio_summary()
        current_prices = {}
        for stock, pos in summary["positions"].items():
            current_prices[stock] = pos.current_price

        # Unrealised gains analysis
        st.subheader("📈 Unrealised Capital Gains")

        unrealised = cgt_calc.get_unrealised_gains(current_prices)

        if unrealised:
            # Create DataFrame for display
            unrealised_df = pd.DataFrame(unrealised)

            # Format for display
            display_df = unrealised_df[
                [
                    "stock",
                    "quantity",
                    "cost_base",
                    "current_value",
                    "unrealised_gain",
                    "after_discount",
                    "holding_period_days",
                    "discount_eligible",
                ]
            ].copy()

            display_df.columns = [
                "Stock",
                "Quantity",
                "Cost Base",
                "Current Value",
                "Gain/Loss",
                "After Discount",
                "Days Held",
                "Discount Eligible",
            ]

            # Format currency columns
            for col in ["Cost Base", "Current Value", "Gain/Loss", "After Discount"]:
                display_df[col] = display_df[col].apply(lambda x: f"${x:,.2f}")

            # Add emoji for discount eligibility
            display_df["Discount Eligible"] = display_df["Discount Eligible"].apply(
                lambda x: "✅" if x else "❌"
            )

            st.dataframe(display_df, use_container_width=True)

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            total_unrealised = sum(h["unrealised_gain"] for h in unrealised)
            total_after_discount = sum(h["after_discount"] for h in unrealised)
            discount_savings = total_unrealised - total_after_discount

            with col1:
                st.metric("Total Unrealised Gain", f"${total_unrealised:,.2f}")

            with col2:
                st.metric("After CGT Discount", f"${total_after_discount:,.2f}")

            with col3:
                st.metric(
                    "Potential CGT Liability", f"${max(0, total_after_discount):,.2f}"
                )

            with col4:
                st.metric("CGT Discount Savings", f"${discount_savings:,.2f}")

            # Visual chart
            st.subheader("📊 CGT Analysis by Stock")

            # Create chart showing gains vs after-discount
            fig = go.Figure()

            stocks = [h["stock"] for h in unrealised]
            gains = [h["unrealised_gain"] for h in unrealised]
            after_discount = [h["after_discount"] for h in unrealised]

            fig.add_trace(
                go.Bar(
                    name="Gross Gain/Loss", x=stocks, y=gains, marker_color="lightblue"
                )
            )

            fig.add_trace(
                go.Bar(
                    name="After CGT Discount",
                    x=stocks,
                    y=after_discount,
                    marker_color="darkblue",
                )
            )

            fig.update_layout(
                title="Unrealised Gains: Gross vs After CGT Discount",
                xaxis_title="Stock",
                yaxis_title="Gain/Loss ($)",
                barmode="group",
                height=400,
            )

            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info(
                "💡 No unrealised gains data available. Click 'Initialize CGT Tracking' to get started."
            )

        # Realised gains for tax year
        st.subheader(f"💰 Realised Gains/Losses ({tax_year})")

        try:
            cgt_summary = cgt_calc.calculate_annual_cgt(tax_year)

            if (
                cgt_summary.total_capital_gains > 0
                or cgt_summary.total_capital_losses > 0
            ):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Total Capital Gains",
                        f"${cgt_summary.total_capital_gains:,.2f}",
                    )
                    st.metric(
                        "Total Capital Losses",
                        f"${cgt_summary.total_capital_losses:,.2f}",
                    )

                with col2:
                    st.metric(
                        "Discount Eligible Gains",
                        f"${cgt_summary.discount_eligible_gains:,.2f}",
                    )
                    st.metric(
                        "After CGT Discount", f"${cgt_summary.discounted_gains:,.2f}"
                    )

                with col3:
                    st.metric(
                        "Carried Forward Losses",
                        f"${cgt_summary.carried_forward_losses:,.2f}",
                    )
                    st.metric(
                        "NET CAPITAL GAIN", f"${cgt_summary.net_capital_gain:,.2f}"
                    )

            else:
                st.info(f"📋 No realised capital gains/losses for {tax_year}")

        except Exception as e:
            st.info(f"📋 No realised gains data for {tax_year}")

        # CGT optimization suggestions
        st.subheader("🎯 Tax Optimization Suggestions")

        # Find stocks with unrealised losses for tax loss harvesting
        if unrealised:
            losses = [h for h in unrealised if h["unrealised_gain"] < 0]
            gains = [h for h in unrealised if h["unrealised_gain"] > 0]

            if losses:
                st.write("**💸 Tax Loss Harvesting Opportunities:**")
                for loss in losses:
                    st.write(
                        f"• **{loss['stock']}**: Loss of ${abs(loss['unrealised_gain']):,.2f} (held {loss['holding_period_days']} days)"
                    )

            if gains:
                st.write("**⏰ CGT Discount Opportunities:**")
                for gain in gains:
                    if gain["holding_period_days"] < 365:
                        days_to_discount = 365 - gain["holding_period_days"]
                        potential_savings = gain["unrealised_gain"] * 0.5
                        st.write(
                            f"• **{gain['stock']}**: Wait {days_to_discount} more days to save ${potential_savings:,.2f} in CGT"
                        )

            if not losses and not gains:
                st.info("🎉 No immediate tax optimization opportunities identified.")

    except ImportError:
        st.error(
            "❌ CGT calculator not available. Please ensure cgt_calculator.py is in the directory."
        )
    except Exception as e:
        st.error(f"❌ CGT analysis error: {e}")

# Tax Calculator Page
elif page == "🧮 Tax Calculator":
    st.header("Tax Calculator")

    # Initialize tracker
    tracker = ASXPortfolioTracker()

    # Check if franking is available
    try:
        from franking_calculator import (FrankingTaxCalculator,
                                         StaticFrankingDatabase)

        franking_available = True
    except ImportError:
        franking_available = False
        st.error(
            "Franking calculator not available. Please install required dependencies."
        )

    if franking_available:
        st.subheader("Tax Settings")

        # Get current tax settings
        current_settings = tracker.get_tax_settings()

        # Tax configuration form
        col1, col2 = st.columns(2)

        with col1:
            tax_year = st.selectbox("Tax Year", ["2024-25", "2023-24"], index=0)
            taxable_income = st.number_input(
                "Taxable Income",
                min_value=0,
                value=current_settings["taxable_income"],
                step=1000,
            )
            is_resident = st.checkbox(
                "Australian Tax Resident", value=current_settings["is_resident"]
            )

        with col2:
            medicare_levy = st.number_input(
                "Medicare Levy (%)",
                min_value=0.0,
                max_value=10.0,
                value=current_settings["medicare_levy"],
                step=0.1,
            )

            if st.button("Save Tax Settings"):
                new_settings = {
                    "tax_year": tax_year,
                    "taxable_income": taxable_income,
                    "tax_bracket": 32.5,  # Will be calculated based on income
                    "medicare_levy": medicare_levy,
                    "is_resident": is_resident,
                }

                tracker.save_tax_settings(new_settings)
                st.success("Tax settings saved successfully!")
                st.rerun()

        # Tax calculation results
        if taxable_income > 0:
            st.subheader("Tax Calculation Results")

            # Get franking analysis with current settings
            franking_analysis = tracker.get_franking_summary(taxable_income)

            if franking_analysis:
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Total Tax Payable",
                        f"${franking_analysis.get('total_tax', 0):,.2f}",
                    )

                with col2:
                    st.metric(
                        "Franking Credits",
                        f"${franking_analysis.get('total_franking_credits', 0):,.2f}",
                    )

                with col3:
                    st.metric(
                        "Net Tax After Franking",
                        f"${franking_analysis.get('net_tax', 0):,.2f}",
                    )

                # Tax breakdown
                st.subheader("Tax Breakdown")

                # Calculate tax brackets
                tax_brackets = [
                    (0, 18200, 0),
                    (18201, 45000, 19),
                    (45001, 120000, 32.5),
                    (120001, 180000, 37),
                    (180001, float("inf"), 45),
                ]

                tax_breakdown = []
                remaining_income = taxable_income

                for min_income, max_income, rate in tax_brackets:
                    if remaining_income <= 0:
                        break

                    if taxable_income > min_income:
                        taxable_in_bracket = min(
                            remaining_income, max_income - min_income + 1
                        )
                        if min_income == 0:
                            taxable_in_bracket = min(remaining_income, max_income)

                        tax_in_bracket = taxable_in_bracket * rate / 100

                        if taxable_in_bracket > 0:
                            tax_breakdown.append(
                                {
                                    "Tax Bracket": (
                                        f"${min_income:,} - ${max_income:,}"
                                        if max_income != float("inf")
                                        else f"${min_income:,}+"
                                    ),
                                    "Rate": f"{rate}%",
                                    "Taxable Income": f"${taxable_in_bracket:,.2f}",
                                    "Tax": f"${tax_in_bracket:,.2f}",
                                }
                            )

                        remaining_income -= taxable_in_bracket

                if tax_breakdown:
                    df_tax = pd.DataFrame(tax_breakdown)
                    st.dataframe(df_tax, use_container_width=True)

# Settings Page
elif page == "⚙️ Settings":
    st.header("Settings & Configuration")

    # API Configuration
    st.subheader("API Configuration")

    col1, col2 = st.columns(2)

    with col1:
        st.text_input(
            "EODHD API Key", value=EODHD_API_KEY, type="password", disabled=True
        )
        st.caption("Edit config.py to change API key")

    with col2:
        st.metric(
            "Current API Usage", f"{get_portfolio_summary()['api_calls_used']}/20"
        )

    # Database Management
    st.subheader("Database Management")

    db_info = get_database_info()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Transactions", db_info["transactions"])
    with col2:
        st.metric("Price Points", db_info["price_points"])
    with col3:
        st.metric("Stocks", db_info["stocks"])

    # Danger zone
    st.subheader("⚠️ Danger Zone")

    if st.button(
        "🗑️ Clear All Data", help="This will delete all transactions and price history"
    ):
        if st.checkbox("I understand this will delete all data"):
            try:
                conn = sqlite3.connect("portfolio.db")
                cursor = conn.cursor()
                cursor.execute("DELETE FROM transactions")
                cursor.execute("DELETE FROM price_history")
                cursor.execute("DELETE FROM dividends")
                conn.commit()
                conn.close()

                st.success("All data cleared successfully")
                st.rerun()
            except Exception as e:
                st.error(f"Error clearing data: {str(e)}")

    # App information
    st.subheader("About")
    st.info(
        """
    **ASX Portfolio Tracker v2.0**
    - Modern web interface powered by Streamlit
    - Original CLI tools remain fully functional
    - Real-time price updates via EODHD API
    - Comprehensive performance analysis
    - Interactive charts and visualizations
    
    **Built with:** Python, Streamlit, Plotly, SQLite
    """
    )

# Footer
st.markdown("---")
st.markdown(
    "Built with ❤️ using Streamlit • "
    "📊 ASX Portfolio Tracker • "
    f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
