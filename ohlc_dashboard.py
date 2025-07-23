#!/usr/bin/env python3
"""
OHLC Analysis Dashboard for ASX Portfolio Tracker
Order simulation and optimal pricing analysis interface
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np

# Import our OHLC collector
from ohlc_collector import OHLCCollector, OHLCData, OptimalPricing

class OHLCDashboard:
    """Streamlit dashboard for OHLC analysis and order simulation"""
    
    def __init__(self, db_path: str = 'portfolio.db'):
        self.db_path = db_path
        self.collector = OHLCCollector(db_path)
    
    def get_portfolio_stocks(self) -> List[str]:
        """Get portfolio stocks for analysis"""
        return self.collector.get_portfolio_stocks_from_db()
    
    def get_portfolio_positions(self) -> pd.DataFrame:
        """Get current portfolio positions"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get current positions
            query = """
            SELECT 
                stock,
                SUM(CASE WHEN action = 'buy' THEN quantity ELSE -quantity END) as quantity,
                SUM(CASE WHEN action = 'buy' THEN total + fees ELSE -(total - fees) END) / 
                    SUM(CASE WHEN action = 'buy' THEN quantity ELSE -quantity END) as avg_cost
            FROM transactions 
            GROUP BY stock 
            HAVING SUM(CASE WHEN action = 'buy' THEN quantity ELSE -quantity END) > 0
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            return df
            
        except Exception as e:
            st.error(f"Error loading portfolio positions: {e}")
            return pd.DataFrame()
    
    def get_ohlc_summary(self, days: int = 30) -> pd.DataFrame:
        """Get OHLC summary for all portfolio stocks"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = """
            SELECT 
                stock,
                COUNT(*) as days_with_data,
                AVG(high_price - low_price) as avg_daily_range,
                AVG((high_price - low_price) / close_price * 100) as avg_range_pct,
                MAX(date) as latest_date,
                AVG(volume) as avg_volume
            FROM daily_ohlc 
            WHERE date >= date('now', '-{} days')
            GROUP BY stock
            ORDER BY avg_range_pct DESC
            """.format(days)
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            return df
            
        except Exception as e:
            st.error(f"Error loading OHLC summary: {e}")
            return pd.DataFrame()
    
    def get_optimal_pricing_summary(self, days: int = 30) -> pd.DataFrame:
        """Get optimal pricing opportunities summary"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = """
            SELECT 
                stock,
                COUNT(*) as analysis_days,
                AVG(missed_opportunity_buy) as avg_missed_buy,
                AVG(missed_opportunity_sell) as avg_missed_sell,
                AVG(price_range_pct) as avg_volatility,
                SUM(missed_opportunity_buy + missed_opportunity_sell) as total_missed_value,
                MAX(date) as latest_analysis
            FROM optimal_pricing_analysis 
            WHERE date >= date('now', '-{} days')
            GROUP BY stock
            ORDER BY total_missed_value DESC
            """.format(days)
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            return df
            
        except Exception as e:
            st.error(f"Error loading optimal pricing summary: {e}")
            return pd.DataFrame()
    
    def simulate_perfect_timing_portfolio(self, days: int = 30) -> Dict:
        """Simulate portfolio performance with perfect daily timing"""
        try:
            positions_df = self.get_portfolio_positions()
            if positions_df.empty:
                return {}
            
            conn = sqlite3.connect(self.db_path)
            
            results = {}
            total_current_value = 0
            total_optimal_value = 0
            total_missed_opportunities = 0
            
            for _, position in positions_df.iterrows():
                stock = position['stock']
                quantity = position['quantity']
                avg_cost = position['avg_cost']
                
                # Get latest OHLC data
                query = """
                SELECT * FROM daily_ohlc 
                WHERE stock = ? 
                ORDER BY date DESC 
                LIMIT 1
                """
                
                ohlc_data = pd.read_sql_query(query, conn, params=(stock,))
                
                if not ohlc_data.empty:
                    latest = ohlc_data.iloc[0]
                    current_price = latest['close_price']
                    optimal_sell_price = latest['high_price']
                    
                    current_value = quantity * current_price
                    optimal_value = quantity * optimal_sell_price
                    missed_opportunity = optimal_value - current_value
                    
                    total_current_value += current_value
                    total_optimal_value += optimal_value
                    total_missed_opportunities += missed_opportunity
                    
                    results[stock] = {
                        'quantity': quantity,
                        'avg_cost': avg_cost,
                        'current_price': current_price,
                        'optimal_price': optimal_sell_price,
                        'current_value': current_value,
                        'optimal_value': optimal_value,
                        'missed_opportunity': missed_opportunity,
                        'cost_basis': quantity * avg_cost
                    }
            
            conn.close()
            
            # Portfolio summary
            results['_portfolio_summary'] = {
                'total_current_value': total_current_value,
                'total_optimal_value': total_optimal_value,
                'total_missed_opportunities': total_missed_opportunities,
                'missed_opportunity_pct': (total_missed_opportunities / total_current_value * 100) if total_current_value > 0 else 0
            }
            
            return results
            
        except Exception as e:
            st.error(f"Error simulating perfect timing: {e}")
            return {}
    
    def create_volatility_chart(self, stock: str, days: int = 30) -> go.Figure:
        """Create volatility analysis chart for a stock"""
        ohlc_data = self.collector.get_ohlc_data(stock, days)
        
        if not ohlc_data:
            return None
        
        # Convert to DataFrame
        df_data = []
        for ohlc in ohlc_data:
            df_data.append({
                'date': ohlc.date,
                'open': ohlc.open_price,
                'high': ohlc.high_price,
                'low': ohlc.low_price,
                'close': ohlc.close_price,
                'volume': ohlc.volume,
                'range_pct': ((ohlc.high_price - ohlc.low_price) / ohlc.close_price) * 100
            })
        
        df = pd.DataFrame(df_data).sort_values('date')
        
        # Create candlestick chart
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=[f'{stock} - OHLC Price Action', 'Daily Volatility %'],
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3]
        )
        
        # Candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=df['date'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name=f'{stock} OHLC'
            ),
            row=1, col=1
        )
        
        # Volatility bar chart
        fig.add_trace(
            go.Bar(
                x=df['date'],
                y=df['range_pct'],
                name='Daily Range %',
                marker_color='orange',
                opacity=0.7
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            title=f'{stock} - Price Action & Volatility Analysis',
            xaxis_rangeslider_visible=False,
            height=600
        )
        
        return fig
    
    def create_missed_opportunities_chart(self) -> go.Figure:
        """Create portfolio-wide missed opportunities chart"""
        optimal_df = self.get_optimal_pricing_summary(30)
        
        if optimal_df.empty:
            return None
        
        # Sort by total missed value
        optimal_df = optimal_df.sort_values('total_missed_value', ascending=True)
        
        fig = go.Figure()
        
        # Missed buy opportunities (could have bought cheaper)
        fig.add_trace(go.Bar(
            y=optimal_df['stock'],
            x=optimal_df['avg_missed_buy'],
            name='Missed Buy Opportunities',
            orientation='h',
            marker_color='red',
            opacity=0.7
        ))
        
        # Missed sell opportunities (could have sold higher)
        fig.add_trace(go.Bar(
            y=optimal_df['stock'],
            x=optimal_df['avg_missed_sell'],
            name='Missed Sell Opportunities',
            orientation='h',
            marker_color='green',
            opacity=0.7
        ))
        
        fig.update_layout(
            title='Average Daily Missed Opportunities by Stock (Last 30 Days)',
            xaxis_title='Average Missed Opportunity ($)',
            yaxis_title='Stock',
            barmode='stack',
            height=600
        )
        
        return fig
    
    def create_portfolio_optimization_chart(self) -> go.Figure:
        """Create portfolio optimization visualization"""
        perfect_timing = self.simulate_perfect_timing_portfolio()
        
        if not perfect_timing or '_portfolio_summary' not in perfect_timing:
            return None
        
        # Prepare data for visualization
        stocks = []
        current_values = []
        optimal_values = []
        missed_opps = []
        
        for stock, data in perfect_timing.items():
            if stock != '_portfolio_summary':
                stocks.append(stock)
                current_values.append(data['current_value'])
                optimal_values.append(data['optimal_value'])
                missed_opps.append(data['missed_opportunity'])
        
        fig = go.Figure()
        
        # Current portfolio value
        fig.add_trace(go.Bar(
            x=stocks,
            y=current_values,
            name='Current Value',
            marker_color='blue',
            opacity=0.7
        ))
        
        # Optimal portfolio value (perfect timing)
        fig.add_trace(go.Bar(
            x=stocks,
            y=optimal_values,
            name='Perfect Timing Value',
            marker_color='gold',
            opacity=0.7
        ))
        
        # Add missed opportunity annotations
        for i, (stock, missed) in enumerate(zip(stocks, missed_opps)):
            fig.add_annotation(
                x=stock,
                y=optimal_values[i],
                text=f"+${missed:.0f}",
                showarrow=True,
                arrowhead=2,
                arrowcolor="red",
                font=dict(color="red", size=10)
            )
        
        summary = perfect_timing['_portfolio_summary']
        
        fig.update_layout(
            title=f'Portfolio: Current vs Perfect Timing<br>'
                  f'<sub>Total Missed Opportunity: ${summary["total_missed_opportunities"]:.0f} '
                  f'({summary["missed_opportunity_pct"]:.1f}%)</sub>',
            xaxis_title='Stock',
            yaxis_title='Portfolio Value ($)',
            barmode='group',
            height=500
        )
        
        return fig


def create_ohlc_dashboard():
    """Main OHLC dashboard interface"""
    
    st.header("📈 OHLC Analysis & Order Simulation")
    
    dashboard = OHLCDashboard()
    
    # Check if OHLC data is available
    if not dashboard.collector.is_enabled():
        st.warning("⚠️ OHLC collection is disabled. Enable it to access these features.")
        if st.button("Enable OHLC Collection"):
            conn = sqlite3.connect('portfolio.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE ohlc_config SET value = ? WHERE key = ?', ('true', 'enabled'))
            conn.commit()
            conn.close()
            st.rerun()
        return
    
    # Get portfolio stocks
    portfolio_stocks = dashboard.get_portfolio_stocks()
    
    if not portfolio_stocks:
        st.error("No portfolio stocks found. Add some transactions first.")
        return
    
    # OHLC data collection status
    ohlc_summary = dashboard.get_ohlc_summary()
    
    if ohlc_summary.empty:
        st.warning("🔄 No OHLC data found. Collect some data first!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 Collect OHLC Data Now"):
                with st.spinner("Collecting OHLC data..."):
                    from ohlc_collector import OHLCCollector
                    collector = OHLCCollector()
                    results = collector.collect_portfolio_ohlc(portfolio_stocks, prefer_yfinance=True)
                    
                    successful = sum(1 for success in results.values() if success)
                    st.success(f"✅ Collected OHLC data for {successful}/{len(portfolio_stocks)} stocks")
                    st.rerun()
        
        with col2:
            st.info("💡 OHLC collection uses Yahoo Finance primarily to save EODHD API calls")
        
        return
    
    # Main dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Portfolio Overview", 
        "🎯 Perfect Timing Analysis", 
        "📈 Individual Stock Analysis", 
        "⚙️ Order Simulation"
    ])
    
    with tab1:
        st.subheader("Portfolio OHLC Overview")
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Stocks with OHLC Data",
                len(ohlc_summary),
                delta=f"out of {len(portfolio_stocks)}"
            )
        
        with col2:
            avg_volatility = ohlc_summary['avg_range_pct'].mean()
            st.metric(
                "Average Daily Volatility",
                f"{avg_volatility:.2f}%"
            )
        
        with col3:
            latest_date = ohlc_summary['latest_date'].max()
            st.metric(
                "Latest OHLC Data",
                latest_date
            )
        
        # OHLC Summary Table
        st.subheader("OHLC Data Summary")
        
        display_df = ohlc_summary.copy()
        display_df['avg_daily_range'] = display_df['avg_daily_range'].apply(lambda x: f"${x:.3f}")
        display_df['avg_range_pct'] = display_df['avg_range_pct'].apply(lambda x: f"{x:.2f}%")
        display_df['avg_volume'] = display_df['avg_volume'].apply(lambda x: f"{x:,.0f}")
        
        display_df.columns = [
            'Stock', 'Days of Data', 'Avg Daily Range', 
            'Avg Volatility %', 'Latest Date', 'Avg Volume'
        ]
        
        st.dataframe(display_df, use_container_width=True)
    
    with tab2:
        st.subheader("🎯 Perfect Timing Analysis")
        
        # Portfolio optimization chart
        opt_chart = dashboard.create_portfolio_optimization_chart()
        if opt_chart:
            st.plotly_chart(opt_chart, use_container_width=True)
        
        # Missed opportunities breakdown
        missed_chart = dashboard.create_missed_opportunities_chart()
        if missed_chart:
            st.plotly_chart(missed_chart, use_container_width=True)
        
        # Perfect timing simulation details
        perfect_timing = dashboard.simulate_perfect_timing_portfolio()
        
        if perfect_timing and '_portfolio_summary' in perfect_timing:
            summary = perfect_timing['_portfolio_summary']
            
            st.subheader("Perfect Timing Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Current Portfolio Value",
                    f"${summary['total_current_value']:,.0f}"
                )
            
            with col2:
                st.metric(
                    "Perfect Timing Value",
                    f"${summary['total_optimal_value']:,.0f}"
                )
            
            with col3:
                st.metric(
                    "Missed Opportunity",
                    f"${summary['total_missed_opportunities']:,.0f}",
                    delta=f"{summary['missed_opportunity_pct']:.1f}%"
                )
            
            with col4:
                improvement = ((summary['total_optimal_value'] / summary['total_current_value']) - 1) * 100
                st.metric(
                    "Potential Improvement",
                    f"{improvement:.1f}%"
                )
    
    with tab3:
        st.subheader("📈 Individual Stock Analysis")
        
        # Stock selector
        selected_stock = st.selectbox("Select Stock for Analysis", portfolio_stocks)
        
        if selected_stock:
            # Volatility chart
            vol_chart = dashboard.create_volatility_chart(selected_stock)
            if vol_chart:
                st.plotly_chart(vol_chart, use_container_width=True)
            
            # Stock-specific metrics
            stock_ohlc = dashboard.collector.get_ohlc_data(selected_stock, 30)
            stock_optimal = dashboard.collector.get_optimal_pricing_analysis(selected_stock, 30)
            
            if stock_ohlc and stock_optimal:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Recent OHLC Data")
                    
                    recent_data = []
                    for ohlc in stock_ohlc[:10]:  # Last 10 days
                        recent_data.append({
                            'Date': ohlc.date,
                            'Open': f"${ohlc.open_price:.3f}",
                            'High': f"${ohlc.high_price:.3f}",
                            'Low': f"${ohlc.low_price:.3f}",
                            'Close': f"${ohlc.close_price:.3f}",
                            'Volume': f"{ohlc.volume:,}"
                        })
                    
                    st.dataframe(pd.DataFrame(recent_data), use_container_width=True)
                
                with col2:
                    st.subheader("Optimal Pricing Analysis")
                    
                    optimal_data = []
                    for opt in stock_optimal[:10]:  # Last 10 days
                        optimal_data.append({
                            'Date': opt.date,
                            'Close': f"${opt.actual_close:.3f}",
                            'Best Buy': f"${opt.optimal_buy_price:.3f}",
                            'Best Sell': f"${opt.optimal_sell_price:.3f}",
                            'Missed Buy': f"${opt.missed_opportunity_buy:.3f}",
                            'Missed Sell': f"${opt.missed_opportunity_sell:.3f}"
                        })
                    
                    st.dataframe(pd.DataFrame(optimal_data), use_container_width=True)
    
    with tab4:
        st.subheader("⚙️ Order Simulation")
        
        st.info("🚧 Order simulation features coming soon!")
        
        st.markdown("""
        **Planned Features:**
        - Stop-limit order simulation
        - Automated trading strategy backtesting  
        - Risk-adjusted order sizing
        - Multi-day strategy optimization
        - Portfolio rebalancing simulation
        """)
        
        # Placeholder for future order simulation interface
        if st.button("🎲 Simulate Random Stop-Limit Orders"):
            st.success("Simulation feature in development!")


if __name__ == "__main__":
    create_ohlc_dashboard()