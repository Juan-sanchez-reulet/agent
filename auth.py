import os
import pickle
import time
import requests
from bs4 import BeautifulSoup

SESSION_FILE = os.path.join(os.path.dirname(__file__), "session.pkl")
LOGIN_URL = "https://ais.usvisa-info.com/en-es/niv/users/sign_in"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}


class AuthError(Exception):
    pass


def _save_session(session: requests.Session) -> None:
    with open(SESSION_FILE, "wb") as f:
        pickle.dump(session.cookies, f)


def _load_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "rb") as f:
            session.cookies.update(pickle.load(f))
    return session


def is_authenticated(response: requests.Response) -> bool:
    # For regular (non-AJAX) responses, check the final URL
    return "sign_in" not in response.url and response.status_code == 200


def login(session: requests.Session) -> None:
    email = os.environ["VISA_EMAIL"]
    password = os.environ["VISA_PASSWORD"]

    resp = session.get(LOGIN_URL, headers=HEADERS)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Try <input name="authenticity_token"> first (common in Rails forms)
    csrf_token = None
    token_input = soup.find("input", {"name": "authenticity_token"})
    if token_input:
        csrf_token = token_input.get("value")

    # Fallback: <meta name="csrf-token" content="...">
    if not csrf_token:
        meta = soup.find("meta", {"name": "csrf-token"})
        if meta:
            csrf_token = meta.get("content")

    if not csrf_token:
        # Debug: print first 2000 chars of the page to help diagnose
        print("[DEBUG] Login page snippet:", resp.text[:2000], flush=True)
        raise AuthError("Could not find CSRF token on login page")

    payload = {
        "user[email]": email,
        "user[password]": password,
        "policy_confirmed": "1",
        "commit": "Sign In",
    }

    # Form uses data-remote="true" (Rails UJS AJAX), so mimic XHR request
    ajax_headers = {
        **HEADERS,
        "Referer": LOGIN_URL,
        "X-CSRF-Token": csrf_token,
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*; q=0.01",
    }
    resp = session.post(LOGIN_URL, data=payload, headers=ajax_headers)
    resp.raise_for_status()

    # AJAX response contains JS redirect — check for account URL in response body
    if "/en-es/niv/account" not in resp.text and "sign_in" in resp.text:
        raise AuthError("Login failed — check VISA_EMAIL and VISA_PASSWORD")

    # Follow the redirect to establish full session
    session.get("https://ais.usvisa-info.com/en-es/niv/account", headers=HEADERS)

    _save_session(session)


def get_authenticated_session(appointment_url: str) -> requests.Session:
    session = _load_session()

    # Quick probe to check if session is still valid
    resp = session.get(appointment_url, headers=HEADERS, allow_redirects=True)

    if is_authenticated(resp):
        return session

    # Session expired — re-login
    for attempt in range(1, 4):
        try:
            login(session)
            return session
        except AuthError as e:
            if attempt == 3:
                raise
            time.sleep(5 * attempt)

    raise AuthError("Failed to authenticate after 3 attempts")
