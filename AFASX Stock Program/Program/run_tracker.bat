@echo off
title Elliot Fidge's Advanced Stock Tracker v2.0
color 0A

echo.
echo ==========================================
echo   ELLIOT FIDGE'S ADVANCED STOCK TRACKER
echo            Version 2.0
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo.
    echo Please install Python from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo [INFO] Python detected
echo.

REM Check if required packages are installed
echo [INFO] Checking required packages...
python -c "import yfinance, pandas, requests, rich, click" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing required packages...
    echo.
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install packages
        echo.
        echo Try running this command manually:
        echo python -m pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
    echo [SUCCESS] Packages installed successfully
    echo.
)

REM Run the advanced tracker
echo [INFO] Starting AFI Stock Tracker Advanced...
echo.

python afi_stock_tracker.py

if errorlevel 1 (
    echo.
    echo [ERROR] The application encountered an error
    echo.
    echo You can also try:
    echo 1. Run test_advanced.py to diagnose issues
    echo 2. Check the logs folder for error details
    echo 3. Ensure you have internet connection
    echo.
)

echo.
pause