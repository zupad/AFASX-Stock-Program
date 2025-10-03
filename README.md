# Elliot Fidge's Advanced Stock Tracker

**Professional ASX Stock Analysis Tool - Version 2.0**

Created by **Elliot Fidge** for comprehensive analysis of Australian Securities Exchange (ASX) stocks.

Made as a passion project that turned into something bigger than I expected

I created this originally to only be for the Australian Foundation stock, but then implemented the ability to track all ASX stocks

---

## What This License & Disclaimer

**Created by Elliot Fidge - Version 2.0 Advanced Edition**

**Important:** This tool is for educational and informational purposes only. Stock market investments carry risk. Always consult with financial professionals before making investment decisions.

*This software uses Yahoo Finance and other free data sources. No warranty is provided for data accuracy.*

---

**Powered by Elliot Fidge's Advanced Stock Tracker v2.0**
Analyze any ASX-listed stock with professional-grade reports including:

- **Real-time prices** and historical data analysis
- **Technical indicators** (RSI, Moving Averages, Bollinger Bands)
- **Financial performance** metrics (returns, volatility, Sharpe ratio)
- **Company information** (sector, industry, market cap)
- **Advanced analytics** and price predictions

## Quick Start Guide

### 1. Installation Options

#### Automatic Installation (Recommended)

**Windows Users (Choose One):**
```batch
# Option 1: Double-click this file
INSTALL.bat

# Option 2: Right-click and "Run with PowerShell"
INSTALL.ps1
```

**Linux/Mac Users:**
```bash
# Make executable and run
chmod +x install.sh
./install.sh
```

#### What the Auto-Installer Does:
- Detects and installs Python 3.8+ if needed
- Installs all required packages from `requirements.txt`
- Tests the installation automatically
- Offers to run a demo analysis
- Sets up the complete environment

#### Manual Installation
```bash
# Step 1: Ensure Python 3.8+ is installed
python --version

# Step 2: Install required packages
pip install -r requirements.txt

# Step 3: Test installation
python afi_stock_tracker.py test
```

### 2. **Run Analysis**
```bash
# Analyze AFI (default)
python afi_stock_tracker.py

# Analyze any ASX stock
python afi_stock_tracker.py analyze --symbol CBA
python afi_stock_tracker.py analyze --symbol BHP --period 6mo
```

### 3. **Get Help**
```bash
# Show all available commands
python afi_stock_tracker.py test
```

## Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `python afi_stock_tracker.py` | Default AFI analysis | Run without options |
| `analyze --symbol [STOCK]` | Analyze specific stock | `--symbol CBA` |
| `analyze --period [TIME]` | Set time period | `--period 6mo` |
| `dashboard` | Launch web interface | Opens in browser |
| `test` | Show all commands | Complete help guide |

**Available time periods:** `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `max`

## Supported Stocks

Works with **any ASX-listed stock** including:

| Symbol | Company Name |
|--------|--------------|
| **AFI** | Australian Foundation Investment Company |
| **CBA** | Commonwealth Bank of Australia |
| **BHP** | BHP Group Limited |
| **CSL** | CSL Limited |
| **WBC** | Westpac Banking Corporation |
| **ANZ** | Australia and New Zealand Banking Group |
| **NAB** | National Australia Bank |
| **TLS** | Telstra Corporation |
| **WES** | Wesfarmers Limited |
| **MQG** | Macquarie Group |

*And hundreds more ASX-listed companies!*

## Sample Output

```
Elliot Fidge's Stock Tracker - CBA.AX
Commonwealth Bank of Australia (CBA)
Advanced Stock Analysis Report
Generated: 2025-10-03 10:54:35
Powered by Elliot Fidge's Stock Tracker v2.0

Current Price Information
┌─────────────────┬─────────┐
│ Current Price   │ $170.10 │
│ 52-Week High    │ $170.95 │
│ 52-Week Low     │ $162.54 │
│ 1-Day Change    │ +0.17%  │
└─────────────────┴─────────┘

