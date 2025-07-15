# ASX Portfolio Tracker

A comprehensive Python-based portfolio tracking system for Australian Stock Exchange (ASX) investments, featuring real-time price updates, dividend tracking, fee calculations, and performance analytics with both CLI and web interfaces.

## Features

- 📊 **Portfolio Tracking**: Track multiple ASX stock positions with cost basis and P&L
- 💰 **Fee Calculation**: Automatic brokerage fee calculation
- 📈 **Real-time Prices**: EODHD API integration with demo mode fallback
- 💵 **Dividend Tracking**: Monitor dividend yields and estimated income
- 📱 **Dual Interface**: Command line tools and modern web interface
- 💾 **Data Persistence**: SQLite database for transaction and price history
- 📤 **Export Functionality**: CSV export for portfolio and transaction data
- 📊 **Performance Analysis**: Advanced analytics and risk metrics
- 📈 **Interactive Charts**: Plotly-based visualizations with export capabilities
- 🔒 **Secure Configuration**: Environment-based API key management

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

# Generate performance analysis charts
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

Configurable brokerage fee structure:
- Supports minimum fee + percentage models
- Default Australian brokerage calculations
- Customizable via configuration files

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

### Performance Analysis
- Portfolio performance tracking over time
- Interactive plotly charts (HTML + PNG output)
- Risk-adjusted performance metrics
- Attribution analysis for individual stocks
- Rolling performance windows

## API Sources

### Primary: EODHD
- **Free Tier**: 20 calls/day, 1-year historical data
- **Format**: `{stock}.AX` (e.g., `CBA.AX`)
- **Endpoint**: `https://eodhd.com/api/real-time/`

### Secondary: yfinance
- **Market Data**: Additional market data access
- **Free**: No API limits or registration required
- **Reliable**: Yahoo Finance data feed
- **Format**: Standard ticker symbols

### Fallback Options
1. Stored price history from previous API calls
2. Demo mode with sample data
3. Cached data for offline analysis

## Sample Output

```
============================================================
           ASX PORTFOLIO TRACKER
============================================================
Last Updated: 2025-07-15 10:30:15
API Calls Used Today: 5/20

PORTFOLIO OVERVIEW:
  Total Cost Basis:     $   XX,XXX.XX
  Current Market Value: $   XX,XXX.XX
  Total Fees Paid:      $      XXX.XX
  Unrealized P&L:       $      XXX.XX
  Total Return:                X.XX% 📈

INDIVIDUAL POSITIONS:
Stock  Qty    Avg Cost   Current    Market Val   P&L          P&L %   
----------------------------------------------------------------------
XXXX   XXX    $X.XXXX    $X.XXXX    $XXXX.XX     $XXX.XX      X.XX % 🟢
XXXX   XXX    $X.XXXX    $X.XXXX    $XXXX.XX     $XXX.XX      X.XX % 🔴
...

DIVIDEND ANALYSIS:
------------------------------------------------------------
XXXX   Yield:  X.XX%  Est. Annual: $   XX.XX
XXXX   Yield:  X.XX%  Est. Annual: $   XX.XX

Total Estimated Annual Dividends: $XXX.XX
Portfolio Dividend Yield: X.XX%
```

## Adding Transactions

### Via Command Line
```bash
python3 portfolio_dashboard.py --add
```

### Via CSV Import
Create a CSV file with your transaction data:

```csv
Date,Stock,Action,Quantity,Price,Total,Status
YYYY-MM-DD,STOCK,buy,100,XX.XX,XXXX.XX,executed
YYYY-MM-DD,STOCK,sell,50,XX.XX,XXXX.XX,executed
```

## Architecture

### Core Components
- **Data Layer**: SQLite database for transactions and price history
- **Analysis Engine**: Portfolio calculations and performance metrics
- **Visualization**: Interactive charts and reports
- **Interfaces**: CLI tools and web dashboard

### Technology Stack
- **Backend**: Python 3.9+, SQLite
- **Data**: pandas, numpy for calculations
- **Charts**: Plotly for interactive visualizations
- **Web UI**: Streamlit for modern interface
- **APIs**: EODHD, yfinance for market data

### Extensibility
- Modular design for easy feature additions
- Plugin architecture for new data sources
- Configurable fee structures and calculations
- API abstraction for multiple data providers

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Support

- 📚 Check the documentation in the `/docs` folder
- 🐛 Report bugs via GitHub Issues
- 💡 Request features via GitHub Issues
- 💬 Join discussions in GitHub Discussions
=======
Feel free to submit issues and enhancement requests. This is a paper trading tool for learning purposes.
>>>>>>> 2eaaebfb8b14e0636d0b633b83b3138aebecd3b5
