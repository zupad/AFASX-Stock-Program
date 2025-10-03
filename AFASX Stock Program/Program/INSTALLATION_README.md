# 🚀 One-Click Installation

Elliot Fidge's Advanced Stock Tracker now includes **automatic installers** that handle everything for you!

## Windows Users (Choose One):

### Option 1: Batch File (Easiest)
```
Double-click: INSTALL.bat
```

### Option 2: PowerShell (Recommended)
```
Right-click: INSTALL.ps1 → "Run with PowerShell"
```

## Linux/Mac Users:

```bash
chmod +x install.sh
./install.sh
```

## What the Installer Does:

1. ✅ **Checks for Python** - Detects if Python 3.8+ is installed
2. ✅ **Installs Python** - Downloads and installs Python if missing
3. ✅ **Installs Packages** - Automatically installs all required dependencies
4. ✅ **Tests Installation** - Verifies everything works correctly
5. ✅ **Runs Demo** - Optional demo analysis of AFI stock

## After Installation:

Your stock tracker will be ready to use with these commands:

```bash
# Analyze AFI (default)
python afi_stock_tracker.py

# Analyze any ASX stock
python afi_stock_tracker.py analyze --symbol CBA

# Get full help
python afi_stock_tracker.py test
```

## Troubleshooting:

- **Windows**: If you get security warnings, right-click the installer and choose "Run as administrator"
- **Mac**: You might need to allow the script in System Preferences → Security & Privacy
- **Linux**: Make sure you have `curl` installed for downloading Python

**Created by Elliot Fidge - Version 2.0** 📈