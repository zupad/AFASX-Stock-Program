#!/bin/bash

# Elliot Fidge's Stock Tracker - Auto Installer for Linux/Mac
# Version 2.0 - Automatically installs Python, pip, and dependencies

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Clear screen and show header
clear
echo ""
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}  ELLIOT FIDGE'S STOCK TRACKER INSTALLER${NC}"
echo -e "${GREEN}           Version 2.0${NC}"
echo -e "${GREEN}==========================================${NC}"
echo ""
echo -e "${YELLOW}This installer will automatically:${NC}"
echo -e "  1. Check for Python installation"
echo -e "  2. Install Python if needed"
echo -e "  3. Install required packages"
echo -e "  4. Test the installation"
echo -e "  5. Launch the stock tracker"
echo ""

# Detect OS
OS="Unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
fi

echo -e "${BLUE}Detected OS: $OS${NC}"
echo ""
read -p "Press Enter to continue..."

# Function to check if Python is installed
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        return 0
    elif command -v python &> /dev/null; then
        python_version=$(python --version 2>&1)
        if [[ $python_version == *"Python 3"* ]]; then
            PYTHON_CMD="python"
            return 0
        fi
    fi
    return 1
}

# Function to install Python on Linux
install_python_linux() {
    echo -e "${YELLOW}Installing Python on Linux...${NC}"
    
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        sudo yum install -y python3 python3-pip
    elif command -v dnf &> /dev/null; then
        # Fedora
        sudo dnf install -y python3 python3-pip
    elif command -v pacman &> /dev/null; then
        # Arch Linux
        sudo pacman -S python python-pip
    else
        echo -e "${RED}❌ Could not detect package manager${NC}"
        echo -e "${YELLOW}Please install Python 3.8+ manually${NC}"
        exit 1
    fi
}

# Function to install Python on macOS
install_python_macos() {
    echo -e "${YELLOW}Installing Python on macOS...${NC}"
    
    if command -v brew &> /dev/null; then
        # Homebrew
        brew install python3
    else
        echo -e "${YELLOW}Homebrew not found. Installing Homebrew first...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        brew install python3
    fi
}

# Main installation process
echo ""
echo -e "${CYAN}[1/5] Checking for Python installation...${NC}"

if check_python; then
    python_version=$($PYTHON_CMD --version)
    echo -e "${GREEN}✅ Python is already installed: $python_version${NC}"
else
    echo -e "${RED}❌ Python 3 not found${NC}"
    
    if [[ $OS == "Linux" ]]; then
        install_python_linux
    elif [[ $OS == "macOS" ]]; then
        install_python_macos
    else
        echo -e "${RED}❌ Unsupported OS for automatic installation${NC}"
        echo -e "${YELLOW}Please install Python 3.8+ manually from https://python.org${NC}"
        exit 1
    fi
    
    # Check again after installation
    if check_python; then
        python_version=$($PYTHON_CMD --version)
        echo -e "${GREEN}✅ Python installation complete: $python_version${NC}"
    else
        echo -e "${RED}❌ Python installation failed${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${CYAN}[2/5] Checking pip installation...${NC}"

if $PYTHON_CMD -m pip --version &> /dev/null; then
    pip_version=$($PYTHON_CMD -m pip --version)
    echo -e "${GREEN}✅ pip is available: $pip_version${NC}"
else
    echo -e "${YELLOW}Installing pip...${NC}"
    $PYTHON_CMD -m ensurepip --upgrade
    $PYTHON_CMD -m pip install --upgrade pip
fi

echo ""
echo -e "${CYAN}[3/5] Installing required packages...${NC}"

if [[ ! -f "requirements.txt" ]]; then
    echo -e "${RED}❌ requirements.txt not found in current directory${NC}"
    echo -e "${YELLOW}Please make sure you're running this from the stock tracker folder${NC}"
    exit 1
fi

echo -e "${YELLOW}Installing stock tracker dependencies...${NC}"
echo -e "${YELLOW}This may take a few minutes...${NC}"

$PYTHON_CMD -m pip install --upgrade pip
if $PYTHON_CMD -m pip install -r requirements.txt; then
    echo -e "${GREEN}✅ Package installation complete!${NC}"
else
    echo -e "${YELLOW}⚠️ Some packages may have failed, trying with --user flag...${NC}"
    $PYTHON_CMD -m pip install --user -r requirements.txt
fi

echo ""
echo -e "${CYAN}[4/5] Testing installation...${NC}"

if $PYTHON_CMD afi_stock_tracker.py test &> /dev/null; then
    echo -e "${GREEN}✅ Installation test passed!${NC}"
else
    echo -e "${YELLOW}⚠️ Installation test had issues, but continuing...${NC}"
fi

echo ""
echo -e "${CYAN}[5/5] Installation complete!${NC}"
echo ""
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}   ELLIOT FIDGE'S STOCK TRACKER${NC}"
echo -e "${GREEN}        READY TO USE!${NC}"
echo -e "${GREEN}==========================================${NC}"
echo ""
echo -e "${YELLOW}Quick commands to try:${NC}"
echo -e "  $PYTHON_CMD afi_stock_tracker.py"
echo -e "  $PYTHON_CMD afi_stock_tracker.py analyze --symbol CBA"
echo -e "  $PYTHON_CMD afi_stock_tracker.py test"
echo ""

read -p "Would you like to run a quick demo? (Y/N): " demo

if [[ $demo == "Y" || $demo == "y" ]]; then
    echo ""
    echo -e "${CYAN}Running demo analysis for AFI...${NC}"
    $PYTHON_CMD afi_stock_tracker.py analyze --period 1mo
fi

echo ""
echo -e "${GREEN}Installation complete! The Stock Tracker is ready to use.${NC}"
echo -e "${YELLOW}Created by Elliot Fidge - Version 2.0${NC}"
echo ""
read -p "Press Enter to exit..."