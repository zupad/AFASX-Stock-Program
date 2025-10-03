#!/usr/bin/env python3
"""
Elliot Fidge's Advanced Stock Tracker
Comprehensive stock tracking system with multiple APIs, technical analysis, and portfolio management

Author: Elliot Fidge
Version: 2.0 Advanced Edition
Specializing in AFI (Australian Foundation Investment Company) and ASX stocks
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.layout import Layout
from rich.live import Live
import pandas as pd

# Add src directory to path
sys.path.append(str(Path(__file__).parent / 'src'))

# Core imports with graceful degradation
console = Console()

try:
    from config import config
    from src.database import DatabaseManager
    from src.apis.yahoo_client import YahooFinanceClient
    from src.analytics.technical_analyzer import TechnicalAnalyzer
    from src.analytics.financial_analyzer import FinancialAnalyzer
    
    # Optional imports
    try:
        from src.apis.alpha_vantage_client import AlphaVantageClient
        ALPHA_VANTAGE_AVAILABLE = True
        console.print("✅ Alpha Vantage API available")
    except ImportError:
        ALPHA_VANTAGE_AVAILABLE = False
        console.print("⚠️ Alpha Vantage API not available (optional)")
    
    try:
        from src.apis.news_client import NewsClient
        NEWS_CLIENT_AVAILABLE = True
        console.print("✅ News API available")
    except ImportError:
        NEWS_CLIENT_AVAILABLE = False
        console.print("⚠️ News API not available (optional)")

    try:
        import streamlit as st
        import plotly.graph_objects as go
        import plotly.express as px
        VISUALIZATION_AVAILABLE = True
        console.print("✅ Visualization libraries available")
    except ImportError:
        VISUALIZATION_AVAILABLE = False
        console.print("⚠️ Visualization libraries not available (optional)")

    try:
        from src.analytics.predictive_analyzer import PredictiveAnalyzer
        PREDICTION_AVAILABLE = True
        console.print("✅ Predictive analytics available")
    except ImportError:
        PREDICTION_AVAILABLE = False
        console.print("⚠️ Predictive analytics not available (optional)")

except ImportError as e:
    console.print(f"[red]❌ Import error: {e}[/]")
    console.print("[yellow]⚠️ Running in basic mode[/]")
    sys.exit(1)

# Configure logging
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'afi_tracker.log'),
        logging.StreamHandler()
    ]
)

class ElliotFidgeStockTracker:
    """Elliot Fidge's Advanced Stock Tracker with multiple data sources and analytics"""
    
    def __init__(self, symbol="AFI"):
        self.console = Console()
        self.symbol = symbol.upper()
        self.logger = logging.getLogger(__name__)
        
        # Ensure ASX symbols have .AX suffix for Yahoo Finance
        if not self.symbol.endswith('.AX') and len(self.symbol) <= 4 and self.symbol.isalpha():
            self.symbol += '.AX'
        
        # Initialize components
        self.db_manager = DatabaseManager()
        self.yahoo_client = YahooFinanceClient()
        self.tech_analyzer = TechnicalAnalyzer()
        self.fin_analyzer = FinancialAnalyzer()
        
        # Optional components
        self.alpha_vantage_client = None
        self.news_client = None
        self.predictive_analyzer = None
        
        # Initialize optional components if available
        if ALPHA_VANTAGE_AVAILABLE and config.has_api_key('alpha_vantage'):
            try:
                self.alpha_vantage_client = AlphaVantageClient()
                self.console.print("✅ Alpha Vantage client initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Alpha Vantage: {e}")
    
    def _get_display_name(self) -> str:
        """Get display name for the stock symbol"""
        symbol_names = {
            "AFI.AX": "Australian Foundation Investment Company (AFI)",
            "CBA.AX": "Commonwealth Bank of Australia (CBA)",
            "BHP.AX": "BHP Group Limited (BHP)",
            "CSL.AX": "CSL Limited (CSL)",
            "WBC.AX": "Westpac Banking Corporation (WBC)",
            "ANZ.AX": "Australia and New Zealand Banking Group (ANZ)",
            "NAB.AX": "National Australia Bank (NAB)",
            "TLS.AX": "Telstra Corporation (TLS)",
            "WES.AX": "Wesfarmers Limited (WES)",
            "MQG.AX": "Macquarie Group (MQG)"
        }
        return symbol_names.get(self.symbol, f"{self.symbol.replace('.AX', '')} Stock Analysis")

        if NEWS_CLIENT_AVAILABLE:
            try:
                self.news_client = NewsClient()
                self.console.print("✅ News client initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize News client: {e}")
        
        if PREDICTION_AVAILABLE:
            try:
                self.predictive_analyzer = PredictiveAnalyzer()
                self.console.print("✅ Predictive analyzer initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Predictive analyzer: {e}")

    def get_comprehensive_data(self, period: str = '1y') -> Dict[str, Any]:
        """Get comprehensive stock data from all sources"""
        data = {}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            # Yahoo Finance data (primary)
            task1 = progress.add_task("Fetching Yahoo Finance data...", total=None)
            try:
                hist_data = self.yahoo_client.get_historical_data(self.symbol, period)
                current_price = self.yahoo_client.get_current_price(self.symbol)
                company_info = self.yahoo_client.get_company_info(self.symbol)
                dividend_data = self.yahoo_client.get_dividend_history(self.symbol)
                
                if hist_data is not None and not hist_data.empty:
                    data['historical'] = hist_data
                    data['current_price'] = current_price
                    data['company_info'] = company_info
                    data['dividends'] = dividend_data
                    progress.update(task1, description="✅ Yahoo Finance data retrieved")
                
                    # Save to database
                    self.db_manager.save_stock_data(self.symbol, hist_data)
                    if dividend_data is not None and not dividend_data.empty:
                        try:
                            if hasattr(self.db_manager, 'save_dividend_data'):
                                self.db_manager.save_dividend_data(self.symbol, dividend_data)
                        except Exception as e:
                            self.logger.warning(f"Could not save dividend data: {e}")
                
            except Exception as e:
                self.logger.error(f"Yahoo Finance error: {e}")
                progress.update(task1, description="❌ Yahoo Finance failed")
                return data
            
            # Alpha Vantage data (optional enhancement)
            if self.alpha_vantage_client:
                task2 = progress.add_task("Fetching Alpha Vantage data...", total=None)
                try:
                    av_data = self.alpha_vantage_client.get_daily_data(self.symbol.replace('.AX', ''))
                    if av_data:
                        data['alpha_vantage'] = av_data
                        progress.update(task2, description="✅ Alpha Vantage data retrieved")
                except Exception as e:
                    self.logger.warning(f"Alpha Vantage error: {e}")
                    progress.update(task2, description="⚠️ Alpha Vantage optional")
            
            # News data
            if self.news_client:
                task3 = progress.add_task("Fetching news data...", total=None)
                try:
                    # Use symbol without .AX suffix for news search
                    news_symbol = self.symbol.replace('.AX', '')
                    news_data = self.news_client.get_financial_news(news_symbol)
                    if news_data and len(news_data) > 0:
                        data['news'] = news_data
                        progress.update(task3, description="✅ News data retrieved")
                except Exception as e:
                    self.logger.warning(f"News API error: {e}")
                    progress.update(task3, description="⚠️ News data optional")
        
        return data

    def perform_technical_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive technical analysis"""
        analysis = {}
        
        try:
            if 'historical' in data:
                hist_data = data['historical']
                # Use basic indicators that we know exist
                analysis['technical'] = {}
                if hasattr(self.tech_analyzer, 'calculate_sma'):
                    analysis['technical']['SMA_20'] = self.tech_analyzer.calculate_sma(hist_data['Close'], 20)
                    analysis['technical']['SMA_50'] = self.tech_analyzer.calculate_sma(hist_data['Close'], 50)
                if hasattr(self.tech_analyzer, 'calculate_rsi'):
                    analysis['technical']['RSI'] = self.tech_analyzer.calculate_rsi(hist_data['Close'])
                
                # Pattern detection if available
                if hasattr(self.tech_analyzer, 'detect_patterns'):
                    analysis['patterns'] = self.tech_analyzer.detect_patterns(hist_data)
            
        except Exception as e:
            self.logger.error(f"Technical analysis error: {e}")
            analysis['error'] = str(e)
        
        return analysis

    def perform_financial_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform financial analysis"""
        analysis = {}
        
        try:
            if 'historical' in data:
                hist_data = data['historical']
                # Basic financial calculations
                analysis['financial'] = {}
                
                # Calculate returns
                returns = hist_data['Close'].pct_change().dropna()
                if not returns.empty:
                    analysis['financial']['total_return'] = (returns + 1).prod() - 1
                    analysis['financial']['annualized_return'] = analysis['financial']['total_return'] * (252 / len(returns))
                    analysis['financial']['volatility'] = returns.std() * (252 ** 0.5)
                    
                    # Sharpe ratio (assuming risk-free rate of 2%)
                    risk_free_rate = 0.02
                    if analysis['financial']['volatility'] > 0:
                        analysis['financial']['sharpe_ratio'] = (analysis['financial']['annualized_return'] - risk_free_rate) / analysis['financial']['volatility']
            
        except Exception as e:
            self.logger.error(f"Financial analysis error: {e}")
            analysis['error'] = str(e)
        
        return analysis

    def display_comprehensive_report(self, data: Dict[str, Any]) -> None:
        """Display comprehensive analysis report"""
        
        # Get company name for display
        company_name = self._get_display_name()
        
        # Header
        self.console.print(Panel.fit(
            f"[bold blue]📈 {company_name}[/]\n"
            "[green]Advanced Stock Analysis Report[/]\n"
            f"[yellow]Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/]\n"
            "[dim]Powered by Elliot Fidge's Stock Tracker v2.0[/]",
            title=f"📊 Elliot Fidge's Stock Tracker - {self.symbol}"
        ))
        
        # Current Price Information
        if 'current_price' in data and data['current_price']:
            price_info = data['current_price']
            table = Table(title="💰 Current Price Information")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            # Handle both dict and float formats
            if isinstance(price_info, dict):
                current_price_val = price_info.get('price', 'N/A')
            else:
                current_price_val = price_info
            
            if isinstance(current_price_val, (int, float)):
                table.add_row("Current Price", f"${current_price_val:.2f}")
            else:
                table.add_row("Current Price", "N/A")
            
            if 'historical' in data and not data['historical'].empty:
                hist_data = data['historical']
                table.add_row("52-Week High", f"${hist_data['High'].max():.2f}")
                table.add_row("52-Week Low", f"${hist_data['Low'].min():.2f}")
                
                # Calculate daily change
                if len(hist_data) >= 2:
                    today_close = hist_data['Close'].iloc[-1]
                    yesterday_close = hist_data['Close'].iloc[-2]
                    change_pct = ((today_close - yesterday_close) / yesterday_close) * 100
                    change_color = "green" if change_pct >= 0 else "red"
                    change_symbol = "+" if change_pct >= 0 else ""
                    table.add_row("1-Day Change", f"[{change_color}]{change_symbol}{change_pct:.2f}%[/]")
            
            self.console.print(table)
            self.console.print()

        # Technical Analysis
        if 'technical' in data:
            tech_data = data['technical']
            table = Table(title="📈 Technical Indicators")
            table.add_column("Indicator", style="cyan")
            table.add_column("Value", style="white")
            table.add_column("Signal", style="yellow")
            
            # RSI
            if 'RSI' in tech_data:
                rsi_val = tech_data['RSI'].iloc[-1] if not tech_data['RSI'].empty else 0
                if rsi_val > 70:
                    signal = "🔴 Overbought"
                elif rsi_val < 30:
                    signal = "🟢 Oversold"
                else:
                    signal = "⚪ Neutral"
                table.add_row("RSI (14)", f"{rsi_val:.2f}", signal)
            
            # Moving Averages
            if 'SMA_20' in tech_data:
                sma20_val = tech_data['SMA_20'].iloc[-1]
                current_price_val = data['historical']['Close'].iloc[-1]
                sma_signal = "🟢 Above" if current_price_val > sma20_val else "🔴 Below"
                table.add_row("SMA (20)", f"${sma20_val:.2f}", sma_signal)
            
            if 'SMA_50' in tech_data:
                sma50_val = tech_data['SMA_50'].iloc[-1]
                current_price_val = data['historical']['Close'].iloc[-1]
                sma_signal = "🟢 Above" if current_price_val > sma50_val else "🔴 Below"
                table.add_row("SMA (50)", f"${sma50_val:.2f}", sma_signal)
            
            self.console.print(table)
            self.console.print()

        # Financial Performance
        if 'financial' in data:
            fin_data = data['financial']
            table = Table(title="💼 Financial Performance")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="white")
            
            for key, value in fin_data.items():
                if isinstance(value, (int, float)):
                    if 'return' in key.lower() or 'ratio' in key.lower():
                        table.add_row(key.replace('_', ' ').title(), f"{value:.2f}%")
                    elif 'volatility' in key.lower():
                        table.add_row(key.replace('_', ' ').title(), f"{value:.2f}%")
                    else:
                        table.add_row(key.replace('_', ' ').title(), f"{value:.2f}")
            
            self.console.print(table)
            self.console.print()

        # Company Information
        if 'company_info' in data and data['company_info']:
            company_data = data['company_info']
            table = Table(title="🏢 Company Information")
            table.add_column("Attribute", style="cyan")
            table.add_column("Value", style="white")
            
            # Display key company info
            info_fields = ['longName', 'sector', 'industry']
            for field in info_fields:
                if field in company_data:
                    display_name = {
                        'longName': 'Company Name',
                        'sector': 'Sector',
                        'industry': 'Industry'
                    }.get(field, field)
                    table.add_row(display_name, str(company_data[field]))
            
            self.console.print(table)
            self.console.print()

        # Predictive Analysis
        if self.predictive_analyzer and 'historical' in data:
            try:
                prediction = self.predictive_analyzer.predict_price(data['historical'], days=30)
                if prediction:
                    table = Table(title="🔮 Price Predictions")
                    table.add_column("Metric", style="cyan")
                    table.add_column("Value", style="white")
                    
                    table.add_row("Trend Direction", "📈 Bullish" if prediction.get('trend', 0) > 0 else "📉 Bearish")
                    table.add_row("30-Day Prediction", f"${prediction.get('predicted_price', 0):.2f}")
                    
                    current_price_val = data['historical']['Close'].iloc[-1]
                    predicted_price = prediction.get('predicted_price', current_price_val)
                    change_pct = ((predicted_price - current_price_val) / current_price_val) * 100
                    table.add_row("Expected Change", f"{change_pct:+.2f}%")
                    
                    self.console.print(table)
                    self.console.print()
            except Exception as e:
                self.logger.warning(f"Prediction error: {e}")

    def run_analysis(self, period: str = '1y'):
        """Run comprehensive stock analysis"""
        self.console.print(f"[bold green]🚀 Starting Advanced Stock Analysis for {self.symbol}...[/]")
        self.console.print()
        
        # Get comprehensive data
        data = self.get_comprehensive_data(period)
        
        if not data:
            self.console.print("[red]❌ Failed to retrieve data[/]")
            return
        
        # Perform analysis
        self.console.print("📊 Performing technical analysis...")
        tech_analysis = self.perform_technical_analysis(data)
        data.update(tech_analysis)
        
        self.console.print("💼 Performing financial analysis...")
        fin_analysis = self.perform_financial_analysis(data)
        data.update(fin_analysis)
        
        if self.predictive_analyzer:
            self.console.print("🔮 Performing predictive analysis...")
        
        # Display comprehensive report
        self.display_comprehensive_report(data)
        
        self.console.print(f"✅ Data saved to database")


