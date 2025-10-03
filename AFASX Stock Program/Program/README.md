# 📈 Elliot Fidge's Advanced Stock Tracker

**Professional ASX Stock Analysis Tool - Version 2.0**

Created by **Elliot Fidge** for comprehensive analysis of Australian Securities Exchange (ASX) stocks.

---

## 🎯 **What This Tool Does**

Analyze any ASX-listed stock with professional-grade reports including:

- **📊 Real-time prices** and historical data analysis
- **📈 Technical indicators** (RSI, Moving Averages, Bollinger Bands)
- **💼 Financial performance** metrics (returns, volatility, Sharpe ratio)
- **🏢 Company information** (sector, industry, market cap)
- **🔮 Advanced analytics** and price predictions

## 🚀 **Quick Start Guide**

### 1. **Installation**
```bash
# Install required packages
pip install -r requirements.txt
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

## 📋 **Available Commands**

| Command | Description | Example |
|---------|-------------|---------|
| `python afi_stock_tracker.py` | Default AFI analysis | Run without options |
| `analyze --symbol [STOCK]` | Analyze specific stock | `--symbol CBA` |
| `analyze --period [TIME]` | Set time period | `--period 6mo` |
| `dashboard` | Launch web interface | Opens in browser |
| `test` | Show all commands | Complete help guide |

**Time Periods:** `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `max`

## 💡 **Supported Stocks**

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

## 📊 **Sample Output**

```
📊 Elliot Fidge's Stock Tracker - CBA.AX
📈 Commonwealth Bank of Australia (CBA)
Advanced Stock Analysis Report
Generated: 2025-10-03 10:54:35
Powered by Elliot Fidge's Stock Tracker v2.0

💰 Current Price Information
┌─────────────────┬─────────┐
│ Current Price   │ $170.10 │
│ 52-Week High    │ $170.95 │
│ 52-Week Low     │ $162.54 │
│ 1-Day Change    │ +0.17%  │
└─────────────────┴─────────┘

📈 Technical Indicators
┌─────────────┬─────────┬────────────┐
│ RSI (14)    │ 52.89   │ ⚪ Neutral │
│ SMA (20)    │ $167.22 │ 🟢 Above   │
│ SMA (50)    │ $nan    │ 🔴 Below   │
└─────────────┴─────────┴────────────┘

💼 Financial Performance
┌───────────────────┬─────────┐
│ Total Return      │ 0.03%   │
│ Annualized Return │ 0.39%   │
│ Volatility        │ 0.18%   │
│ Sharpe Ratio      │ 1.99%   │
└───────────────────┴─────────┘
```

## 🔧 **Features**

### **Core Analytics**
- Real-time price data from Yahoo Finance
- Historical price analysis with multiple timeframes
- Technical indicators (RSI, SMA, EMA, MACD, Bollinger Bands)
- Financial performance metrics and risk analysis
- Company fundamental information

### **User Experience**
- Beautiful command-line interface with colored output
- Professional tables and charts
- Comprehensive error handling
- Automatic data saving to SQLite database
- Optional web dashboard interface

### **Flexibility**
- Analyze any ASX-listed stock
- Multiple time periods (1 day to maximum history)
- Customizable analysis parameters
- Export data capabilities

## 📁 **Project Structure**

```
Elliot Fidge's Stock Tracker/
├── afi_stock_tracker.py    # Main application
├── requirements.txt        # Required packages
├── README.md              # This file
├── run_tracker.bat        # Windows batch file
├── config/                # Configuration files
├── src/                   # Source code modules
│   ├── apis/             # Data source APIs
│   ├── analytics/        # Analysis modules
│   ├── database/         # Database management
│   └── visualization/    # Charts and dashboards
└── data/                 # Database storage
```

## 🚨 **Requirements**

- **Python 3.8 or higher**
- **Internet connection** (for stock data)
- **Windows, macOS, or Linux**

## 📞 **Support**

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

**Powered by Elliot Fidge's Advanced Stock Tracker v2.0** 📈