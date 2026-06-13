import os
import random
import re
import time
import requests
from datetime import date
from typing import Optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
}

# API template — schedule ID comes from APPOINTMENT_URL, facility ID from FACILITY_ID env var
DAYS_API = "https://ais.usvisa-info.com/en-es/niv/schedule/{schedule_id}/appointment/days/{facility_id}.json?appointments[expedite]=false"


def _parse_schedule_id(appointment_url: str) -> str:
    """Extract the numeric schedule ID from the appointment URL."""
    match = re.search(r"/schedule/(\d+)/", appointment_url)
    if not match:
        raise ValueError(f"Could not parse schedule ID from URL: {appointment_url}")
    return match.group(1)


def check_availability(
    session: requests.Session, appointment_url: str, target_date: date
) -> list[date]:
    time.sleep(random.uniform(2, 5))

    schedule_id = _parse_schedule_id(appointment_url)
    facility_id = os.environ["FACILITY_ID"]
    url = DAYS_API.format(schedule_id=schedule_id, facility_id=facility_id)
    headers = {**HEADERS, "Referer": appointment_url}

    resp = session.get(url, headers=headers)
    resp.raise_for_status()

    available: list[date] = []
    for entry in resp.json():
        try:
            d = date.fromisoformat(entry["date"])
            if d <= target_date:
                available.append(d)
        except (KeyError, ValueError):
            continue

    return available
