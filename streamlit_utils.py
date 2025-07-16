#!/usr/bin/env python3
"""
Streamlit Utilities
Helper functions for the Streamlit web interface
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date
import sqlite3
import io
import base64

# Import existing functionality (non-destructive)
from portfolio_tracker import ASXPortfolioTracker
from dividend_tracker import DividendTracker
from config import EODHD_API_KEY

def init_session_state():
    """Initialize Streamlit session state variables"""
    if 'tracker' not in st.session_state:
        st.session_state.tracker = ASXPortfolioTracker()
    if 'dividend_tracker' not in st.session_state:
        st.session_state.dividend_tracker = DividendTracker()
    if 'last_update' not in st.session_state:
        st.session_state.last_update = None
    if 'portfolio_data' not in st.session_state:
        st.session_state.portfolio_data = None

def get_portfolio_summary(use_api=False, force=False):
    """Get portfolio summary with caching"""
    return st.session_state.tracker.get_portfolio_summary(EODHD_API_KEY, use_api, force)

def format_currency(value):
    """Format currency values for display"""
    return f"${value:,.2f}"

def format_percentage(value):
    """Format percentage values for display"""
    return f"{value:.2f}%"

def get_performance_color(value):
    """Get color for performance values"""
    if value > 0:
        return "green"
    elif value < 0:
        return "red"
    else:
        return "gray"

def create_metric_card(title, value, delta=None, delta_color=None):
    """Create a metric card with optional delta"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if isinstance(value, (int, float)):
            if title in ["Total Cost", "Market Value", "Unrealized P&L"]:
                st.metric(title, format_currency(value), delta=delta)
            elif "%" in title or "Return" in title:
                st.metric(title, format_percentage(value), delta=delta)
            else:
                st.metric(title, f"{value:,.0f}", delta=delta)
        else:
            st.metric(title, value, delta=delta)

def create_portfolio_overview_chart(summary):
    """Create portfolio overview donut chart"""
    if not summary['positions']:
        return None
    
    # Prepare data for donut chart
    stocks = []
    values = []
    colors = []
    
    for stock, position in summary['positions'].items():
        stocks.append(stock)
        values.append(position.market_value)
        colors.append(get_performance_color(position.unrealized_pnl))
    
    # Create donut chart
    fig = go.Figure(data=[go.Pie(
        labels=stocks,
        values=values,
        hole=0.4,
        hovertemplate='<b>%{label}</b><br>' +
                     'Value: $%{value:,.0f}<br>' +
                     'Percentage: %{percent}<br>' +
                     '<extra></extra>'
    )])
    
    fig.update_layout(
        title="Portfolio Allocation",
        showlegend=True,
        height=400
    )
    
    return fig

def create_performance_bar_chart(summary):
    """Create performance bar chart"""
    if not summary['positions']:
        return None
    
    stocks = []
    pnl_values = []
    pnl_percentages = []
    
    for stock, position in summary['positions'].items():
        stocks.append(stock)
        pnl_values.append(position.unrealized_pnl)
        pnl_pct = ((position.current_price / position.avg_cost - 1) * 100) if position.avg_cost > 0 else 0
        pnl_percentages.append(pnl_pct)
    
    # Create bar chart
    fig = go.Figure()
    
    # Add bars with conditional coloring
    colors = ['green' if x > 0 else 'red' if x < 0 else 'gray' for x in pnl_values]
    
    fig.add_trace(go.Bar(
        x=stocks,
        y=pnl_values,
        marker_color=colors,
        text=[f"{pct:.1f}%" for pct in pnl_percentages],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>' +
                     'P&L: $%{y:,.0f}<br>' +
                     'Return: %{text}<br>' +
                     '<extra></extra>'
    ))
    
    fig.update_layout(
        title="Stock Performance (P&L)",
        xaxis_title="Stock",
        yaxis_title="Unrealized P&L ($)",
        height=400
    )
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    return fig

