"""
Data module for fetching and managing market data
"""

from .data_fetcher import DataFetcher
from .economic_calendar import EconomicCalendar

__all__ = ['DataFetcher', 'EconomicCalendar']
