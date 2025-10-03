"""
Interactive visualization dashboard for AFI Stock Tracker
Uses Plotly for interactive charts and Streamlit for web interface
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

class InteractiveCharts:
    """Interactive chart generation using Plotly"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.colors = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e', 
            'success': '#2ca02c',
            'danger': '#d62728',
            'warning': '#ff7f0e',
            'info': '#17a2b8',
            'background': '#f8f9fa'
        }
    
    def create_price_chart(self, price_data: pd.DataFrame, indicators: Dict[str, pd.Series] = None, 
                          title: str = "AFI Stock Price") -> go.Figure:
        """Create interactive candlestick chart with technical indicators"""
        
        if price_data.empty:
            return go.Figure().add_annotation(text="No data available", x=0.5, y=0.5)
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.6, 0.2, 0.2],
            subplot_titles=('Price & Indicators', 'Volume', 'RSI')
        )
        
        # Candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=price_data.index,
                open=price_data['Open'],
                high=price_data['High'],
                low=price_data['Low'],
                close=price_data['Close'],
                name='Price',
                increasing_line_color='#2ca02c',
                decreasing_line_color='#d62728'
            ),
            row=1, col=1
        )
        
        # Add technical indicators
        if indicators:
            # Moving averages
            for name, data in indicators.items():
                if 'SMA' in name or 'EMA' in name:
                    fig.add_trace(
                        go.Scatter(
                            x=data.index,
                            y=data,
                            mode='lines',
                            name=name,
                            line=dict(width=2)
                        ),
                        row=1, col=1
                    )
                
                # Bollinger Bands
                elif name == 'bollinger_upper':
                    fig.add_trace(
                        go.Scatter(
                            x=data.index,
                            y=data,
                            mode='lines',
                            name='BB Upper',
                            line=dict(dash='dash', color='gray')
                        ),
                        row=1, col=1
                    )
                elif name == 'bollinger_lower':
                    fig.add_trace(
                        go.Scatter(
                            x=data.index,
                            y=data,
                            mode='lines',
                            name='BB Lower',
                            line=dict(dash='dash', color='gray'),
                            fill='tonexty',
                            fillcolor='rgba(128,128,128,0.1)'
                        ),
                        row=1, col=1
                    )
                
                # RSI
                elif name == 'RSI':
                    fig.add_trace(
                        go.Scatter(
                            x=data.index,
                            y=data,
                            mode='lines',
                            name='RSI',
                            line=dict(color='purple')
                        ),
                        row=3, col=1
                    )
        
        # Volume chart
        if 'Volume' in price_data.columns:
            colors = ['red' if close < open else 'green' 
                     for close, open in zip(price_data['Close'], price_data['Open'])]
            
            fig.add_trace(
                go.Bar(
                    x=price_data.index,
                    y=price_data['Volume'],
                    name='Volume',
                    marker_color=colors,
                    opacity=0.7
                ),
                row=2, col=1
            )
        
        # Add RSI overbought/oversold lines
        fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=3, col=1)
        
        # Update layout
        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Price (AUD)",
            height=800,
            showlegend=True,
            xaxis_rangeslider_visible=False,
            template="plotly_white"
        )
        
        fig.update_yaxes(title_text="Price (AUD)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        fig.update_yaxes(title_text="RSI", row=3, col=1, range=[0, 100])
        
        return fig
    
    def create_performance_chart(self, returns_data: Dict[str, float]) -> go.Figure:
        """Create performance metrics visualization"""
        
        metrics = ['1 Day', '1 Week', '1 Month', '3 Months', '6 Months', '1 Year']
        values = [returns_data.get(f'{period.lower().replace(" ", "_")}_return', 0) for period in metrics]
        
        colors = ['green' if v > 0 else 'red' for v in values]
        
        fig = go.Figure(data=[
            go.Bar(
                x=metrics,
                y=values,
                marker_color=colors,
                text=[f'{v:.2f}%' for v in values],
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title="Performance Returns",
            xaxis_title="Time Period",
            yaxis_title="Return (%)",
            template="plotly_white",
            height=400
        )
        
        return fig
    
    def create_dividend_chart(self, dividend_data: pd.DataFrame) -> go.Figure:
        """Create dividend history visualization"""
        
        if dividend_data.empty:
            return go.Figure().add_annotation(text="No dividend data available", x=0.5, y=0.5)
        
        fig = go.Figure()
        
        # Annual dividends bar chart
        annual_dividends = dividend_data.groupby(dividend_data.index.year)['Amount'].sum()
        
        fig.add_trace(
            go.Bar(
                x=annual_dividends.index,
                y=annual_dividends.values,
                name='Annual Dividends',
                marker_color=self.colors['success'],
                text=[f'${v:.3f}' for v in annual_dividends.values],
                textposition='auto'
            )
        )
        
        # Add trend line
        if len(annual_dividends) > 1:
            z = np.polyfit(annual_dividends.index, annual_dividends.values, 1)
            trend_line = np.poly1d(z)
            
            fig.add_trace(
                go.Scatter(
                    x=annual_dividends.index,
                    y=trend_line(annual_dividends.index),
                    mode='lines',
                    name='Trend',
                    line=dict(dash='dash', color='red')
                )
            )
        
        fig.update_layout(
            title="Dividend History",
            xaxis_title="Year",
            yaxis_title="Dividend Amount (AUD)",
            template="plotly_white",
            height=400
        )
        
        return fig
    
    def create_portfolio_summary(self, portfolio_data: Dict[str, Any]) -> go.Figure:
        """Create portfolio allocation and performance chart"""
        
        # Create pie chart for allocation
        fig = make_subplots(
            rows=1, cols=2,
            specs=[[{"type": "domain"}, {"type": "xy"}]],
            subplot_titles=('Portfolio Allocation', 'Performance Metrics')
        )
        
        # Portfolio allocation (if multiple holdings)
        if 'allocations' in portfolio_data:
            allocations = portfolio_data['allocations']
            fig.add_trace(
                go.Pie(
                    labels=list(allocations.keys()),
                    values=list(allocations.values()),
                    name="Allocation"
                ),
                1, 1
            )
        
        # Performance metrics
        metrics = ['Capital Gain', 'Dividends', 'Total Return']
        values = [
            portfolio_data.get('capital_gain_percent', 0),
            portfolio_data.get('dividend_yield', 0),
            portfolio_data.get('total_return_percent', 0)
        ]
        
        colors = ['green' if v > 0 else 'red' for v in values]
        
        fig.add_trace(
            go.Bar(
                x=metrics,
                y=values,
                marker_color=colors,
                text=[f'{v:.2f}%' for v in values],
                textposition='auto'
            ),
            1, 2
        )
        
        fig.update_layout(
            title="Portfolio Overview",
            template="plotly_white",
            height=500
        )
        
        return fig
    
    def create_news_sentiment_chart(self, news_data: List[Dict]) -> go.Figure:
        """Create news sentiment analysis chart"""
        
        if not news_data:
            return go.Figure().add_annotation(text="No news data available", x=0.5, y=0.5)
        
        # Aggregate sentiment by date
        sentiment_by_date = {}
        for article in news_data:
            date = article['published_date'].date()
            sentiment = article['sentiment']['compound']
            
            if date not in sentiment_by_date:
                sentiment_by_date[date] = []
            sentiment_by_date[date].append(sentiment)
        
        # Calculate daily average sentiment
        dates = []
        sentiments = []
        for date, scores in sentiment_by_date.items():
            dates.append(date)
            sentiments.append(np.mean(scores))
        
        # Create sentiment chart
        fig = go.Figure()
        
        colors = ['green' if s > 0 else 'red' if s < 0 else 'gray' for s in sentiments]
        
        fig.add_trace(
            go.Bar(
                x=dates,
                y=sentiments,
                marker_color=colors,
                name='Daily Sentiment',
                text=[f'{s:.2f}' for s in sentiments],
                textposition='auto'
            )
        )
        
        # Add neutral line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        fig.update_layout(
            title="News Sentiment Analysis",
            xaxis_title="Date",
            yaxis_title="Sentiment Score",
            template="plotly_white",
            height=400,
            yaxis_range=[-1, 1]
        )
        
        return fig
    
    def create_correlation_heatmap(self, correlation_data: pd.DataFrame) -> go.Figure:
        """Create correlation heatmap for multiple metrics"""
        
        fig = go.Figure(data=go.Heatmap(
            z=correlation_data.values,
            x=correlation_data.columns,
            y=correlation_data.index,
            colorscale='RdBu',
            zmid=0,
            text=correlation_data.round(2).values,
            texttemplate="%{text}",
            textfont={"size": 10},
            hoverongaps=False
        ))
        
        fig.update_layout(
            title="Correlation Analysis",
            template="plotly_white",
            height=500
        )
        
        return fig

class StreamlitDashboard:
    """Streamlit web dashboard"""
    
    def __init__(self, data_manager, chart_generator: InteractiveCharts):
        self.data_manager = data_manager
        self.charts = chart_generator
        
    def render_main_dashboard(self):
        """Render the main dashboard"""
        
        st.set_page_config(
            page_title="AFI Stock Tracker",
            page_icon="📈",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        st.title("🏦 Australian Foundation Investment Company (AFI) Tracker")
        
        # Sidebar controls
        with st.sidebar:
            st.header("⚙️ Controls")
            
            # Time period selector
            time_period = st.selectbox(
                "Select Time Period",
                ["1 Month", "3 Months", "6 Months", "1 Year", "2 Years", "5 Years"],
                index=3
            )
            
            # Refresh button
            if st.button("🔄 Refresh Data"):
                st.experimental_rerun()
            
            # Configuration
            st.header("📊 Display Options")
            show_volume = st.checkbox("Show Volume", value=True)
            show_indicators = st.checkbox("Show Technical Indicators", value=True)
            show_news = st.checkbox("Show News Analysis", value=True)
        
        # Main content area
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            # Current price and basic info
            current_price = self.data_manager.get_latest_price('AFI')
            if current_price:
                st.metric("Current Price", f"${current_price:.3f}", "0.00%")
        
        with col2:
            # Market status
            market_hours = self._get_market_status()
            st.write(f"**Market Status:** {market_hours}")
        
        with col3:
            # Last updated
            st.write(f"**Last Updated:** {datetime.now().strftime('%H:%M:%S')}")
        
        # Price chart
        st.header("📈 Price Chart")
        price_data = self._load_price_data(time_period)
        
        if not price_data.empty:
            indicators = self._load_indicators() if show_indicators else None
            chart = self.charts.create_price_chart(price_data, indicators)
            st.plotly_chart(chart, use_container_width=True)
        else:
            st.warning("No price data available")
        
        # Performance and analytics
        col1, col2 = st.columns(2)
        
        with col1:
            st.header("📊 Performance")
            returns_data = self._calculate_returns(price_data)
            perf_chart = self.charts.create_performance_chart(returns_data)
            st.plotly_chart(perf_chart, use_container_width=True)
        
        with col2:
            st.header("💰 Dividends")
            dividend_data = self._load_dividend_data()
            div_chart = self.charts.create_dividend_chart(dividend_data)
            st.plotly_chart(div_chart, use_container_width=True)
        
        # News and sentiment
        if show_news:
            st.header("📰 News & Sentiment")
            news_data = self._load_news_data()
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Recent news
                st.subheader("Recent News")
                for article in news_data[:5]:
                    with st.expander(f"📄 {article['title'][:100]}..."):
                        st.write(f"**Source:** {article['source']}")
                        st.write(f"**Date:** {article['published_date'].strftime('%Y-%m-%d %H:%M')}")
                        st.write(f"**Sentiment:** {article['sentiment']['compound']:.2f}")
                        st.write(article['description'])
                        st.link_button("Read More", article['url'])
            
            with col2:
                # Sentiment chart
                sentiment_chart = self.charts.create_news_sentiment_chart(news_data)
                st.plotly_chart(sentiment_chart, use_container_width=True)
        
        # Portfolio section (if configured)
        portfolio_data = self._load_portfolio_data()
        if portfolio_data:
            st.header("🏦 Portfolio")
            portfolio_chart = self.charts.create_portfolio_summary(portfolio_data)
            st.plotly_chart(portfolio_chart, use_container_width=True)
    
    def _get_market_status(self) -> str:
        """Get current market status"""
        now = datetime.now()
        if now.weekday() < 5 and 10 <= now.hour < 16:  # Simplified ASX hours
            return "🟢 Open"
        else:
            return "🔴 Closed"
    
    def _load_price_data(self, period: str) -> pd.DataFrame:
        """Load price data for specified period"""
        # This would integrate with your data manager
        # Return sample data for now
        return pd.DataFrame()
    
    def _load_indicators(self) -> Dict[str, pd.Series]:
        """Load technical indicators"""
        return {}
    
    def _load_dividend_data(self) -> pd.DataFrame:
        """Load dividend data"""
        return pd.DataFrame()
    
    def _load_news_data(self) -> List[Dict]:
        """Load news data"""
        return []
    
    def _load_portfolio_data(self) -> Dict[str, Any]:
        """Load portfolio data"""
        return {}
    
    def _calculate_returns(self, price_data: pd.DataFrame) -> Dict[str, float]:
        """Calculate return metrics"""
        return {}