# ASX Portfolio Tracker

A comprehensive Python-based portfolio tracking system for Australian Stock Exchange (ASX) investments, featuring real-time price updates, dividend tracking, fee calculations, and performance analytics with both CLI and web interfaces.

## Features

- 🚀 **New User Onboarding**: Guided setup wizard for first-time users with configurable starting cash
- 📊 **Portfolio Tracking**: Track multiple ASX stock positions with cost basis and P&L
- 💰 **Cash Balance Tracking**: Real-time cash position monitoring with personalized starting capital
- 🏛️ **Franking Credits Analysis**: Comprehensive Australian tax credit calculations
- 💰 **CGT Analysis**: Capital Gains Tax tracking with 12-month discount calculations
- 📈 **OHLC Analysis**: Open/High/Low/Close data collection and analysis
- 🎯 **Perfect Timing Analysis**: Optimal pricing simulation and missed opportunities
- 🕐 **Historical Data**: Automated collection of 30-365 days of historical OHLC data
- 💰 **Fee Calculation**: Automatic brokerage fee calculation
- 📈 **Real-time Prices**: EODHD API integration with Yahoo Finance fallback
- 💵 **Dividend Tracking**: Monitor dividend yields and estimated income
- 🧮 **Tax Calculator**: Interactive tax optimization with franking benefits
- 📱 **Dual Interface**: Command line tools and modern web interface
- 💾 **Data Persistence**: SQLite database for transaction and price history
- 📤 **Export Functionality**: Complete data export including OHLC history
- 📊 **Performance Analysis**: Advanced analytics and risk metrics
- 📈 **Interactive Charts**: Candlestick charts with volatility analysis
- 🎯 **Sector Analysis**: Proper GICS sector classifications for all stocks
- 🔒 **Secure Configuration**: Environment-based API key management
- 🤖 **Automated Ticker Integration**: One-command setup for new ASX stocks

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

# Show franking credits analysis
python3 portfolio_dashboard.py --franking

# Update franking data from API
python3 portfolio_dashboard.py --update-franking

# Show CGT analysis (unrealized gains)
python3 portfolio_dashboard.py --cgt

# Generate detailed CGT report for tax year
python3 portfolio_dashboard.py --cgt-report 2024-2025

# Initialize CGT tracking from transactions
python3 portfolio_dashboard.py --update-cgt

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

# Add new ASX ticker with automated data collection
python3 add_new_ticker.py CHN

# Collect OHLC data for analysis
python3 ohlc_collector.py --enable
python3 ohlc_collector.py --all --save-api-calls

# Collect historical OHLC data (30 days recommended)
python3 ohlc_collector.py --historical 30 --save-api-calls

# Fill missing OHLC data gaps
python3 ohlc_collector.py --fill-gaps
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

### First Time Setup (New Users)

**🚀 For First-Time Users - Easy Setup Wizard:**

1. **Clone and install** (as above)
2. **Launch the web interface**: `streamlit run streamlit_app.py`
3. **Complete the setup wizard**: You'll be automatically guided through:
   - Setting your starting cash balance (no more hardcoded $25,000!)
   - Naming your portfolio
   - Learning the basic workflow
4. **Start tracking**: Add your first transaction and begin portfolio analysis

**The 2-minute setup wizard will:**
- ✅  Auto-detect that you're a new user
- ✅  Guide you through essential configuration  
- ✅  Set up your personalized cash balance
- ✅  Show you exactly what to do next

### Experienced Users

If you're already familiar with the system:
1. **Clone the repository**
2. **Set up API key** (optional - uses demo mode by default)  
3. **Install dependencies**
4. **Add your first transaction** directly

### Legacy Migration

Existing portfolios continue to work unchanged. The system gracefully handles:
- Previous hardcoded $25,000 starting cash amounts
- Existing transaction history and settings
- All current functionality without interruption

## File Structure

```
asx-portfolio-tracker/
├── portfolio_tracker.py       # Core portfolio tracking logic
├── dividend_tracker.py        # Dividend analysis and tracking
├── franking_calculator.py     # Franking credits and tax analysis
├── cgt_calculator.py          # Capital Gains Tax calculations
├── ohlc_collector.py          # OHLC data collection and analysis
├── ohlc_dashboard.py          # OHLC web interface components
├── add_new_ticker.py          # Automated ticker integration tool
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
- Integrates with franking credits analysis

### FrankingCalculator
- Comprehensive Australian tax credit calculations
- 50+ major ASX stocks franking rates database
- Tax optimization suggestions
- Effective yield calculations including franking benefits
- API integration framework for real-time updates

### CGTCalculator
- Australian Capital Gains Tax compliance and calculations
- Tax parcel tracking with FIFO/LIFO matching methods
- 12-month CGT discount eligibility tracking
- Historical transaction processing and CGT event creation
- Unrealized gains analysis with discount projections
- Loss carry-forward calculations and tax optimization suggestions

### Portfolio Dashboard
- Command-line interface
- Multiple viewing modes
- Interactive transaction entry
- Data export functionality
- Force API update capability

### OHLC Analysis System
- **Automated Data Collection**: Zero-API-call historical data via Yahoo Finance
- **Perfect Timing Simulation**: Calculate optimal buy/sell opportunities
- **Volatility Analysis**: Track daily price ranges and trading opportunities
- **Candlestick Charts**: Interactive OHLC visualization with volume data
- **Gap Filling**: Intelligent detection and filling of missing data
- **Historical Periods**: 7 days to 1 year of historical OHLC data

### Performance Analysis
- Portfolio performance tracking over time
- Interactive plotly charts (HTML + PNG output)
- Risk-adjusted performance metrics
- Attribution analysis for individual stocks
- Rolling performance windows
- OHLC-based perfect timing analysis

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
  Cash Balance:         $    X,XXX.XX  [Configurable via Setup Wizard]
  Total Portfolio:      $   XX,XXX.XX
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

FRANKING CREDITS ANALYSIS:
------------------------------------------------------------
Annual Franking Credits:  $      XXX.XX
Tax Benefit:             $      XXX.XX
Franking Efficiency:            XX.X%
Effective Tax Rate:             XX.X%

CGT ANALYSIS:
------------------------------------------------------------
Total Unrealized Gain:   $      XXX.XX
After CGT Discount:      $      XXX.XX
Potential CGT Liability: $      XXX.XX
CGT Discount Savings:    $      XXX.XX
```

## New User Experience

### 🚀 First-Time User Flow

**When you first launch the system:**

1. **Auto-Detection**: System detects you're a new user (no existing data)
2. **Welcome Screen**: Dashboard shows setup guidance instead of empty data
3. **Setup Wizard**: Complete 2-minute configuration via `🚀 Setup` page:
   - Configure starting cash balance (your actual amount, not hardcoded $25k)
   - Set portfolio name for personalization
   - Review next steps and tips
4. **Ready to Use**: Dashboard now shows your configured portfolio
5. **Add First Transaction**: Guided to add your first stock purchase

### ⚙️ Setup Wizard Features

- **Smart Defaults**: Reasonable starting values with easy customization
- **Validation**: Input validation with helpful error messages  
- **Visual Feedback**: Success animations and clear next steps
- **Re-configurable**: Existing users can re-run setup to change settings
- **Backward Compatible**: Existing portfolios unaffected by new features

## Adding Transactions

### Via Web Interface (Recommended for New Users)
1. Navigate to `💰 Add Transaction` page
2. Fill in stock details (symbol, quantity, price, date)
3. Preview transaction including fees
4. Submit to add to portfolio

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

Feel free to submit issues and enhancement requests. This is a paper trading tool for learning purposes.
