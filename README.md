# ASX Paper Trading Portfolio Tracker

A comprehensive Python-based portfolio tracking system for Australian Stock Exchange (ASX) paper trading, featuring real-time price updates, dividend tracking, fee calculations, and performance analytics.

## Features

- 📊 **Portfolio Tracking**: Track multiple ASX stock positions with cost basis and P&L
- 💰 **Fee Calculation**: Automatic brokerage fee calculation (minimum $19.95 + 0.1%)
- 📈 **Real-time Prices**: EODHD API integration with fallback sample prices
- 💵 **Dividend Tracking**: Monitor dividend yields and estimated annual income
- 📱 **Command Line Interface**: Easy-to-use CLI with multiple viewing options
- 💾 **Data Persistence**: SQLite database for transaction and price history
- 📤 **Export Functionality**: CSV export for portfolio and transaction data
- 📊 **Performance Comparison**: Portfolio vs ASX200 benchmark analysis with interactive charts
- 🎯 **Force API Updates**: Bypass daily API limits for fresh data when needed
- 📈 **Advanced Visualization**: Plotly-based interactive charts with performance metrics

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/asx-portfolio-tracker.git
cd asx-portfolio-tracker

# Set up API key (optional)
cp .env.example .env
# Edit .env with your API key or leave as 'demo'

# Install dependencies
pip install -r requirements_streamlit.txt

# Run web interface
streamlit run streamlit_app.py

# Or use CLI tools
python portfolio_dashboard.py
```

### Basic Usage

```bash
# View portfolio summary (uses sample/stored prices)
python3 portfolio_dashboard.py

# Show detailed positions (uses sample/stored prices)
python3 portfolio_dashboard.py --details

# Include dividend analysis
python3 portfolio_dashboard.py --dividends

# Update current prices from EODHD API (only when explicitly requested)
python3 portfolio_dashboard.py --update

# Force API update even if daily limit reached
python3 portfolio_dashboard.py --update --force

# Generate portfolio vs ASX200 performance comparison chart
python3 portfolio_vs_asx200.py

# Add new transaction interactively
python3 portfolio_dashboard.py --add

# Export portfolio data
python3 portfolio_dashboard.py --export
```

## Configuration

### API Setup (Optional)

1. Get a free EODHD API key from [eodhd.com](https://eodhd.com)
2. Copy `.env.example` to `.env` and add your API key:

```bash
cp .env.example .env
# Edit .env and add: EODHD_API_KEY=your_actual_key_here
```

**Note**: The system uses sample/stored prices by default. EODHD API is only called when using `--update` flag.

### Brokerage Fees

Default Australian brokerage structure (configurable in `config.py`):
- Minimum fee: $19.95 per trade
- Rate: 0.1% of transaction value
- Fee applied: `max(transaction_value × 0.001, 19.95)`

## Getting Started

### First Time Setup

1. **Clone the repository**
2. **Set up API key** (optional - uses demo mode by default)
3. **Install dependencies**
4. **Add your first transaction**

The system includes sample data to demonstrate functionality. You can clear this and add your own transactions using the CLI or web interface.

## File Structure

```
asx-portfolio-tracker/
├── portfolio_tracker.py       # Core portfolio tracking logic
├── dividend_tracker.py        # Dividend analysis and tracking
├── portfolio_dashboard.py     # Command-line interface
├── portfolio_vs_asx200.py     # Portfolio vs ASX200 comparison
├── performance_attribution.py # Stock contribution analysis
├── rolling_performance.py     # Rolling performance metrics
├── streamlit_app.py           # Web interface (main)
├── streamlit_utils.py         # Web interface utilities
├── config.py                  # Configuration settings
├── requirements_streamlit.txt # Dependencies for web interface
├── .env.example              # API key template
├── .gitignore                # Git ignore file
└── README.md                 # This file
```

## Key Components

### ASXPortfolioTracker
- Imports transactions from CSV
- Calculates positions and P&L
- Fetches real-time prices via API
- Manages SQLite database

### DividendTracker
- Tracks dividend history
- Calculates dividend yields
- Estimates annual dividend income
- Supports franking credits (future enhancement)

### Portfolio Dashboard
- Command-line interface
- Multiple viewing modes
- Interactive transaction entry
- Data export functionality
- Force API update capability

### Portfolio vs ASX200 Comparison
- Real-time ASX200 index data via yfinance
- Portfolio performance vs market benchmark
- Interactive plotly charts (HTML + PNG output)
- Risk-adjusted performance metrics
- Fallback to weighted ASX proxy using major stocks

## API Sources

### Primary: EODHD
- **Free Tier**: 20 calls/day, 1-year historical data
- **Format**: `{stock}.AX` (e.g., `CBA.AX`)
- **Endpoint**: `https://eodhd.com/api/real-time/`