Technical Indicators
┌─────────────┬─────────┬────────────┐
│ RSI (14)    │ 52.89   │ Neutral    │
│ SMA (20)    │ $167.22 │ Above      │
│ SMA (50)    │ $nan    │ Below      │
└─────────────┴─────────┴────────────┘

Financial Performance
┌───────────────────┬─────────┐
│ Total Return      │ 0.03%   │
│ Annualized Return │ 0.39%   │
│ Volatility        │ 0.18%   │
│ Sharpe Ratio      │ 1.99%   │
└───────────────────┴─────────┘
```

## Features

### Core Analytics
- Real-time price data from Yahoo Finance
- Historical price analysis with multiple timeframes
- Technical indicators (RSI, SMA, EMA, MACD, Bollinger Bands)
- Financial performance metrics and risk analysis
- Company fundamental information

### User Experience
- Clean command-line interface with colored output
- Professional tables and charts
- Comprehensive error handling
- Automatic data saving to SQLite database
- Optional web dashboard interface

### Flexibility
- Analyze any ASX-listed stock
- Multiple time periods (1 day to maximum history)
- Customizable analysis parameters
- Export data capabilities

## Project Structure

```
Elliot Fidge's Stock Tracker/
├── afi_stock_tracker.py      # Main application
├── afi_dashboard.py          # Web dashboard interface
├── requirements.txt          # Python dependencies
├── README.md                 # Main documentation (this file)
│
├── Installation Files
├── INSTALL.bat              # Windows auto-installer (batch)
├── INSTALL.ps1              # Windows auto-installer (PowerShell)
├── install.sh               # Linux/Mac auto-installer
├── INSTALL.txt              # Manual installation guide
├── INSTALLATION_README.md   # Installation documentation
├── QUICKSTART.txt           # Quick start guide
├── run_tracker.bat          # Windows runner script
│
├── Directories
├── config/                  # Configuration files
├── data/                    # Database storage
├── logs/                    # Application logs
└── src/                     # Source code modules
    ├── apis/               # Data source APIs
    ├── analytics/          # Analysis modules
    ├── database/           # Database management
    └── visualization/      # Charts and dashboards
```

## Installation Files Reference

| File | Purpose | Platform | Usage |
|------|---------|----------|--------|
| **INSTALL.bat** | Auto-installer with GUI | Windows | Double-click to run |
| **INSTALL.ps1** | PowerShell auto-installer | Windows | Right-click → "Run with PowerShell" |
| **install.sh** | Auto-installer script | Linux/Mac | `chmod +x install.sh && ./install.sh` |
| **requirements.txt** | Python dependencies | All | `pip install -r requirements.txt` |
| **run_tracker.bat** | Quick launcher | Windows | Double-click to run tracker |
| **INSTALL.txt** | Manual installation guide | All | Read for manual setup steps |
| **INSTALLATION_README.md** | Installation documentation | All | Detailed installation instructions |
| **QUICKSTART.txt** | Quick start guide | All | Fast setup and usage guide |

### Which Installation Method to Choose?

- **First-time users:** Use `INSTALL.bat` (Windows) or `install.sh` (Linux/Mac)
- **Advanced users:** Use `INSTALL.ps1` (Windows PowerShell)
- **Manual setup:** Follow `INSTALL.txt` or `INSTALLATION_README.md`
- **Already installed:** Use `run_tracker.bat` for quick launching

## Requirements

- **Python 3.8 or higher**
- **Internet connection** (for stock data)
- **Windows, macOS, or Linux**

## Support

This tool was created by **Elliot Fidge** for personal and educational use.

For issues or questions:
1. Check the help guide: `python afi_stock_tracker.py test`
2. Review this README file
3. Ensure all requirements are installed correctly

---

## 📄 **License & Disclaimer**

**Created by Elliot Fidge - Version 2.0 Advanced Edition**

⚠️ **Important:** This tool is for educational and informational purposes only. Stock market investments carry risk. Always consult with financial professionals before making investment decisions.

*This software uses Yahoo Finance and other free data sources. No warranty is provided for data accuracy.*

---

**Powered by Elliot Fidge's Advanced Stock Tracker v2.0** 
