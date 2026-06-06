#!/usr/bin/env python3
import os
import sys
from datetime import date, datetime

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from auth import get_authenticated_session, AuthError
from checker import check_availability
from notifier import send_alert


def main() -> int:
    appointment_url = os.environ["APPOINTMENT_URL"]
    target_date = date.fromisoformat(os.environ["TARGET_DATE"])
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        session = get_authenticated_session(appointment_url)
    except AuthError as e:
        print(f"[{now}] AUTH ERROR: {e}", file=sys.stderr)
        return 1

    try:
        available_dates = check_availability(session, appointment_url, target_date)
    except Exception as e:
        print(f"[{now}] CHECK ERROR: {e}", file=sys.stderr)
        return 1

    if available_dates:
        try:
            send_alert(available_dates, appointment_url)
        except Exception as e:
            print(f"[{now}] NOTIFY ERROR: {e}", file=sys.stderr)
            return 1
    else:
        print(f"[{now}] No slots available before {target_date}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