# CLI Commands
@click.group()
def cli():
    """Elliot Fidge's Advanced Stock Tracker - Comprehensive financial analysis tool for AFI and ASX stocks"""

@cli.command()
@click.option('--period', default='1y', help='Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)')
@click.option('--symbol', default='AFI', help='Stock symbol to analyze (e.g., AFI, CBA, BHP)')
def analyze(period, symbol):
    """Run comprehensive stock analysis for any ASX-listed stock"""
    tracker = ElliotFidgeStockTracker(symbol)
    tracker.run_analysis(period)

@cli.command()
def dashboard():
    """Launch Streamlit dashboard"""
    if not VISUALIZATION_AVAILABLE:
        console.print("[red]❌ Visualization libraries not installed[/]")
        console.print("[yellow]Install with: pip install streamlit plotly[/]")
        return
    
    # Create dashboard file
    dashboard_content = '''
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Elliot Fidge's Stock Dashboard", page_icon="📈")

st.title("📈 Elliot Fidge's Stock Dashboard")
st.markdown("### Advanced Stock Analysis Dashboard")

# Sidebar for stock selection
symbol = st.sidebar.selectbox(
    "Select Stock Symbol",
    ["AFI.AX", "CBA.AX", "BHP.AX", "CSL.AX", "WBC.AX", "ANZ.AX", "NAB.AX", "TLS.AX"],
    index=0
)

period = st.sidebar.selectbox(
    "Select Time Period",
    ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
    index=3
)

# Get stock data
@st.cache_data
def get_stock_data(symbol, period):
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period)
    info = ticker.info
    return hist, info

try:
    hist, info = get_stock_data(symbol, period)
    
    # Current price
    current_price = hist['Close'].iloc[-1]
    prev_price = hist['Close'].iloc[-2]
    change = current_price - prev_price
    change_pct = (change / prev_price) * 100
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Price", f"${current_price:.2f}", f"{change:+.2f} ({change_pct:+.2f}%)")
    with col2:
        st.metric("52-Week High", f"${hist['High'].max():.2f}")
    with col3:
        st.metric("52-Week Low", f"${hist['Low'].min():.2f}")
    
    # Price chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name=f'{symbol} Price', line=dict(color='blue')))
    fig.update_layout(title=f"{symbol} Stock Price ({period.upper()})", xaxis_title="Date", yaxis_title="Price (AUD)")
    st.plotly_chart(fig, use_container_width=True)
    
    # Volume chart
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=hist.index, y=hist['Volume'], name='Volume'))
    fig2.update_layout(title=f"{symbol} Trading Volume", xaxis_title="Date", yaxis_title="Volume")
    st.plotly_chart(fig2, use_container_width=True)
    
    # Company info
    if info:
        st.subheader("Company Information")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Company Name:** {info.get('longName', 'N/A')}")
            st.write(f"**Sector:** {info.get('sector', 'N/A')}")
            st.write(f"**Industry:** {info.get('industry', 'N/A')}")
        with col2:
            st.write(f"**Market Cap:** {info.get('marketCap', 'N/A')}")
            st.write(f"**P/E Ratio:** {info.get('trailingPE', 'N/A')}")
            st.write(f"**Dividend Yield:** {info.get('dividendYield', 'N/A')}")

except Exception as e:
    st.error(f"Error loading data: {e}")

st.markdown("---")
st.markdown("*Powered by Elliot Fidge's Advanced Stock Tracker v2.0*")
'''
    
    dashboard_file = Path(__file__).parent / 'afi_dashboard.py'
    dashboard_file.write_text(dashboard_content)
    
    try:
        import subprocess
        subprocess.run(['python', '-m', 'streamlit', 'run', str(dashboard_file)], check=True)
    except Exception as e:
        console.print("[red]❌ Failed to launch Streamlit. Try running manually:[/]")
        console.print(f"[cyan]python -m streamlit run {dashboard_file}[/]")

