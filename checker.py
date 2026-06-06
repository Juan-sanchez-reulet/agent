import random
import time
import requests
from datetime import date, datetime
from typing import Optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
}

# Madrid facility ID (from the appointment page HTML)
FACILITY_ID = 7
DAYS_API = "https://ais.usvisa-info.com/en-es/niv/schedule/74726699/appointment/days/{facility_id}.json?appointments[expedite]=false"


def check_availability(
    session: requests.Session, appointment_url: str, target_date: date
) -> list[date]:
    time.sleep(random.uniform(2, 5))

    url = DAYS_API.format(facility_id=FACILITY_ID)
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
