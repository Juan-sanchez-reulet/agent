# Visa Appointment Monitor

Monitors the US Embassy Madrid appointment page every 5 minutes and sends an email alert when a slot opens before September 17, 2026.

## Setup

### 1. Install dependencies

```bash
cd /Users/lucassanchez/Desktop/casa/agent
pip install -r requirements.txt
playwright install chromium  # only needed for JS fallback
```

### 2. Configure credentials

```bash
cp .env.example .env
```

Edit `.env` and fill in:

| Variable | Value |
|---|---|
| `VISA_EMAIL` | Your email for ais.usvisa-info.com |
| `VISA_PASSWORD` | Your password for ais.usvisa-info.com |
| `GMAIL_APP_PASSWORD` | 16-char Google App Password (see below) |
| `NOTIFY_EMAIL` | Where to send alerts (your Gmail) |
| `TARGET_DATE` | `2026-09-17` |
| `APPOINTMENT_URL` | Leave as-is |

#### Getting a Gmail App Password

1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Select "Mail" + "Mac" → Generate
3. Copy the 16-character password into `GMAIL_APP_PASSWORD`

> You need 2-Step Verification enabled on your Google account for App Passwords to work.

### 3. Test it manually

```bash
cd /Users/lucassanchez/Desktop/casa/agent
python3 monitor.py
```

You should see a line like:
```
[2026-06-06 12:00:00] No slots available before 2026-09-17
```

### 4. Install the background job (runs every 5 min, 24/7)

```bash
cp com.visa.monitor.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.visa.monitor.plist
```

### 5. Verify it's running

```bash
launchctl list | grep visa
```

You should see `com.visa.monitor` in the output.

Watch the logs:
```bash
tail -f ~/Library/Logs/visa-monitor.log
```

## Stopping the monitor

```bash
launchctl unload ~/Library/LaunchAgents/com.visa.monitor.plist
```

## How it works

1. Loads your session cookies (or logs in fresh if expired)
2. Fetches the appointment page
3. Parses the calendar for available dates before Sep 17
4. If slots found → sends you an email alert with the dates and a direct booking link
5. Logs the result and exits (launchd restarts it in 5 minutes)

The email deduplication prevents spam: if the same slots are still available, you only get one email per hour.
