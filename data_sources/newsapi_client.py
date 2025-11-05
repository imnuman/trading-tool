"""
NewsAPI Client for Sentiment Analysis

NewsAPI provides news headlines from major financial sources.
Free tier: 100 requests/day
API: https://newsapi.org/

Features to extract:
- overall_sentiment [-1, 1]
- sentiment_strength [0, 1]
- news_volume (count in last 24h)
- sentiment_change
"""

import os
from typing import Dict, List
import requests
from datetime import datetime, timedelta


class NewsAPIClient:
    """Client for fetching news and performing sentiment analysis"""

    def __init__(self):
        self.base_url = "https://newsapi.org/v2"
        self.api_key = os.getenv("NEWSAPI_API_KEY")

        if not self.api_key:
            raise ValueError("NEWSAPI_API_KEY not found in environment variables")

    def fetch_news(self, query_terms: List[str], lookback_hours: int = 24) -> List[Dict]:
        """
        Fetch news articles for specified query terms

        Args:
            query_terms: List of search terms (e.g., ["forex", "EUR/USD"])
            lookback_hours: How far back to search

        Returns:
            List of news articles
        """
        # TODO: Implement NewsAPI connection
        pass

    def analyze_sentiment(self, articles: List[Dict]) -> Dict[str, float]:
        """
        Analyze sentiment using FinBERT model

        Args:
            articles: List of news articles

        Returns:
            Dictionary with 4 sentiment features
        """
        # TODO: Implement FinBERT sentiment analysis
        pass