@cli.command()
def test():
    """Test all available features"""
    console.print("[bold blue]🧪 Testing Elliot Fidge's Advanced Stock Tracker Features...[/]")
    console.print()
    
    # Test core functionality
    console.print("Core Features:")
    console.print(f"✅ Yahoo Finance API: Available")
    console.print(f"{'✅' if ALPHA_VANTAGE_AVAILABLE else '⚠️ '} Alpha Vantage API: {'Available' if ALPHA_VANTAGE_AVAILABLE else 'Not Available (optional)'}")
    console.print(f"{'✅' if NEWS_CLIENT_AVAILABLE else '⚠️ '} News API: {'Available' if NEWS_CLIENT_AVAILABLE else 'Not Available (optional)'}")
    console.print(f"{'✅' if VISUALIZATION_AVAILABLE else '⚠️ '} Visualization: {'Available' if VISUALIZATION_AVAILABLE else 'Not Available (optional)'}")
    console.print(f"{'✅' if PREDICTION_AVAILABLE else '⚠️ '} Predictive Analytics: {'Available' if PREDICTION_AVAILABLE else 'Not Available (optional)'}")
    
    console.print()
    console.print("Running quick test...")
    
    try:
        tracker = ElliotFidgeStockTracker()
        console.print("✅ Elliot Fidge's Stock Tracker initialized successfully")
        
        # Quick data test
        hist_data = tracker.yahoo_client.get_historical_data("AFI.AX", "5d")
        if hist_data is not None and not hist_data.empty:
            console.print("✅ Data retrieval test passed")
        else:
            console.print("⚠️ Data retrieval test failed")
        
        console.print("\n[green]🎉 Elliot Fidge's Advanced Stock Tracker is ready to use![/]")
        
        # Create a comprehensive command reference table
        console.print()
        console.print("[bold cyan]📋 Complete Command Reference:[/]")
        console.print()
        
        # Main commands table
        command_table = Table(title="Available Commands", show_header=True, header_style="bold magenta")
        command_table.add_column("Command", style="cyan", no_wrap=True, width=35)
        command_table.add_column("Description", style="white")
        command_table.add_column("Options", style="yellow")
        
        command_table.add_row(
            "python afi_stock_tracker.py",
            "Run default AFI analysis (no command)",
            "Default behavior"
        )
        command_table.add_row(
            "python afi_stock_tracker.py analyze",
            "Run comprehensive stock analysis for any ASX stock",
            "--period TEXT (1d, 5d, 1mo, etc.) --symbol TEXT (AFI, CBA, BHP, etc.)"
        )
        command_table.add_row(
            "python afi_stock_tracker.py dashboard",
            "Launch interactive Streamlit web dashboard",
            "None"
        )
        command_table.add_row(
            "python afi_stock_tracker.py test",
            "Test all features and show this command reference",
            "None"
        )
        command_table.add_row(
            "python afi_stock_tracker.py --help",
            "Show main help menu",
            "None"
        )
        
        console.print(command_table)
        
        # Usage examples
        console.print()
        console.print("[bold green]💡 Usage Examples:[/]")
        examples_table = Table(show_header=True, header_style="bold green")
        examples_table.add_column("Example Command", style="cyan")
        examples_table.add_column("What It Does", style="white")
        
        examples_table.add_row(
            "python afi_stock_tracker.py analyze",
            "Run full AFI analysis with default 1-year period"
        )
        examples_table.add_row(
            "python afi_stock_tracker.py analyze --symbol CBA",
            "Analyze Commonwealth Bank of Australia stock"
        )
        examples_table.add_row(
            "python afi_stock_tracker.py analyze --period 6mo --symbol BHP",
            "Run 6-month analysis for BHP Group"
        )
        examples_table.add_row(
            "python afi_stock_tracker.py analyze --period max",
            "Run analysis with maximum available historical data"
        )
        examples_table.add_row(
            "python afi_stock_tracker.py dashboard",
            "Launch interactive web dashboard on localhost:8501"
        )
        examples_table.add_row(
            "python afi_stock_tracker.py test",
            "Test system and show this complete command reference"
        )
        
        console.print(examples_table)
        
        # Additional help
        console.print()
        console.print("[bold blue]ℹ️  Additional Information:[/]")
        console.print("• Use [cyan]--help[/] with any command for detailed options")
        console.print("• Dashboard runs on [cyan]http://localhost:8501[/] by default")
        console.print("• All analysis data is automatically saved to SQLite database")
        console.print("• First run may take longer as it downloads historical data")
        console.print("• Supports all ASX-listed stocks (AFI, CBA, BHP, CSL, etc.)")
        console.print()
        console.print("[dim]For more details, check README.md or run individual commands with --help[/]")
        
    except Exception as e:
        console.print(f"❌ Test failed: {e}")

def main():
    """Main function"""
    if len(sys.argv) == 1:
        # Default behavior - run AFI analysis
        tracker = ElliotFidgeStockTracker()
        tracker.run_analysis()
    else:
        cli()

if __name__ == "__main__":
    main()