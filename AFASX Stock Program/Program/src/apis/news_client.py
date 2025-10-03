"""
News API client for financial news and sentiment analysis
"""

import feedparser
import requests
from newsapi import NewsApiClient
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from .base_client import BaseAPIClient

class NewsClient(BaseAPIClient):
    """Client for fetching and analyzing financial news"""
    
    def __init__(self, news_api_key: Optional[str] = None):
        super().__init__(news_api_key or "", "", rate_limit=1.0)
        self.news_client = NewsApiClient(api_key=news_api_key) if news_api_key else None
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        
        # RSS feeds for Australian financial news
        self.rss_feeds = [
            "https://www.asx.com.au/asx/news/rss.do",
            "https://www.afr.com/rss",
            "https://www.businessnews.com.au/rss/latest-news",
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=AFI.AX&region=AU&lang=en-AU"
        ]
    
    def get_company_news(self, symbol: str = "AFI", days: int = 7) -> List[Dict[str, Any]]:
        """Get news articles related to the company"""
        all_news = []
        
        # Try NewsAPI first if available
        if self.news_client:
            try:
                news_data = self._get_news_api_articles(symbol, days)
                all_news.extend(news_data)
            except Exception as e:
                self.logger.error(f"NewsAPI failed: {e}")
        
        # Fallback to RSS feeds
        rss_news = self._get_rss_news(symbol, days)
        all_news.extend(rss_news)
        
        # Add sentiment analysis
        for article in all_news:
            article['sentiment'] = self._analyze_sentiment(article.get('title', '') + ' ' + article.get('description', ''))
        
        # Sort by publish date
        all_news.sort(key=lambda x: x.get('published_date', datetime.now()), reverse=True)
        
        return all_news[:50]  # Return top 50 articles
    
    def _get_news_api_articles(self, symbol: str, days: int) -> List[Dict[str, Any]]:
        """Get news from NewsAPI"""
        articles = []
        
        try:
            # Search for company-specific news
            queries = [
                f"Australian Foundation Investment Company",
                f"AFI {symbol}",
                f"Australian Foundation shares",
                f"AFIC investment"
            ]
            
            for query in queries:
                response = self.news_client.get_everything(
                    q=query,
                    from_param=(datetime.now() - timedelta(days=days)).isoformat(),
                    language='en',
                    sort_by='relevancy',
                    page_size=20
                )
                
                for article in response.get('articles', []):
                    articles.append({
                        'title': article['title'],
                        'description': article['description'],
                        'url': article['url'],
                        'source': article['source']['name'],
                        'published_date': datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ'),
                        'image_url': article.get('urlToImage')
                    })
        
        except Exception as e:
            self.logger.error(f"Failed to get NewsAPI articles: {e}")
        
        return articles
    
    def _get_rss_news(self, symbol: str, days: int) -> List[Dict[str, Any]]:
        """Get news from RSS feeds"""
        articles = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for feed_url in self.rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    # Check if article is relevant
                    title = entry.get('title', '').lower()
                    summary = entry.get('summary', '').lower()
                    
                    if any(keyword in title + summary for keyword in ['afi', 'australian foundation', 'afic']):
                        # Parse publish date
                        published_date = datetime.now()
                        if hasattr(entry, 'published_parsed'):
                            try:
                                published_date = datetime(*entry.published_parsed[:6])
                            except:
                                pass
                        
                        if published_date >= cutoff_date:
                            articles.append({
                                'title': entry.get('title', ''),
                                'description': entry.get('summary', ''),
                                'url': entry.get('link', ''),
                                'source': feed.feed.get('title', 'RSS Feed'),
                                'published_date': published_date,
                                'image_url': None
                            })
            
            except Exception as e:
                self.logger.error(f"Failed to parse RSS feed {feed_url}: {e}")
        
        return articles
    
    def _analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of text using multiple methods"""
        if not text:
            return {'compound': 0.0, 'positive': 0.0, 'neutral': 1.0, 'negative': 0.0, 'textblob_polarity': 0.0}
        
        # VADER sentiment analysis
        vader_scores = self.sentiment_analyzer.polarity_scores(text)
        
        # TextBlob sentiment analysis
        blob = TextBlob(text)
        textblob_polarity = blob.sentiment.polarity
        
        return {
            'compound': vader_scores['compound'],
            'positive': vader_scores['pos'],
            'neutral': vader_scores['neu'],
            'negative': vader_scores['neg'],
            'textblob_polarity': textblob_polarity
        }
    
    def get_market_sentiment(self, days: int = 7) -> Dict[str, Any]:
        """Get overall market sentiment for the company"""
        news_articles = self.get_company_news(days=days)
        
        if not news_articles:
            return {'overall_sentiment': 'neutral', 'sentiment_score': 0.0, 'article_count': 0}
        
        # Calculate average sentiment
        total_compound = sum(article['sentiment']['compound'] for article in news_articles)
        avg_sentiment = total_compound / len(news_articles)
        
        # Categorize sentiment
        if avg_sentiment >= 0.05:
            sentiment_label = 'positive'
        elif avg_sentiment <= -0.05:
            sentiment_label = 'negative'
        else:
            sentiment_label = 'neutral'
        
        # Get sentiment distribution
        positive_count = sum(1 for article in news_articles if article['sentiment']['compound'] > 0.05)
        negative_count = sum(1 for article in news_articles if article['sentiment']['compound'] < -0.05)
        neutral_count = len(news_articles) - positive_count - negative_count
        
        return {
            'overall_sentiment': sentiment_label,
            'sentiment_score': avg_sentiment,
            'article_count': len(news_articles),
            'positive_articles': positive_count,
            'negative_articles': negative_count,
            'neutral_articles': neutral_count,
            'sentiment_distribution': {
                'positive': positive_count / len(news_articles),
                'negative': negative_count / len(news_articles),
                'neutral': neutral_count / len(news_articles)
            }
        }
    
    def get_economic_indicators(self) -> List[Dict[str, Any]]:
        """Get Australian economic news that might affect AFI"""
        economic_keywords = [
            "RBA", "Reserve Bank Australia", "interest rates",
            "ASX", "Australian economy", "dividend imputation",
            "franking credits", "investment market Australia"
        ]
        
        articles = []
        
        if self.news_client:
            try:
                for keyword in economic_keywords:
                    response = self.news_client.get_everything(
                        q=keyword,
                        from_param=(datetime.now() - timedelta(days=3)).isoformat(),
                        language='en',
                        domains='asx.com.au,rba.gov.au,afr.com',
                        sort_by='relevancy',
                        page_size=5
                    )
                    
                    for article in response.get('articles', []):
                        articles.append({
                            'title': article['title'],
                            'description': article['description'],
                            'url': article['url'],
                            'source': article['source']['name'],
                            'published_date': datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ'),
                            'category': 'economic',
                            'sentiment': self._analyze_sentiment(article['title'] + ' ' + (article['description'] or ''))
                        })
            
            except Exception as e:
                self.logger.error(f"Failed to get economic indicators: {e}")
        
        return articles[:20]  # Return top 20 economic articles
    
    # Implementation of abstract methods from BaseAPIClient
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Not applicable for news client - return None"""
        return None
    
    def get_historical_data(self, symbol: str, period: str) -> Optional[Dict[str, Any]]:
        """Not applicable for news client - return None"""
        return None
    
    def get_financial_news(self, symbol: str = "AFI", days: int = 7) -> List[Dict[str, Any]]:
        """Alias for get_company_news for compatibility"""
        return self.get_company_news(symbol, days)