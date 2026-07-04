# US Visa Appointment Monitor

## Problem

US visa appointment slots at embassies are extremely scarce. Cancellations open and fill within minutes, making it nearly impossible to find an earlier date by checking manually. Anyone with a deadline needs a way to monitor availability 24/7 without human intervention.

## Solution

A lightweight Python daemon that polls the official US visa scheduling system every 5 minutes and delivers an immediate alert — email + mobile push notification — the moment a slot opens before your target date. The push notification uses maximum priority, bypassing silent mode and Do Not Disturb, so it can wake you up if needed.

## How It Works

The monitor uses **authenticated session scraping with CSRF handling, cookie persistence, and real-time push notifications via ntfy**. Specifically:

1. **Auth** — logs into `ais.usvisa-info.com` by extracting the CSRF token from the login page meta tag, submitting credentials via the site's AJAX form handler, and persisting the session cookie to disk. On subsequent runs the saved cookie is reused; re-authentication triggers automatically on session expiry.
2. **Availability check** — calls the site's internal JSON API (`/appointment/days/{facility_id}.json`) directly, bypassing the JavaScript-rendered calendar. Returns a list of available dates filtered to those on or before `TARGET_DATE`.
3. **Notification** — sends a Gmail SMTP email and a high-priority ntfy push notification simultaneously. A deduplication guard prevents repeat alerts for the same slots within one hour.
4. **Scheduling** — runs as a macOS `launchd` service every 300 seconds, with automatic restart on failure and network-error retries.

## Setup

### Requirements

- macOS or Windows with Python 3.10+
- A [ais.usvisa-info.com](https://ais.usvisa-info.com) account with a pending appointment
- A Gmail account
- The **ntfy** app on your phone ([iOS](https://apps.apple.com/app/ntfy/id1625396347) / [Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy))

### 1. Clone the repo

**macOS** — open Terminal (`Cmd + Space`, type "Terminal"):
```bash
cd ~/Desktop && git clone https://github.com/Juan-sanchez-reulet/agent.git visa-monitor && cd visa-monitor
```

**Windows** — open PowerShell:
```powershell
cd $env:USERPROFILE\Desktop; git clone https://github.com/Juan-sanchez-reulet/agent.git visa-monitor; cd visa-monitor
```

> If git is not installed, download it from [git-scm.com](https://git-scm.com/download/win) (Windows) or accept the prompt (macOS).

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure

**macOS:**
```bash
cp .env.example .env
open -e .env
```

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
notepad .env
```

Fill in each value — see the [Configuration](#configuration) section below. Save and close.

### 4. Test it

**macOS:**
```bash
TARGET_DATE=2026-12-31 python3 monitor.py
```

**Windows (PowerShell):**
```powershell
$env:TARGET_DATE="2026-12-31"; python monitor.py
```

You should see:
```
[ALERT] Push notification sent to ntfy topic: your-topic
[ALERT] Email sent — available dates: 2026-10-01, 2026-10-02, ...
```

A push notification will arrive on your phone and an email in your inbox.

### 5. Install the background service

**macOS:**
```bash
bash install.sh
```
This installs a `launchd` job that runs every 5 minutes, survives reboots, and logs to `~/Library/Logs/visa-monitor.log`.

**Windows** — run PowerShell as Administrator, then:
```powershell
.\install-windows.ps1
```
This installs a Windows Task Scheduler job that runs every 5 minutes and logs to `%USERPROFILE%\AppData\Local\Logs\visa-monitor.log`.

**Verify it's running:**

macOS:
```bash
launchctl list | grep visa
tail -f ~/Library/Logs/visa-monitor.log
```

Windows:
```powershell
Get-ScheduledTask -TaskName "VisaAppointmentMonitor"
Get-Content "$env:USERPROFILE\AppData\Local\Logs\visa-monitor.log" -Tail 20
```

### 6. Configure ntfy for silent/DND override

To receive alerts even when your phone is on silent:
- **iOS:** Settings → Ntfy → Notifications → enable **Critical Alerts**
- **Android:** long-press a ntfy notification → set channel importance to **Urgent**

### Stop the monitor

**macOS:**
```bash
launchctl unload ~/Library/LaunchAgents/com.visa.monitor.plist
```

**Windows (PowerShell):**
```powershell
Unregister-ScheduledTask -TaskName "VisaAppointmentMonitor" -Confirm:$false
```

---

## Configuration

All configuration lives in `.env`. Copy `.env.example` and fill in your values.

| Variable | Description |
|---|---|
| `VISA_EMAIL` | Email address for ais.usvisa-info.com |
| `VISA_PASSWORD` | Password for ais.usvisa-info.com |
| `GMAIL_APP_PASSWORD` | 16-char Google App Password — generate at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) (requires 2-Step Verification) |
| `NOTIFY_EMAIL` | Email address to receive alerts |
| `TARGET_DATE` | Deadline — any slot on or before this date triggers an alert (format: `YYYY-MM-DD`) |
| `APPOINTMENT_URL` | Your full scheduling URL from the browser address bar after logging in |
| `FACILITY_ID` | Numeric facility ID found in the appointment page HTML (Madrid = `7`) |
| `NTFY_TOPIC` | A unique string for your push channel, e.g. `visa-monitor-yourname-2026` |

**Finding your `APPOINTMENT_URL`:** log in to ais.usvisa-info.com, navigate to Schedule Appointment, and copy the URL from the address bar.

**Finding your `FACILITY_ID`:** open DevTools on the appointment page, search the HTML for `facility_id`. Each embassy has a different ID.

---

## Troubleshooting

| Error | Fix |
|---|---|
| `AUTH ERROR: Could not find CSRF token` | The site may be temporarily down or blocking the request — wait a few minutes |
| `AUTH ERROR: Login failed` | Check `VISA_EMAIL` and `VISA_PASSWORD` in `.env` |
| `NOTIFY ERROR: BadCredentials` | `GMAIL_APP_PASSWORD` is wrong — generate a new one |
| `No slots available` | Working correctly — no slots before your deadline yet |
| Push not arriving | Make sure the ntfy topic in the app matches `NTFY_TOPIC` exactly |
