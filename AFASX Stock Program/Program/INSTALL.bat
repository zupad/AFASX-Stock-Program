@echo off
title Elliot Fidge's Stock Tracker - Auto Installer
color 0A

echo.
echo ==========================================
echo   ELLIOT FIDGE'S STOCK TRACKER INSTALLER
echo            Version 2.0
echo ==========================================
echo.
echo This installer will automatically:
echo   1. Check for Python installation
echo   2. Install Python if needed
echo   3. Install required packages
echo   4. Test the installation
echo   5. Launch the stock tracker
echo.
pause

echo.
echo [1/5] Checking for Python installation...
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Python is already installed!
    python --version
    goto :check_pip
)

echo ❌ Python not found. Installing Python...
echo.

:: Check if we're on 64-bit or 32-bit system
if "%PROCESSOR_ARCHITECTURE%"=="AMD64" (
    set PYTHON_URL=https://www.python.org/ftp/python/3.11.6/python-3.11.6-amd64.exe
    set PYTHON_INSTALLER=python-3.11.6-amd64.exe
) else (
    set PYTHON_URL=https://www.python.org/ftp/python/3.11.6/python-3.11.6.exe
    set PYTHON_INSTALLER=python-3.11.6.exe
)

echo Downloading Python installer...
powershell -Command "& {Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%'}"

if not exist "%PYTHON_INSTALLER%" (
    echo ❌ Failed to download Python installer.
    echo Please manually install Python from https://python.org
    pause
    exit /b 1
)

echo Installing Python (this may take a few minutes)...
echo Please check "Add Python to PATH" when the installer opens!
echo.
start /wait %PYTHON_INSTALLER% /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

:: Clean up installer
del "%PYTHON_INSTALLER%" >nul 2>&1

:: Refresh environment variables
call refreshenv >nul 2>&1

echo Python installation complete!
echo.

:check_pip
echo [2/5] Checking pip installation...
echo.

:: Check if pip is available
pip --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ pip is available!
    pip --version
) else (
    echo Installing pip...
    python -m ensurepip --upgrade
    python -m pip install --upgrade pip
)

echo.
echo [3/5] Installing required packages...
echo.

:: Install requirements
echo Installing stock tracker dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ❌ Failed to install some packages.
    echo Trying with --user flag...
    python -m pip install --user -r requirements.txt
)

echo.
echo [4/5] Testing installation...
echo.

:: Test the installation
python afi_stock_tracker.py test >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Installation test passed!
) else (
    echo ⚠️ Installation test had issues, but continuing...
)

echo.
echo [5/5] Installation complete!
echo.
echo ==========================================
echo    ELLIOT FIDGE'S STOCK TRACKER
echo         READY TO USE!
echo ==========================================
echo.
echo Quick commands to try:
echo   python afi_stock_tracker.py
echo   python afi_stock_tracker.py analyze --symbol CBA
echo   python afi_stock_tracker.py test
echo.
echo Would you like to run a quick demo? (Y/N)
set /p demo="Enter choice: "

if /i "%demo%"=="Y" (
    echo.
    echo Running demo analysis for AFI...
    python afi_stock_tracker.py analyze --period 1mo
)

echo.
echo Installation complete! The Stock Tracker is ready to use.
echo Created by Elliot Fidge - Version 2.0
echo.
pause