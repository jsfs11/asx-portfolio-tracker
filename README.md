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
# Clone or download the files
cd claude_p_trader

# Install dependencies
pip install -r requirements.txt

# For enhanced visualization and ASX200 comparison (optional)
pip install plotly yfinance kaleido
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
2. Edit `config.py` and replace `"demo"` with your actual API key:

```python
EODHD_API_KEY = "your_actual_api_key_here"
```

**Note**: The system uses sample/stored prices by default. EODHD API is only called when using `--update` flag.

### Brokerage Fees

Default Australian brokerage structure (configurable in `config.py`):
- Minimum fee: $19.95 per trade
- Rate: 0.1% of transaction value
- Fee applied: `max(transaction_value × 0.001, 19.95)`

## Your Portfolio

Your current holdings from $25,000 AUD starting capital:

| Stock | Company | Shares | Purchase Price | Total Cost |
|-------|---------|---------|---------------|------------|
| WAX   | Warnex Mining | 872 | $1.175 | $1,044.55 |
| WAM   | WAM Capital | 910 | $1.63 | $1,503.25 |
| HLI   | Helloworld Travel | 349 | $4.97 | $1,754.48 |
| YMAX  | Ymax Group | 260 | $7.69 | $2,019.35 |
| WOW   | Woolworths | 40 | $31.16 | $1,266.35 |
| CBA   | Commonwealth Bank | 8 | $180.37 | $1,462.91 |
| CSL   | CSL Limited | 8 | $242.41 | $1,959.23 |
| LNW   | LendLease | 13 | $152.16 | $1,998.03 |
| DTR   | DTek Resources | 16,580 | $0.089 | $1,495.57 |
| SDR   | SiteOne Landscape | 562 | $4.44 | $2,515.23 |
| BHP   | BHP Group | 65 | $38.3 | $2,509.45 |
| NXT   | NextDC | 192 | $13.59 | $2,629.23 |
| XRO   | Xero | 16 | $176.33 | $2,841.23 |

**Total Invested**: ~$24,998.86 + $259.35 fees = $25,258.21

## File Structure

```
claude_p_trader/
├── portfolio_tracker.py     # Core portfolio tracking logic
├── dividend_tracker.py      # Dividend analysis and tracking
├── portfolio_dashboard.py   # Command-line interface
├── portfolio_vs_asx200.py   # Portfolio vs ASX200 comparison chart
├── config.py               # Configuration settings
├── sample_prices.py        # Sample prices for demo mode
├── bar.py                  # Portfolio visualization charts
├── bar2.py                 # Enhanced portfolio bar charts
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── portfolio.db           # SQLite database (created automatically)
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

## Development Roadmap

### Phase 1: Data Accuracy & Core Fixes (Week 1-2)
- **🔧 Date Alignment**: Fix ASX200 vs portfolio data synchronization
- **💰 Dividend Integration**: Include dividend payments in total returns
- **📊 Transaction Costs**: Factor brokerage fees into performance calculations
- **📈 Enhanced Visualization**: Improved chart styling and annotations

### Phase 2: Risk Analytics & Attribution (Week 3-4)
- **📊 Risk Metrics**: Sharpe ratio, maximum drawdown, beta calculation
- **🎯 Performance Attribution**: Stock-level contribution analysis
- **📈 Rolling Windows**: 1D, 1W, 1M performance comparisons
- **📊 Drawdown Charts**: Visualize portfolio decline periods

### Phase 3: Advanced Features (Month 2+)
- **🌐 Additional Data Sources**: Google Finance, broker API integrations
- **🏦 Franking Credits**: Full Australian tax credit tracking
- **⚠️ Risk Alerts**: Price and volatility alerts
- **📱 Web Interface**: Browser-based dashboard
- **🏢 Sector Analysis**: Industry allocation vs ASX200 sectors

### Current Status
- ✅ **Completed**: Portfolio vs ASX200 comparison, Force API updates
- 🔄 **In Progress**: Documentation updates, code organization
- 📋 **Next**: Date alignment fixes, dividend integration

### Dependencies
- **Short-term**: Standard Python libraries (pandas, numpy, sqlite3)
- **Medium-term**: Enhanced visualization (plotly, matplotlib)
- **Long-term**: Web framework (Flask/FastAPI), advanced analytics libraries

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
- Verify API key in `config.py`
- Check daily API call limit (20/day for free EODHD)
- Use `--force` flag to bypass API limits when needed
- Sample prices used when API unavailable

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