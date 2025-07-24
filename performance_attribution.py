#!/usr/bin/env python3
"""
Performance Attribution Analysis
Analyzes which stocks contributed most to portfolio performance vs ASX200
"""

import sqlite3
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px  # type: ignore
import plotly.graph_objects as go  # type: ignore
from plotly.subplots import make_subplots  # type: ignore

from portfolio_tracker import \
    ASXPortfolioTracker  # Import for consistent pricing


def calculate_stock_contributions():
    """Calculate each stock's contribution to total portfolio performance"""

    # Use ASXPortfolioTracker for consistent price retrieval (same as CLI dashboard)
    tracker = ASXPortfolioTracker()

    # Force price update to ensure we have current prices (same as CLI --update)
    positions = tracker.update_current_prices(use_api=False, force=False)

    # Convert to DataFrame format for existing analysis logic
    positions_data = []
    latest_price_data = []

    for stock, pos in positions.items():
        positions_data.append(
            {
                "stock": stock,
                "quantity": pos.quantity,
                "total_cost": pos.avg_cost * pos.quantity,
                "avg_cost": pos.avg_cost,  # Add avg_cost explicitly for return calculation
            }
        )
        latest_price_data.append({"stock": stock, "current_price": pos.current_price})

    positions_df = pd.DataFrame(positions_data)
    latest_prices_df = pd.DataFrame(latest_price_data)

    # Connect to database for historical data only
    conn = sqlite3.connect("portfolio.db")

    # Get initial prices (first available price for each stock)
    initial_prices_df = pd.read_sql_query(
        """
        SELECT DISTINCT stock, price as initial_price
        FROM price_history ph1
        WHERE date = (
            SELECT MIN(date) 
            FROM price_history ph2 
            WHERE ph2.stock = ph1.stock
        )
    """,
        conn,
    )

    conn.close()

    # Debug: Check if we have data
    if positions_df.empty:
        print("ERROR: No positions data found!")
        return pd.DataFrame()

    if latest_prices_df.empty:
        print("ERROR: No price data found!")
        return pd.DataFrame()

    # Merge price data (we already have avg_cost from positions, so skip the initial_prices merge)
    attribution_df = positions_df.merge(latest_prices_df, on="stock", how="left")

    # Debug: Check for missing price data
    missing_prices = attribution_df[attribution_df["current_price"].isna()]
    if not missing_prices.empty:
        print(
            f"WARNING: Missing current prices for: {missing_prices['stock'].tolist()}"
        )

    # Fill NaN prices with 0 temporarily to debug
    attribution_df["current_price"] = attribution_df["current_price"].fillna(0)

    # Calculate metrics for each stock
    attribution_df["current_value"] = (
        attribution_df["quantity"] * attribution_df["current_price"]
    )
    attribution_df["unrealized_pnl"] = (
        attribution_df["current_value"] - attribution_df["total_cost"]
    )

    # Only calculate returns for stocks with valid prices
    attribution_df["return_pct"] = 0.0
    valid_prices = attribution_df["current_price"] > 0
    attribution_df.loc[valid_prices, "return_pct"] = (
        attribution_df.loc[valid_prices, "current_price"]
        / attribution_df.loc[valid_prices, "avg_cost"]
        - 1
    ) * 100

    # Calculate weight in portfolio
    total_portfolio_value = attribution_df["current_value"].sum()
    if total_portfolio_value <= 0:
        print(f"ERROR: Total portfolio value is still {total_portfolio_value}")
        print("ERROR: This means current_price values are all 0 or NaN")
        # Return a placeholder DataFrame so we can see what's wrong
        attribution_df["weight"] = 0.0
        attribution_df["contribution_to_return"] = 0.0
        return attribution_df

    attribution_df["weight"] = (
        attribution_df["current_value"] / total_portfolio_value * 100
    )

    # Calculate contribution to total return
    attribution_df["contribution_to_return"] = (
        attribution_df["unrealized_pnl"] / attribution_df["total_cost"].sum()
    ) * 100

    # Sort by contribution
    attribution_df = attribution_df.sort_values(
        "contribution_to_return", ascending=False
    )

    return attribution_df


def create_attribution_waterfall_chart(attribution_df):
    """Create a waterfall chart showing stock contributions"""

    # Prepare data for waterfall chart
    stocks = attribution_df["stock"].tolist()
    contributions = attribution_df["contribution_to_return"].tolist()

    # Create waterfall chart
    fig = go.Figure()

    # Add bars for each stock
    colors = ["green" if x > 0 else "red" for x in contributions]

    fig.add_trace(
        go.Bar(
            x=stocks,
            y=contributions,
            marker_color=colors,
            name="Contribution to Return",
            hovertemplate="<b>%{x}</b><br>"
            + "Contribution: %{y:.3f}%<br>"
            + "<extra></extra>",
        )
    )

    # Update layout
    fig.update_layout(
        title="Stock Performance Attribution - Contribution to Total Return",
        xaxis_title="Stock",
        yaxis_title="Contribution to Portfolio Return (%)",
        template="plotly_white",
        height=600,
    )

    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

    return fig


def create_attribution_treemap(attribution_df):
    """Create a treemap showing position sizes and performance"""

    # Prepare data - use absolute values for size, color for performance
    attribution_df["abs_value"] = attribution_df["current_value"].abs()

    # Create treemap
    fig = px.treemap(
        attribution_df,
        path=["stock"],
        values="abs_value",
        color="return_pct",
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
        title="Portfolio Holdings - Size & Performance",
        labels={"return_pct": "Return %", "abs_value": "Position Value ($)"},
    )

    # Update hover template
    fig.update_traces(
        hovertemplate="<b>%{label}</b><br>"
        + "Position Value: $%{value:,.0f}<br>"
        + "Return: %{color:.2f}%<br>"
        + "<extra></extra>"
    )

    return fig


