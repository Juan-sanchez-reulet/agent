# Visa Appointment Monitor — Design Spec
**Date:** 2026-06-06  
**Deadline:** Appointment must be found before 2026-09-17  
**Target URL:** https://ais.usvisa-info.com/en-es/niv/schedule/74726699/appointment?confirmed_limit_message=1&commit=Continue

---

## Context

The user needs a US nonimmigrant visa appointment at the US Embassy in Madrid before September 17, 2026 to travel to the United States. Appointment slots are scarce and open unpredictably. The goal is to monitor the appointment scheduling page 24/7 and send an immediate email alert when a slot becomes available before the deadline, so the user can manually book it as fast as possible.

---

## Architecture

```
agent/
├── monitor.py               # Entry point — orchestrates the check cycle
├── auth.py                  # Login, session management, cookie persistence
├── checker.py               # Fetches appointment page, parses available dates
├── notifier.py              # Sends email alert via Gmail SMTP
├── session.pkl              # Persisted session cookies (excluded from git)
├── .env                     # All secrets and config (excluded from git)
├── .env.example             # Template for required env vars
├── .gitignore
└── com.visa.monitor.plist   # macOS launchd job definition
```

---

## Components

### `auth.py` — Authentication
- Loads cookies from `session.pkl` on startup
- Detects session expiry: if the appointment page redirects to login, re-authenticates
- Login flow:
  1. GET login page → extract CSRF token (`authenticity_token`) from HTML
  2. POST credentials + CSRF token to login endpoint
  3. Follow redirects, assert we land on an authenticated page
  4. Persist new cookies to `session.pkl`
- Raises `AuthError` if login fails after 3 retries

### `checker.py` — Appointment Availability
- Uses the authenticated `requests.Session` from `auth.py`
- GET the appointment URL with a random delay (2–5 seconds) before the request
- Parses the HTML calendar with `BeautifulSoup`
- Identifies available date slots: days that are not disabled/greyed out in the calendar
- Filters for dates ≤ `TARGET_DATE` (2026-09-17)
- Returns list of available dates as `datetime.date` objects (empty list = no availability)
- If the site renders the calendar via JavaScript (no dates in HTML), falls back to Playwright headless

### `notifier.py` — Email Alert
- Gmail SMTP on port 587 with STARTTLS
- Subject: `VISA SLOT AVAILABLE — {dates} — Book now!`
- Body: list of available dates + direct booking URL
- Sends to `NOTIFY_EMAIL` (same as user's Gmail)
- Idempotent: logs a "notified" flag to avoid duplicate emails for the same date set within 1 hour

### `monitor.py` — Orchestrator
```
1. Load session (auth.py)
2. Fetch + parse calendar (checker.py)
3. If available dates found → notify (notifier.py) → exit 0
4. If no dates → log "checked at {time}, no slots" → exit 0
5. On any exception → log error → exit 1 (launchd will retry on next interval)
```

---

## Configuration (`.env`)

```env
VISA_EMAIL=juancruzr1975@gmail.com
VISA_PASSWORD=<password for ais.usvisa-info.com>
GMAIL_APP_PASSWORD=<16-char Google App Password>
NOTIFY_EMAIL=juancruzr1975@gmail.com
TARGET_DATE=2026-09-17
APPOINTMENT_URL=https://ais.usvisa-info.com/en-es/niv/schedule/74726699/appointment?confirmed_limit_message=1&commit=Continue
```

---

## macOS Scheduling (`launchd`)

File: `com.visa.monitor.plist` installed to `~/Library/LaunchAgents/`

- Runs `python3 monitor.py` every **300 seconds** (5 minutes)
- Auto-starts on login, restarts on failure
- Logs stdout/stderr to `~/Library/Logs/visa-monitor.log`

---

## Anti-Detection Measures

- Random delay 2–5 seconds before each HTTP request
- Real Chrome User-Agent header
- Single-URL scraping (not crawling) — low footprint
- Session cookies reused across runs to minimize login frequency

---

## Playwright Fallback

If `checker.py` finds no dates in the HTML (calendar rendered by JS):
- Launch Chromium headless via Playwright
- Navigate to the appointment URL using the persisted session cookies
- Wait for the calendar to render, then extract dates from the DOM
- Same filter logic applies

---

## Verification Plan

1. Run `python3 monitor.py` manually — confirm it logs in and checks the page without errors
2. Temporarily set `TARGET_DATE` to a far-future date (e.g., 2027-01-01) and verify the email alert fires when a date is detected
3. Confirm the launchd job is running: `launchctl list | grep visa`
4. Check `~/Library/Logs/visa-monitor.log` shows 5-minute check entries
5. Kill the session cookie, verify re-authentication works automatically