def create_positions_table(summary):
    """Create positions table with franking information"""
    if not summary['positions']:
        return pd.DataFrame()
    
    data = []
    for stock, position in summary['positions'].items():
        pnl_pct = ((position.current_price / position.avg_cost - 1) * 100) if position.avg_cost > 0 else 0
        
        # Get franking information if available
        franking_info = {'franking_rate': 0, 'sector': 'Unknown'}
        if hasattr(st.session_state.tracker, 'get_stock_franking_info'):
            try:
                franking_info = st.session_state.tracker.get_stock_franking_info(stock)
            except:
                pass
        
        # Calculate effective yield (basic estimation)
        dividend_yield = 4.0  # Default 4% assumption
        effective_yield = dividend_yield * (1 + franking_info['franking_rate'] / 100 * 0.3)
        
        row_data = {
            'Stock': stock,
            'Quantity': f"{position.quantity:,}",
            'Avg Cost': format_currency(position.avg_cost),
            'Current Price': format_currency(position.current_price),
            'Market Value': format_currency(position.market_value),
            'Unrealized P&L': format_currency(position.unrealized_pnl),
            'Return %': format_percentage(pnl_pct)
        }
        
        # Add franking columns if franking calculator is available
        if hasattr(st.session_state.tracker, 'franking_calculator') and st.session_state.tracker.franking_calculator:
            row_data.update({
                'Franking Rate': f"{franking_info['franking_rate']:.0f}%",
                'Sector': franking_info['sector'],
                'Effective Yield': f"{effective_yield:.1f}%"
            })
        
        data.append(row_data)
    
    return pd.DataFrame(data)

def display_success_message(message):
    """Display success message"""
    st.success(f"✅ {message}")

def display_error_message(message):
    """Display error message"""
    st.error(f"❌ {message}")

def display_warning_message(message):
    """Display warning message"""
    st.warning(f"⚠️ {message}")

def display_info_message(message):
    """Display info message"""
    st.info(f"ℹ️ {message}")

def download_button(data, filename, label):
    """Create download button for data"""
    if isinstance(data, pd.DataFrame):
        csv = data.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{label}</a>'
        st.markdown(href, unsafe_allow_html=True)
    else:
        st.download_button(
            label=label,
            data=data,
            file_name=filename,
            mime='text/csv'
        )

def get_database_info():
    """Get database information"""
    conn = sqlite3.connect('portfolio.db')
    cursor = conn.cursor()
    
    try:
        # Get transaction count
        cursor.execute('SELECT COUNT(*) FROM transactions')
        transaction_count = cursor.fetchone()[0]
        
        # Get price history count
        cursor.execute('SELECT COUNT(*) FROM price_history')
        price_count = cursor.fetchone()[0]
        
        # Get date range
        cursor.execute('SELECT MIN(date), MAX(date) FROM price_history')
        date_range = cursor.fetchone()
        
        # Get stocks count
        cursor.execute('SELECT COUNT(DISTINCT stock) FROM transactions')
        stock_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'transactions': transaction_count,
            'price_points': price_count,
            'date_range': date_range,
            'stocks': stock_count
        }
    except Exception as e:
        conn.close()
        return {
            'transactions': 0,
            'price_points': 0,
            'date_range': (None, None),
            'stocks': 0
        }

def validate_transaction_input(stock, action, quantity, price):
    """Validate transaction input"""
    errors = []
    
    if not stock or len(stock.strip()) == 0:
        errors.append("Stock symbol is required")
    
    if action not in ['buy', 'sell']:
        errors.append("Action must be 'buy' or 'sell'")
    
    if quantity <= 0:
        errors.append("Quantity must be greater than 0")
    
    if price <= 0:
        errors.append("Price must be greater than 0")
    
    return errors

def add_transaction(stock, action, quantity, price, transaction_date):
    """Add transaction using existing functionality"""
    try:
        # Calculate total and fees
        total = quantity * price
        fees = st.session_state.tracker.calculate_brokerage(total)
        
        # Create CSV format for import
        csv_data = f"Date,Stock,Action,Quantity,Price,Total,Status\n{transaction_date},{stock},{action},{quantity},{price},{total},executed"
        
        # Import transaction
        st.session_state.tracker.import_transactions_from_csv(csv_data)
        
        return True, f"Transaction added: {action.title()} {quantity} shares of {stock} at ${price:.2f}"
    except Exception as e:
        return False, f"Error adding transaction: {str(e)}"