def create_attribution_scatter(attribution_df):
    """Create scatter plot of weight vs return"""

    fig = px.scatter(
        attribution_df,
        x="weight",
        y="return_pct",
        size="current_value",
        color="contribution_to_return",
        hover_name="stock",
        labels={
            "weight": "Portfolio Weight (%)",
            "return_pct": "Stock Return (%)",
            "contribution_to_return": "Contribution (%)",
        },
        title="Position Weight vs Performance",
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
    )

    # Add quadrant lines
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(
        x=attribution_df["weight"].mean(),
        line_dash="dash",
        line_color="gray",
        opacity=0.5,
    )

    # Update layout
    fig.update_layout(template="plotly_white", height=600)

    return fig


def generate_attribution_report():
    """Generate comprehensive attribution analysis"""

    print("📊 Calculating performance attribution...")

    # Calculate attribution
    attribution_df = calculate_stock_contributions()

    if attribution_df.empty:
        print("❌ No position data available for attribution analysis")
        return

    # Display summary
    print("\n📈 PERFORMANCE ATTRIBUTION SUMMARY:")
    print("=" * 60)

    # Top and bottom contributors
    top_contributor = attribution_df.iloc[0]
    bottom_contributor = attribution_df.iloc[-1]

    print(f"🏆 Top Contributor: {top_contributor['stock']}")
    print(f"   Return: {top_contributor['return_pct']:.2f}%")
    print(f"   Portfolio Weight: {top_contributor['weight']:.2f}%")
    print(f"   Contribution: {top_contributor['contribution_to_return']:.3f}%")

    print(f"📉 Bottom Contributor: {bottom_contributor['stock']}")
    print(f"   Return: {bottom_contributor['return_pct']:.2f}%")
    print(f"   Portfolio Weight: {bottom_contributor['weight']:.2f}%")
    print(f"   Contribution: {bottom_contributor['contribution_to_return']:.3f}%")

    # Portfolio composition
    print(f"\n📊 PORTFOLIO COMPOSITION:")
    print(f"Total Portfolio Value: ${attribution_df['current_value'].sum():,.2f}")
    print(f"Total Unrealized P&L: ${attribution_df['unrealized_pnl'].sum():,.2f}")
    print(
        f"Weighted Average Return: {(attribution_df['contribution_to_return']).sum():.2f}%"
    )

    # Detailed breakdown
    print(f"\n📋 DETAILED BREAKDOWN:")
    print(f"{'Stock':<6} {'Weight':<8} {'Return':<8} {'Contribution':<12} {'P&L':<12}")
    print("-" * 60)

    for _, row in attribution_df.iterrows():
        print(
            f"{row['stock']:<6} {row['weight']:<8.2f}% {row['return_pct']:<8.2f}% "
            f"{row['contribution_to_return']:<12.3f}% ${row['unrealized_pnl']:<12.0f}"
        )

    # Create visualizations
    print(f"\n📊 Generating attribution charts...")

    # Waterfall chart
    waterfall_fig = create_attribution_waterfall_chart(attribution_df)
    waterfall_filename = (
        f"attribution_waterfall_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    )
    waterfall_fig.write_html(waterfall_filename)
    waterfall_fig.write_image(waterfall_filename.replace(".html", ".png"))
    print(f"✅ Waterfall chart saved as {waterfall_filename}")

    # Treemap
    treemap_fig = create_attribution_treemap(attribution_df)
    treemap_filename = (
        f"attribution_treemap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    )
    treemap_fig.write_html(treemap_filename)
    treemap_fig.write_image(treemap_filename.replace(".html", ".png"))
    print(f"✅ Treemap chart saved as {treemap_filename}")

    # Scatter plot
    scatter_fig = create_attribution_scatter(attribution_df)
    scatter_filename = (
        f"attribution_scatter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    )
    scatter_fig.write_html(scatter_filename)
    scatter_fig.write_image(scatter_filename.replace(".html", ".png"))
    print(f"✅ Scatter plot saved as {scatter_filename}")

    # Summary insights
    print(f"\n🎯 KEY INSIGHTS:")

    # Concentration analysis
    top_3_weight = attribution_df.head(3)["weight"].sum()
    print(f"• Top 3 positions represent {top_3_weight:.1f}% of portfolio")

    # Winner/loser analysis
    winners = attribution_df[attribution_df["return_pct"] > 0]
    losers = attribution_df[attribution_df["return_pct"] < 0]

    if len(winners) > 0:
        print(
            f"• {len(winners)} positions are profitable (avg return: {winners['return_pct'].mean():.2f}%)"
        )
    if len(losers) > 0:
        print(
            f"• {len(losers)} positions are losing (avg return: {losers['return_pct'].mean():.2f}%)"
        )

    # Contribution analysis
    positive_contributors = attribution_df[attribution_df["contribution_to_return"] > 0]
    negative_contributors = attribution_df[attribution_df["contribution_to_return"] < 0]

    if len(positive_contributors) > 0:
        print(
            f"• {len(positive_contributors)} stocks contributed positively (+{positive_contributors['contribution_to_return'].sum():.3f}%)"
        )
    if len(negative_contributors) > 0:
        print(
            f"• {len(negative_contributors)} stocks contributed negatively ({negative_contributors['contribution_to_return'].sum():.3f}%)"
        )

    return attribution_df


if __name__ == "__main__":
    generate_attribution_report()
