"""Live job search using the Jooble API.

Reads JOOBLE_API_KEY from the .env file in the smart-hire folder.
If there is no key, or the request fails, it returns an empty list,
so the rest of the app keeps working with jobs.csv.
"""
import html
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv

# .env lives in the smart-hire folder (one level above backend)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

LAST_ERROR = ""  # short reason for the last failure (never contains the key)


def live_jobs_available():
    return bool(os.getenv("JOOBLE_API_KEY"))


def _strip_html(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def search_live_jobs(keywords, location="India", limit=10):
    """Return a list of job dicts from Jooble, or [] if unavailable."""
    global LAST_ERROR
    LAST_ERROR = ""

    key = os.getenv("JOOBLE_API_KEY")
    if not key:
        LAST_ERROR = "No JOOBLE_API_KEY in .env"
        return []

    try:
        resp = requests.post(
            f"https://jooble.org/api/{key}",
            json={"keywords": keywords, "location": location, "page": 1},
            timeout=15,
        )
        if resp.status_code != 200:
            LAST_ERROR = f"Jooble returned status {resp.status_code}"
            return []
        data = resp.json()
    except requests.RequestException as e:
        LAST_ERROR = f"Network problem ({type(e).__name__})"
        return []
    except ValueError:
        LAST_ERROR = "Jooble reply was not valid JSON"
        return []

    jobs = []
    for j in (data.get("jobs") or [])[:limit]:
        jobs.append({
            "title": j.get("title") or "Untitled",
            "company": j.get("company") or "Not listed",
            "location": j.get("location") or "Not listed",
            "work_type": j.get("type") or "Not listed",
            "salary": j.get("salary") or "",
            "snippet": _strip_html(j.get("snippet"))[:300],
            "url": j.get("link") or "",
            "source": "Jooble",
        })
    return jobs