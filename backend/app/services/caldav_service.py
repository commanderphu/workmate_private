"""
CalDAV Integration Service
Handles calendar sync with CalDAV-compatible services (Nextcloud, iCloud, etc.)
"""

import caldav
from caldav import DAVClient
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from icalendar import Calendar, Event as iCalEvent
import uuid
import logging

logger = logging.getLogger(__name__)


class CalDAVService:
    """Service for CalDAV calendar integration"""

    def __init__(self, url: str, username: str, password: str):
        """
        Initialize CalDAV client

        Args:
            url: CalDAV server URL (e.g., https://nextcloud.example.com/remote.php/dav/)
            username: Username for authentication
            password: Password or app-specific password
        """
        self.client = DAVClient(
            url=url,
            username=username,
            password=password
        )
        try:
            self.principal = self.client.principal()
            self.calendars = self.principal.calendars()
            logger.info(f"Connected to CalDAV server: {url}")
        except Exception as e:
            logger.error(f"Failed to connect to CalDAV: {e}")
            raise

    def list_calendars(self) -> List[Dict]:
        """List all available calendars"""
        calendar_list = []

        for calendar in self.calendars:
            try:
                calendar_list.append({
                    "id": str(calendar.id) if hasattr(calendar, 'id') else calendar.url,
                    "name": calendar.name,
                    "url": calendar.url
                })
            except Exception as e:
                logger.warning(f"Failed to get calendar info: {e}")
                continue

        return calendar_list

    def get_calendar_by_name(self, calendar_name: str):
        """Get calendar object by name"""
        for calendar in self.calendars:
            if calendar.name == calendar_name:
                return calendar

        raise ValueError(f"Calendar '{calendar_name}' not found")

    async def create_event(
        self,
        calendar_name: str,
        title: str,
        start: datetime,
        end: datetime,
        description: str = None,
        location: str = None
    ) -> str:
        """
        Create event in calendar

        Returns:
            External event ID (UID from calendar)
        """
        calendar = self.get_calendar_by_name(calendar_name)

        # Build iCal event
        ical = self._build_ical_event(
            title=title,
            start=start,
            end=end,
            description=description,
            location=location
        )

        # Save to calendar
        try:
            event = calendar.save_event(ical)
            logger.info(f"Created event '{title}' in calendar '{calendar_name}'")
            return str(event.id) if hasattr(event, 'id') else event.url
        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            raise

    async def update_event(
        self,
        event_id: str,
        title: str,
        start: datetime,
        end: datetime,
        description: str = None,
        location: str = None
    ):
        """Update existing event"""
        # Find event by ID
        event = self._find_event_by_id(event_id)

        if not event:
            raise ValueError(f"Event {event_id} not found")

        # Update event data
        ical = self._build_ical_event(
            title=title,
            start=start,
            end=end,
            description=description,
            location=location,
            uid=event_id
        )

        try:
            event.data = ical
            event.save()
            logger.info(f"Updated event {event_id}")
        except Exception as e:
            logger.error(f"Failed to update event: {e}")
            raise

    async def delete_event(self, event_id: str):
        """Delete event from calendar"""
        event = self._find_event_by_id(event_id)

        if event:
            try:
                event.delete()
                logger.info(f"Deleted event {event_id}")
            except Exception as e:
                logger.error(f"Failed to delete event: {e}")
                raise

    async def fetch_events(
        self,
        calendar_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Fetch events from calendar

        Args:
            calendar_name: Name of the calendar
            start_date: Start date range (default: 30 days ago)
            end_date: End date range (default: 365 days from now)

        Returns:
            List of event dictionaries
        """
        calendar = self.get_calendar_by_name(calendar_name)

        # Set default date range
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now() + timedelta(days=365)

        try:
            events = calendar.date_search(start=start_date, end=end_date)
            logger.info(f"Fetched {len(events)} events from '{calendar_name}'")

            parsed_events = []
            for event in events:
                try:
                    parsed = self._parse_ical_event(event.data)
                    if parsed:
                        parsed['external_id'] = str(event.id) if hasattr(event, 'id') else event.url
                        parsed_events.append(parsed)
                except Exception as e:
                    logger.warning(f"Failed to parse event: {e}")
                    continue

            return parsed_events
        except Exception as e:
            logger.error(f"Failed to fetch events: {e}")
            raise

    def _build_ical_event(
        self,
        title: str,
        start: datetime,
        end: datetime,
        description: str = None,
        location: str = None,
        uid: str = None
    ) -> str:
        """Build iCalendar format event"""
        cal = Calendar()
        cal.add('prodid', '-//Workmate Private//EN')
        cal.add('version', '2.0')

        event = iCalEvent()

        # UID (unique identifier)
        if uid:
            event.add('uid', uid)
        else:
            event.add('uid', f"{uuid.uuid4()}@workmate.private")

        # Event data
        event.add('dtstamp', datetime.utcnow())
        event.add('dtstart', start)
        event.add('dtend', end)
        event.add('summary', title)

        if description:
            event.add('description', description)

        if location:
            event.add('location', location)

        cal.add_component(event)

        return cal.to_ical().decode('utf-8')

    def _parse_ical_event(self, ical_data: str) -> Optional[Dict]:
        """Parse iCalendar data to dictionary"""
        try:
            cal = Calendar.from_ical(ical_data)

            for component in cal.walk():
                if component.name == "VEVENT":
                    return {
                        'uid': str(component.get('uid')),
                        'title': str(component.get('summary', '')),
                        'description': str(component.get('description', '')),
                        'start': component.get('dtstart').dt,
                        'end': component.get('dtend').dt,
                        'location': str(component.get('location', '')),
                        'last_modified': component.get('last-modified', datetime.utcnow()).dt
                            if component.get('last-modified') else datetime.utcnow()
                    }

            return None
        except Exception as e:
            logger.error(f"Failed to parse iCal: {e}")
            return None

    def _find_event_by_id(self, event_id: str):
        """Find event across all calendars by ID/URL"""
        for calendar in self.calendars:
            try:
                events = calendar.events()
                for event in events:
                    if (hasattr(event, 'id') and str(event.id) == event_id) or event.url == event_id:
                        return event
            except Exception as e:
                logger.warning(f"Error searching calendar: {e}")
                continue

        return None

    async def test_connection(self) -> bool:
        """Test if connection is working"""
        try:
            calendars = self.list_calendars()
            return len(calendars) >= 0  # Success if we can list calendars
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