def update_prices(force=False):
    """Update prices using existing functionality"""
    try:
        summary = st.session_state.tracker.get_portfolio_summary(EODHD_API_KEY, True, force)
        st.session_state.portfolio_data = summary
        st.session_state.last_update = datetime.now()
        return True, "Prices updated successfully"
    except Exception as e:
        return False, f"Error updating prices: {str(e)}"

def get_chart_download_link(fig, filename):
    """Create download link for plotly chart"""
    img_bytes = fig.to_image(format="png", width=1200, height=800)
    b64 = base64.b64encode(img_bytes).decode()
    href = f'<a href="data:image/png;base64,{b64}" download="{filename}">Download Chart as PNG</a>'
    return href


def create_franking_credits_chart(franking_summary):
    """Create franking credits visualization chart"""
    if not franking_summary or 'stock_details' not in franking_summary:
        return None
    
    stock_details = franking_summary['stock_details']
    
    # Prepare data
    stocks = []
    franking_credits = []
    franking_rates = []
    sectors = []
    market_values = []
    
    for stock in stock_details:
        stocks.append(stock['stock'])
        franking_credits.append(stock['franking_credit'])
        franking_rates.append(stock['franking_rate'])
        sectors.append(stock['sector'])
        market_values.append(stock['market_value'])
    
    # Sort by franking credits descending
    sorted_data = sorted(zip(stocks, franking_credits, franking_rates, sectors, market_values), 
                        key=lambda x: x[1], reverse=True)
    stocks, franking_credits, franking_rates, sectors, market_values = zip(*sorted_data)
    
    # Create color mapping for franking rates
    colors = []
    for rate in franking_rates:
        if rate == 100:
            colors.append('#2E8B57')  # Green for 100% franked
        elif rate > 0:
            colors.append('#FFD700')  # Gold for partially franked
        else:
            colors.append('#DC143C')  # Red for unfranked
    
    # Create bar chart
    fig = go.Figure(data=[go.Bar(
        x=list(stocks),
        y=list(franking_credits),
        marker_color=colors,
        hovertemplate='<b>%{x}</b><br>' +
                      'Annual Franking Credits: $%{y:.2f}<br>' +
                      'Franking Rate: %{customdata[0]}%<br>' +
                      'Sector: %{customdata[1]}<br>' +
                      'Market Value: $%{customdata[2]:,.2f}<br>' +
                      '<extra></extra>',
        customdata=list(zip(franking_rates, sectors, market_values))
    )])
    
    fig.update_layout(
        title="Annual Franking Credits by Stock",
        xaxis_title="Stock",
        yaxis_title="Annual Franking Credits ($)",
        showlegend=False,
        height=500,
        xaxis={'categoryorder': 'total descending'}
    )
    
    return fig


def create_franking_by_sector_chart(franking_summary):
    """Create franking credits by sector pie chart"""
    if not franking_summary or 'stock_details' not in franking_summary:
        return None
    
    stock_details = franking_summary['stock_details']
    
    # Aggregate by sector
    sector_franking = {}
    sector_market_value = {}
    
    for stock in stock_details:
        sector = stock['sector']
        if sector not in sector_franking:
            sector_franking[sector] = 0
            sector_market_value[sector] = 0
        
        sector_franking[sector] += stock['franking_credit']
        sector_market_value[sector] += stock['market_value']
    
    # Prepare data for pie chart
    sectors = list(sector_franking.keys())
    franking_values = list(sector_franking.values())
    market_values = list(sector_market_value.values())
    
    # Create pie chart
    fig = go.Figure(data=[go.Pie(
        labels=sectors,
        values=franking_values,
        hovertemplate='<b>%{label}</b><br>' +
                      'Franking Credits: $%{value:.2f}<br>' +
                      'Market Value: $%{customdata:,.2f}<br>' +
                      'Percentage: %{percent}<br>' +
                      '<extra></extra>',
        customdata=market_values
    )])
    
    fig.update_layout(
        title="Franking Credits by Sector",
        height=400
    )
    
    return fig