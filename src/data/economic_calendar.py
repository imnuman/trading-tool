"""
Economic Calendar Module
Filters trades around high-impact news events
"""

from datetime import datetime, time, timedelta
from typing import Tuple, Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class EconomicCalendar:
    """Manages economic calendar and news filtering"""

    def __init__(self, buffer_minutes: int = 30):
        """
        Initialize economic calendar

        Args:
            buffer_minutes: Minutes before/after news to avoid trading
        """
        self.buffer_minutes = buffer_minutes

        # High-impact news times (UTC) - typical release times
        # In production, this should be fetched from an API
        self.high_impact_times = {
            # Monday
            0: [],
            # Tuesday
            1: [
                time(13, 30),  # US economic data
            ],
            # Wednesday
            2: [
                time(12, 30),  # US ADP Employment
                time(18, 0),   # FOMC Minutes (when scheduled)
            ],
            # Thursday
            3: [
                time(12, 30),  # US Jobless Claims
            ],
            # Friday
            4: [
                time(12, 30),  # US NFP (first Friday)
                time(13, 30),  # US economic data
            ],
            # Weekend
            5: [],
            6: [],
        }

        # Major central bank announcement times (UTC)
        self.central_bank_times = [
            time(12, 0),   # ECB
            time(18, 0),   # Fed
            time(19, 0),   # Fed
        ]

    def is_trading_allowed(self) -> Tuple[bool, Optional[str]]:
        """
        Check if trading is allowed based on economic calendar

        Returns:
            Tuple of (is_allowed, reason_if_blocked)
        """
        now = datetime.utcnow()
        current_time = now.time()
        current_weekday = now.weekday()

        # Check if within buffer time of high-impact news
        if current_weekday in self.high_impact_times:
            for news_time in self.high_impact_times[current_weekday]:
                if self._is_within_buffer(current_time, news_time):
                    return False, f"High-impact news at {news_time.strftime('%H:%M')} UTC"

        # Check central bank times
        for cb_time in self.central_bank_times:
            if self._is_within_buffer(current_time, cb_time):
                return False, f"Central bank announcement at {cb_time.strftime('%H:%M')} UTC"

        # Check if it's NFP week (first Friday of month)
        if self._is_nfp_friday(now):
            nfp_time = time(12, 30)
            if self._is_within_buffer(current_time, nfp_time):
                return False, "US Non-Farm Payrolls release time"

        return True, None

    def _is_within_buffer(self, current_time: time, event_time: time) -> bool:
        """
        Check if current time is within buffer minutes of event time

        Args:
            current_time: Current time
            event_time: Event time

        Returns:
            True if within buffer
        """
        # Convert times to minutes since midnight
        current_minutes = current_time.hour * 60 + current_time.minute
        event_minutes = event_time.hour * 60 + event_time.minute

        # Check if within buffer
        diff = abs(current_minutes - event_minutes)

        return diff <= self.buffer_minutes

    def _is_nfp_friday(self, dt: datetime) -> bool:
        """
        Check if given date is NFP Friday (first Friday of month)

        Args:
            dt: DateTime to check

        Returns:
            True if it's NFP Friday
        """
        # Check if it's Friday
        if dt.weekday() != 4:
            return False

        # Check if it's the first Friday of the month
        # Get the first day of the month
        first_day = dt.replace(day=1)

        # Find the first Friday
        days_until_friday = (4 - first_day.weekday()) % 7
        first_friday = first_day + timedelta(days=days_until_friday)

        # Check if current date is within the first week
        return dt.date() == first_friday.date()

    def add_news_event(
        self,
        weekday: int,
        event_time: time,
        description: str = ""
    ):
        """
        Add a custom high-impact news event

        Args:
            weekday: Day of week (0=Monday, 6=Sunday)
            event_time: Time of event (UTC)
            description: Event description
        """
        if weekday not in self.high_impact_times:
            self.high_impact_times[weekday] = []

        self.high_impact_times[weekday].append(event_time)
        logger.info(f"Added news event: {description} on weekday {weekday} at {event_time}")

    def get_upcoming_events(self, hours_ahead: int = 24) -> List[Dict]:
        """
        Get upcoming high-impact events

        Args:
            hours_ahead: How many hours ahead to look

        Returns:
            List of upcoming events
        """
        now = datetime.utcnow()
        events = []

        for i in range(hours_ahead):
            check_time = now + timedelta(hours=i)
            weekday = check_time.weekday()

            if weekday in self.high_impact_times:
                for news_time in self.high_impact_times[weekday]:
                    event_datetime = check_time.replace(
                        hour=news_time.hour,
                        minute=news_time.minute,
                        second=0,
                        microsecond=0
                    )

                    if now < event_datetime < now + timedelta(hours=hours_ahead):
                        events.append({
                            'time': event_datetime,
                            'description': 'High-impact economic news',
                            'weekday': weekday
                        })

        return sorted(events, key=lambda x: x['time'])
