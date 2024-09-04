import re
from datetime import datetime
from typing import Any, Dict, Generator


class EventErrorsReport:
    """Group sentry issues by specific search pattern"""

    def __init__(self, events: list[Dict[str, Any]]):
        self.events = events

    def extract_val_by_pattern(self, pattern: str, message: str) -> str | None:
        """Find IP address in message."""
        search_match = re.search(pattern, message)
        return search_match.group(0) if search_match else None

    def group_by_pattern(self, pattern: str) -> Generator[tuple[str, Any], None, None]:
        """Extract value by pattern from event message and return it with
        event."""
        for event in self.events:
            groupping_value = self.extract_val_by_pattern(pattern, event["message"])

            # Group only if we found a match
            if groupping_value:
                event_timestamp = datetime.fromisoformat(
                    event["dateCreated"]
                )
                event["dateCreatedObject"] = event_timestamp.strftime("%Y-%m-%d")
                event["dateCreatedTime"] = event_timestamp.strftime("%H:%M:%S")
                event["eventCreatedTimestamp"] = event_timestamp
                yield groupping_value, event
