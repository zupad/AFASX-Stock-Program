# Elliot Fidge's Stock Tracker - PowerShell Auto Installer
# Version 2.0 - Automatically installs Python, pip, and dependencies

# Set console title and colors
$Host.UI.RawUI.WindowTitle = "Elliot Fidge's Stock Tracker - Auto Installer"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  ELLIOT FIDGE'S STOCK TRACKER INSTALLER" -ForegroundColor Green  
Write-Host "           Version 2.0" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "This installer will automatically:" -ForegroundColor Yellow
Write-Host "  1. Check for Python installation" -ForegroundColor White
Write-Host "  2. Install Python if needed" -ForegroundColor White
Write-Host "  3. Install required packages" -ForegroundColor White
Write-Host "  4. Test the installation" -ForegroundColor White
Write-Host "  5. Launch the stock tracker" -ForegroundColor White
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $isAdmin) {
    Write-Host "⚠️  For best results, run as Administrator" -ForegroundColor Yellow
    Write-Host "   (Right-click and 'Run as administrator')" -ForegroundColor Yellow
    Write-Host ""
}

Read-Host "Press Enter to continue"

# Function to check if Python is installed
function Test-PythonInstalled {
    try {
        $pythonVersion = & python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            return $true, $pythonVersion
        }
    } catch {
        return $false, $null
    }
    return $false, $null
}

# Function to install Python
function Install-Python {
    Write-Host ""
    Write-Host "[1/5] Installing Python..." -ForegroundColor Cyan
    Write-Host ""
    
    # Determine architecture
    $arch = if ([Environment]::Is64BitOperatingSystem) { "amd64" } else { "win32" }
    $pythonVersion = "3.11.6"
    $installerName = "python-$pythonVersion-$arch.exe"
    $downloadUrl = "https://www.python.org/ftp/python/$pythonVersion/$installerName"
    
    Write-Host "Downloading Python $pythonVersion for $arch..." -ForegroundColor Yellow
    
    try {
        Invoke-WebRequest -Uri $downloadUrl -OutFile $installerName -UseBasicParsing
        Write-Host "✅ Downloaded Python installer" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to download Python installer" -ForegroundColor Red
        Write-Host "Please manually install Python from https://python.org" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    Write-Host "Installing Python (this may take a few minutes)..." -ForegroundColor Yellow
    Write-Host "Please wait..." -ForegroundColor Yellow
    
    # Install Python silently with PATH addition
    $installArgs = "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_doc=0"
    Start-Process -FilePath $installerName -ArgumentList $installArgs -Wait
    
    # Clean up installer
    Remove-Item $installerName -ErrorAction SilentlyContinue
    
    # Refresh environment variables
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    Write-Host "✅ Python installation complete!" -ForegroundColor Green
}

# Main installation process
Write-Host ""
Write-Host "[1/5] Checking for Python installation..." -ForegroundColor Cyan

$pythonInstalled, $pythonVersion = Test-PythonInstalled

if ($pythonInstalled) {
    Write-Host "✅ Python is already installed: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Python not found" -ForegroundColor Red
    Install-Python
    
    # Check again after installation
    Start-Sleep 3
    $pythonInstalled, $pythonVersion = Test-PythonInstalled
    if (-not $pythonInstalled) {
        Write-Host "❌ Python installation may have failed" -ForegroundColor Red
        Write-Host "Please restart your computer and try again" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host ""
Write-Host "[2/5] Checking pip installation..." -ForegroundColor Cyan

try {
    $pipVersion = & python -m pip --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ pip is available: $pipVersion" -ForegroundColor Green
    } else {
        Write-Host "Installing pip..." -ForegroundColor Yellow
        & python -m ensurepip --upgrade
        & python -m pip install --upgrade pip
    }
} catch {
    Write-Host "Installing pip..." -ForegroundColor Yellow
    & python -m ensurepip --upgrade
    & python -m pip install --upgrade pip
}

Write-Host ""
Write-Host "[3/5] Installing required packages..." -ForegroundColor Cyan

if (-not (Test-Path "requirements.txt")) {
    Write-Host "❌ requirements.txt not found in current directory" -ForegroundColor Red
    Write-Host "Please make sure you're running this from the stock tracker folder" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Installing stock tracker dependencies..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Yellow

try {
    & python -m pip install --upgrade pip
    & python -m pip install -r requirements.txt
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️ Some packages may have failed, trying with --user flag..." -ForegroundColor Yellow
        & python -m pip install --user -r requirements.txt
    }
    
    Write-Host "✅ Package installation complete!" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install packages" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "[4/5] Testing installation..." -ForegroundColor Cyan

try {
    $testOutput = & python afi_stock_tracker.py test 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Installation test passed!" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Installation test had issues, but continuing..." -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ Could not run test, but installation may still work" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[5/5] Installation complete!" -ForegroundColor Cyan
Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "   ELLIOT FIDGE'S STOCK TRACKER" -ForegroundColor Green
Write-Host "        READY TO USE!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Quick commands to try:" -ForegroundColor Yellow
Write-Host "  python afi_stock_tracker.py" -ForegroundColor White
Write-Host "  python afi_stock_tracker.py analyze --symbol CBA" -ForegroundColor White
Write-Host "  python afi_stock_tracker.py test" -ForegroundColor White
Write-Host ""

$demo = Read-Host "Would you like to run a quick demo? (Y/N)"

if ($demo -eq "Y" -or $demo -eq "y") {
    Write-Host ""
    Write-Host "Running demo analysis for AFI..." -ForegroundColor Cyan
    & python afi_stock_tracker.py analyze --period 1mo
}

Write-Host ""
Write-Host "Installation complete! The Stock Tracker is ready to use." -ForegroundColor Green
Write-Host "Created by Elliot Fidge - Version 2.0" -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to exit"