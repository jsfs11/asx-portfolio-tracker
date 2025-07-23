# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.4.0] - 2025-07-23

### Added
- 🚀 **New User Onboarding System**: Complete first-time user setup wizard
- 🎯 **Smart User Detection**: Automatic detection of new vs existing users
- 🏠 **Dashboard Integration**: New user welcome flow with guided setup
- 💰 **Configurable Starting Cash**: No more hardcoded $25,000 assumption
- 📝 **Portfolio Personalization**: Custom portfolio naming and preferences
- 🎛️ **Setup Wizard Interface**: Intuitive 2-minute configuration process
- 🔄 **Re-setup Capability**: Existing users can reconfigure their settings

### Enhanced
- **Dashboard Experience**: New users see welcome message with setup guidance
- **Sidebar Navigation**: Visual indicators for incomplete setup
- **Cash Balance Calculation**: Now uses user-configured starting cash amount
- **Backward Compatibility**: Existing portfolios work unchanged with graceful defaults
- **User Settings Management**: Persistent storage of user preferences and setup status

### Technical
- New `user_settings` database table for onboarding and preferences
- Enhanced `ASXPortfolioTracker` with user detection methods (`is_new_user()`, `has_any_data()`)
- Updated cash balance calculation to use stored starting cash values
- Added user settings management methods (`initialize_user_settings()`, `get_user_settings()`)
- Safe database schema additions with backward compatibility

### UI/UX Improvements
- Setup wizard with clear instructions and tips
- Visual feedback with success messages and balloons
- Guided next steps after setup completion
- Prominent setup prompts for new users in sidebar and dashboard

## [2.3.0] - 2025-07-23

### Added
- 📈 **OHLC Analysis System**: Complete Open/High/Low/Close data collection and analysis
- 🎯 **Perfect Timing Analysis**: Portfolio simulation with optimal daily execution
- 🕐 **Historical Data Collection**: Automated collection of 30-365 days of OHLC data
- 📊 **Interactive Candlestick Charts**: Rich price action visualization with volume data
- ⚡ **Zero-API-Call Collection**: Yahoo Finance primary with EODHD fallback strategy
- 🔍 **Gap Filling System**: Intelligent detection and filling of missing OHLC data
- 💰 **Missed Opportunities Tracking**: Calculate potential gains from perfect timing
- 📈 **Volatility Analysis**: Daily price range and trading opportunity identification
- 🤖 **Automated Ticker Integration**: One-command setup for new ASX stocks with full data population
- 🎛️ **OHLC Dashboard**: Dedicated web interface with 4 analysis tabs

### Enhanced
- **Streamlit Interface**: New "📈 OHLC Analysis" page with portfolio optimization insights
- **API Efficiency**: Yahoo Finance prioritized to save EODHD API calls (18/20 calls saved)
- **Data Export**: Enhanced ZIP export now includes OHLC historical data
- **Portfolio Analysis**: Perfect timing simulation showing potential portfolio improvements
- **Stock Analysis**: Individual stock volatility and optimal pricing analysis

### Technical
- New `ohlc_collector.py` module with comprehensive OHLC data management
- New `ohlc_dashboard.py` with advanced visualization components
- New `add_new_ticker.py` for automated ticker integration
- Database schema extensions for OHLC storage (`daily_ohlc`, `optimal_pricing_analysis`)
- Yahoo Finance integration with period-based historical data fetching
- Configurable data retention and cleanup systems

### CLI Enhancements
- `python ohlc_collector.py --historical 30`: Collect 30 days of historical data
- `python ohlc_collector.py --fill-gaps`: Fill missing data automatically
- `python ohlc_collector.py --save-api-calls`: Yahoo Finance only mode
- `python add_new_ticker.py CHN`: Automated ticker setup with data population

## [2.2.1] - 2025-07-17

### Fixed
- Fixed type checking errors in franking_calculator.py, dividend_tracker.py, and portfolio_dashboard.py
- Resolved mypy compatibility issues for better code quality and IDE support

## [2.2.0] - 2025-07-17

### Added
- 💰 **Capital Gains Tax (CGT) Analysis**: Complete Australian CGT compliance system
- 📊 **Tax Parcel Tracking**: FIFO/LIFO matching with accurate cost base calculations
- 🎯 **12-Month CGT Discount**: Automatic eligibility tracking and discount calculations
- 📈 **Unrealized Gains Analysis**: Real-time CGT liability projections
- 📋 **CGT Reporting**: Detailed annual tax reports for ATO compliance
- 🔄 **Historical Processing**: Automatic CGT event creation from transaction history
- 💸 **Tax Optimization**: Loss harvesting and discount timing suggestions
- 🖥️ **Dedicated CGT Interface**: Full-featured web dashboard for CGT analysis
- 📱 **CLI CGT Commands**: `--cgt`, `--cgt-report`, `--update-cgt` flags

### Enhanced
- Enhanced transaction processing to include historical sales in CGT calculations
- Added comprehensive CGT analysis to Streamlit web interface
- Improved tax optimization with combined franking credits and CGT insights
- Extended CLI with professional CGT reporting capabilities

### Technical
- New `cgt_calculator.py` module with complete Australian tax compliance
- Database schema extensions for tax parcels and CGT events tracking
- Chronological transaction processing for accurate cost basis calculations
- Proportional cost base allocation including brokerage fees

## [2.1.0] - 2025-07-16

### Added
- 🏛️ **Franking Credits Analysis**: Comprehensive Australian tax credit calculations
- 💰 **Cash Balance Tracking**: Real-time cash position monitoring
- 🧮 **Tax Calculator**: Interactive tax optimization tool
- 📊 **Enhanced Visualizations**: Plotly charts for franking credits and sector analysis
- 🔄 **API Integration Framework**: Extensible system for real-time franking data updates
- 🎯 **Sector Classifications**: Proper GICS sector mapping for all portfolio stocks
- 📈 **Effective Yield Calculations**: Tax-adjusted yield metrics including franking benefits

### Enhanced
- Updated portfolio dashboard with franking analysis (`--franking` flag)
- Enhanced web interface with dedicated franking credits pages
- Improved export functionality with franking data inclusion
- Extended static database with 50+ major ASX stocks franking information

### Fixed
- Resolved $0.00 market values in franking exports
- Corrected sector classifications for HLI, YMAX, LNW, DTR, SDR, PME
- Fixed cash balance calculations to include starting capital

## [2.0.0] - 2025-07-15

### Added
- Streamlit web interface for modern GUI experience
- Performance attribution analysis
- Rolling performance metrics
- Advanced risk calculations (Sharpe ratio, maximum drawdown, beta)
- Interactive Plotly charts with export capabilities
- Environment-based configuration for API keys
- Docker deployment support
- Comprehensive documentation suite

### Changed
- Improved security with environment variable configuration
- Enhanced CLI interface with force update capability
- Modernized codebase architecture
- Updated documentation for public repository

### Security
- Moved API keys to environment variables
- Added .gitignore for sensitive files
- Implemented secure deployment practices

## [1.0.0] - 2025-07-10

### Added
- Initial release with core portfolio tracking
- EODHD API integration for real-time prices
- SQLite database for data persistence
- Basic CLI interface
- CSV import/export functionality
- Dividend tracking capabilities
- Australian brokerage fee calculations