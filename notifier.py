import json
import os
import smtplib
import time
import urllib.request
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

NOTIFIED_FILE = os.path.join(os.path.dirname(__file__), "notified.json")
DEDUP_WINDOW_SECONDS = 3600  # 1 hour


def _already_notified(dates: list[date]) -> bool:
    if not os.path.exists(NOTIFIED_FILE):
        return False
    try:
        with open(NOTIFIED_FILE) as f:
            data = json.load(f)
        last_dates = set(data.get("dates", []))
        last_ts = data.get("timestamp", 0)
        current_dates = {str(d) for d in dates}
        return current_dates == last_dates and (time.time() - last_ts) < DEDUP_WINDOW_SECONDS
    except Exception:
        return False


def _record_notification(dates: list[date]) -> None:
    with open(NOTIFIED_FILE, "w") as f:
        json.dump({"dates": [str(d) for d in dates], "timestamp": time.time()}, f)


def send_alert(dates: list[date], booking_url: str) -> None:
    if _already_notified(dates):
        return

    gmail_user = os.environ["VISA_EMAIL"]
    gmail_app_password = os.environ["GMAIL_APP_PASSWORD"]
    notify_email = os.environ["NOTIFY_EMAIL"]

    dates_str = ", ".join(str(d) for d in sorted(dates))

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"VISA SLOT AVAILABLE — {dates_str} — Book now!"
    msg["From"] = gmail_user
    msg["To"] = notify_email

    text_body = f"""VISA APPOINTMENT SLOTS AVAILABLE!

Available dates before your deadline:
{chr(10).join(f'  • {d}' for d in sorted(dates))}

Book now:
{booking_url}

Act fast — slots fill up quickly!
"""

    html_body = f"""<html><body>
<h2 style="color:#d32f2f;">🚨 Visa Appointment Slots Available!</h2>
<p><strong>Available dates before your deadline:</strong></p>
<ul>
{''.join(f'<li><strong>{d}</strong></li>' for d in sorted(dates))}
</ul>
<p><a href="{booking_url}" style="background:#1565c0;color:white;padding:12px 24px;text-decoration:none;border-radius:4px;font-weight:bold;">Book Your Appointment Now</a></p>
<p style="color:#666;font-size:12px;">Act fast — slots fill up quickly!</p>
</body></html>"""

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(gmail_user, gmail_app_password)
        server.sendmail(gmail_user, notify_email, msg.as_string())

    _send_push(dates_str, booking_url)
    _record_notification(dates)
    print(f"[ALERT] Email sent — available dates: {dates_str}")


def _send_push(dates_str: str, booking_url: str) -> None:
    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        return

    message = f"Fechas disponibles: {dates_str}\n\nReserva YA: {booking_url}"
    req = urllib.request.Request(
        f"https://ntfy.sh/{topic}",
        data=message.encode("utf-8"),
        headers={
            "Title": "VISA SLOT DISPONIBLE - Reserva ahora!",
            "Priority": "urgent",
            "Tags": "rotating_light,us",
            "Sound": "really-long-ring",
        },
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=10)
        print(f"[ALERT] Push notification sent to ntfy topic: {topic}")
    except Exception as e:
        print(f"[WARN] Push notification failed: {e}")
