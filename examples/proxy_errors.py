import asyncio
from collections import defaultdict
from datetime import timedelta
import logging
from os import environ
from textwrap import indent
from typing import Any

from sentry_rest import EventErrorsReport, SentryClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    sentry_client = SentryClient(
        auth_token=environ["SENTRY_AUTH_TOKEN"],
        auth_organization=environ["SENTRY_ORGANIZATION"],
        auth_project=environ["SENTRY_PROJECT"],
        search_query="Proxy error detected",
        tracing_enabled=False,  # toggle aiohttp requests information
    )

    # Get all events for issues with specific rearch query
    events = asyncio.run(sentry_client.extract())

    # Group event messages by proxy and date
    report = EventErrorsReport(events)
    report_data = report.group_by_pattern(pattern=r"[0-9]+(?:\.[0-9]+){3}")

    # -------------------------------
    # "Simple Vizualization"
    # --------------------------------

    # Step 1. Group by proxy
    grouped_data: defaultdict[str, defaultdict[str, Any]] = defaultdict(
        lambda: defaultdict(list)
    )
    for grouping_value, event in report_data:
        grouped_data[grouping_value][event["dateCreatedObject"]].append(
            {
                "message": f"{event['dateCreatedTime']} >> {event['message']}",
                "eventCreatedTimestamp": event["eventCreatedTimestamp"],
            }
        )

    # Step 2. Visualize grouped data
    MESSAGE_MAX_LENGTH = 70
    print("Proxy checking report (2 weeks), timezone is UTC")
    print("=" * 40)
    for grouping_value, events in grouped_data.items():
        print(
            f"[Proxy: {grouping_value}. "
            f"Total erors: {sum(len(e) for e in events.values())}]"
        )
        for date, errors in events.items():
            print(f"\t{date}: {len(errors)} errors")
            prev_timestamp = None
            for error in sorted(errors, key=lambda e: e["eventCreatedTimestamp"]):
                if not prev_timestamp:
                    prev_timestamp = error["eventCreatedTimestamp"]

                if (
                    error["eventCreatedTimestamp"] - prev_timestamp
                ).total_seconds() > timedelta(hours=1).total_seconds():
                    print("\t\t" + "-" * 8 + "🕐" + "-" * 8)
                    prev_timestamp = error["eventCreatedTimestamp"]

                print(indent(error["message"][:MESSAGE_MAX_LENGTH], "\t"*2))

        print("=" * 40)
