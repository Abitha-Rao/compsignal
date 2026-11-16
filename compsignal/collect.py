"""Collect open job postings from the official public job-board APIs.

Greenhouse, Lever and Ashby all publish read-only JSON for companies that use them.
We use only those endpoints, identify ourselves, and wait between requests.
"""
import html
import json
import os
import re
import ssl
import time
import urllib.request

UA = {"User-Agent": "compsignal/0.1 (personal research project; low request rate)"}
DELAY = 0.4  # seconds between requests


def _context():
    # Some Python installs on macOS ship without CA certificates; fall back to the system bundle.
    # Verification stays ON in every case.
    for path in ("/etc/ssl/cert.pem",):
        if os.path.exists(path):
            return ssl.create_default_context(cafile=path)
    return ssl.create_default_context()


_CTX = _context()


def _get(url):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=25, context=_CTX) as r:
            data = json.load(r)
        time.sleep(DELAY)
        return data
    except Exception:
        time.sleep(0.1)
        return None


def _strip(raw):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(raw or ""))).strip()


def _greenhouse(slug):
    d = _get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true")
    if not d or not d.get("jobs"):
        return None
    return [
        {
            "job_id": str(j["id"]),
            "title": j.get("title", ""),
            "location": (j.get("location") or {}).get("name", ""),
            "url": j.get("absolute_url", ""),
            "text": _strip(j.get("content", "")),
        }
        for j in d["jobs"]
    ]


def _lever(slug):
    d = _get(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    if not isinstance(d, list) or not d:
        return None
    out = []
    for j in d:
        extra = " ".join(
            f"{x.get('text', '')} {_strip(x.get('content', ''))}" for x in j.get("lists", [])
        )
        out.append(
            {
                "job_id": j["id"],
                "title": j.get("text", ""),
                "location": (j.get("categories") or {}).get("location", ""),
                "url": j.get("hostedUrl", ""),
                "text": _strip(f"{j.get('descriptionPlain', '')} {extra}"),
            }
        )
    return out


def _ashby(slug):
    d = _get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
    if not d or not d.get("jobs"):
        return None
    return [
        {
            "job_id": j["id"],
            "title": j.get("title", ""),
            "location": j.get("location", ""),
            "url": j.get("jobUrl", ""),
            "text": _strip(j.get("descriptionPlain", "")),
        }
        for j in d["jobs"]
    ]


FETCHERS = (("greenhouse", _greenhouse), ("lever", _lever), ("ashby", _ashby))


def fetch_company(slug):
    """Return (source, jobs) for the first job board that has postings, else (None, [])."""
    for name, fn in FETCHERS:
        jobs = fn(slug)
        if jobs:
            return name, jobs
    return None, []