### Secondary: yfinance
- **ASX200 Index Data**: ^AXJO symbol for market benchmark
- **Free**: No API limits or registration required
- **Reliable**: Yahoo Finance data feed
- **Format**: Standard ticker symbols

### Fallback Options
1. Stored price history from previous API calls
2. Weighted ASX proxy using major portfolio stocks
3. Sample prices for demo/development

## Sample Output

```
============================================================
           ASX PAPER TRADING PORTFOLIO
============================================================
Last Updated: 2025-07-11 19:58:49
API Calls Used Today: 0/20

PORTFOLIO OVERVIEW:
  Total Cost Basis:     $   25,258.21
  Current Market Value: $   25,280.74
  Total Fees Paid:      $      259.35
  Unrealized P&L:       $       22.53
  Total Return:                0.09% 📈

INDIVIDUAL POSITIONS:
Stock  Qty    Avg Cost   Current    Market Val   P&L          P&L %   
----------------------------------------------------------------------
WAX    872    $1.2208    $1.1800    $1028.96     $-35.54      -3.34  % 🔴
WAM    910    $1.6738    $1.6500    $1501.50     $-21.70      -1.42  % 🔴
...

DIVIDEND ANALYSIS:
------------------------------------------------------------
WAM    Yield:  2.12%  Est. Annual: $   31.85
WOW    Yield:  1.71%  Est. Annual: $   22.00
CBA    Yield:  1.30%  Est. Annual: $   19.20
BHP    Yield:  4.86%  Est. Annual: $  123.50

Total Estimated Annual Dividends: $196.55
Portfolio Dividend Yield: 0.78%
```

## Adding Transactions

### Via Command Line
```bash
python3 portfolio_dashboard.py --add
```

### Via CSV Import
Modify the CSV data in `portfolio_dashboard.py` or create your own CSV file:

```csv
Date,Stock,Action,Quantity,Price,Total,Status
2025-07-11,BHP,buy,100,39.50,3950.00,executed
2025-07-11,CBA,sell,4,185.00,740.00,executed
```

## Visualization Outputs

The system generates several types of charts and visualizations:

### Portfolio vs ASX200 Comparison
- **Interactive HTML**: `portfolio_vs_asx200_YYYYMMDD_HHMMSS.html`
- **Static PNG**: `portfolio_vs_asx200_YYYYMMDD_HHMMSS.png`
- **Performance Metrics**: Outperformance calculation, volatility comparison
- **Risk-adjusted Analysis**: Sharpe ratio, maximum drawdown (when sufficient data)

### Portfolio Holdings Charts
- **Market Value Bar Chart**: `portfolio_holdings_bar.png`
- **Interactive Plotly Charts**: Hover details, zoom, pan functionality
- **Export Ready**: High-resolution PNG for reports

## Troubleshooting

### API Issues
- Verify API key in `.env` file
- Check daily API call limit (20/day for free EODHD)
- Use `--force` flag to bypass API limits when needed
- Demo mode works without API key

### Visualization Issues
- Install plotly and dependencies: `pip install plotly yfinance kaleido`
- Check that charts are saved to current directory
- Verify browser can open HTML files for interactive charts

### Database Issues
- Delete `portfolio.db` to reset database
- Check SQLite installation
- Verify transaction data integrity

### Import Errors
- Verify CSV format matches expected structure
- Check transaction data for correct data types
- Ensure numeric values don't contain currency symbols

## License

This project is for educational/personal use. Please verify any stock prices and dividend data independently before making investment decisions.

## Contributing

Feel free to submit issues and enhancement requests. This is a paper trading tool for learning purposes.
