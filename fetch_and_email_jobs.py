"""
Remote PM / Product Owner / Business Analyst Job Alert
--------------------------------------------------------
Fetches remote job listings from free public job-board APIs, filters
them for Product Manager / Product Owner / Business Analyst roles,
and emails a formatted digest. Designed to be run daily via
GitHub Actions (see .github/workflows/daily-job-alert.yml).

Data sources (all free, no API key required):
  - Remotive       https://remotive.com/api/remote-jobs
  - Arbeitnow      https://arbeitnow.com/api/job-board-api
  - Jobicy         https://jobicy.com/api/v2/remote-jobs
  - RemoteOK       https://remoteok.com/api

Google Careers has no public API, so it is not included here.
See README.md for how to add it later via a paid service like SerpApi.
"""

import os
import smtplib
import ssl
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

ROLE_KEYWORDS = [
    "product manager",
    "product owner",
    "business analyst",
    "senior product manager",
    "associate product manager",
]

# Locations that count as "relevant" — worldwide remote roles + anything
# that explicitly mentions India.
LOCATION_HINTS = ["india", "worldwide", "anywhere", "remote", "global"]

REQUEST_TIMEOUT = 15  # seconds
HEADERS = {"User-Agent": "Mozilla/5.0 (job-alert-bot/1.0)"}


def title_matches(title: str) -> bool:
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in ROLE_KEYWORDS)


def location_matches(location: str) -> bool:
    if not location:
        return True  # some sources leave this blank for fully-remote roles
    location_lower = location.lower()
    return any(hint in location_lower for hint in LOCATION_HINTS)


# ---------------------------------------------------------------------------
# FETCHERS — each returns a list of dicts: title, company, location, url, source
# ---------------------------------------------------------------------------

def fetch_remotive():
    jobs = []
    try:
        resp = requests.get(
            "https://remotive.com/api/remote-jobs",
            params={"category": "product"},
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        for job in resp.json().get("jobs", []):
            jobs.append({
                "title": job.get("title", ""),
                "company": job.get("company_name", ""),
                "location": job.get("candidate_required_location", ""),
                "url": job.get("url", ""),
                "source": "Remotive",
            })
    except Exception as e:
        print(f"[warn] Remotive fetch failed: {e}")
    return jobs


def fetch_arbeitnow():
    jobs = []
    try:
        resp = requests.get(
            "https://arbeitnow.com/api/job-board-api",
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        for job in resp.json().get("data", []):
            if not job.get("remote", False):
                continue
            jobs.append({
                "title": job.get("title", ""),
                "company": job.get("company_name", ""),
                "location": job.get("location", "Remote"),
                "url": job.get("url", ""),
                "source": "Arbeitnow",
            })
    except Exception as e:
        print(f"[warn] Arbeitnow fetch failed: {e}")
    return jobs


def fetch_jobicy():
    jobs = []
    try:
        resp = requests.get(
            "https://jobicy.com/api/v2/remote-jobs",
            params={"count": 50, "tag": "product-manager"},
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        for job in resp.json().get("jobs", []):
            jobs.append({
                "title": job.get("jobTitle", ""),
                "company": job.get("companyName", ""),
                "location": job.get("jobGeo", "Remote"),
                "url": job.get("url", ""),
                "source": "Jobicy",
            })
    except Exception as e:
        print(f"[warn] Jobicy fetch failed: {e}")
    return jobs


def fetch_remoteok():
    jobs = []
    try:
        resp = requests.get(
            "https://remoteok.com/api",
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        # First element is a legal notice, not a job — skip it
        for job in data[1:]:
            jobs.append({
                "title": job.get("position", ""),
                "company": job.get("company", ""),
                "location": job.get("location", "Remote"),
                "url": job.get("url", ""),
                "source": "RemoteOK",
            })
    except Exception as e:
        print(f"[warn] RemoteOK fetch failed: {e}")
    return jobs


# ---------------------------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------------------------

def collect_and_filter_jobs():
    all_jobs = (
        fetch_remotive()
        + fetch_arbeitnow()
        + fetch_jobicy()
        + fetch_remoteok()
    )

    seen_urls = set()
    filtered = []
    for job in all_jobs:
        if not job["title"] or not job["url"]:
            continue
        if job["url"] in seen_urls:
            continue
        if not title_matches(job["title"]):
            continue
        if not location_matches(job["location"]):
            continue
        seen_urls.add(job["url"])
        filtered.append(job)

    # Sort: India-mentioning roles first, then everything else, alphabetically by title
    def sort_key(job):
        is_india = "india" in (job["location"] or "").lower()
        return (0 if is_india else 1, job["title"].lower())

    filtered.sort(key=sort_key)
    return filtered


def build_email_html(jobs):
    today = datetime.now(timezone.utc).strftime("%d %b %Y")
    if not jobs:
        return f"""
        <h2>Remote PM / PO / BA Job Digest — {today}</h2>
        <p>No matching roles found today. The pipeline ran successfully, but
        nothing matched the current filters.</p>
        """

    rows = ""
    for job in jobs:
        india_tag = (
            " 🇮🇳" if "india" in (job["location"] or "").lower() else ""
        )
        rows += f"""
        <tr>
          <td style="padding:8px;border-bottom:1px solid #eee;">
            <a href="{job['url']}" style="text-decoration:none;color:#2563eb;font-weight:600;">
              {job['title']}{india_tag}
            </a><br/>
            <span style="color:#555;font-size:13px;">
              {job['company']} &middot; {job['location'] or 'Remote'} &middot; {job['source']}
            </span>
          </td>
        </tr>
        """

    return f"""
    <h2>Remote PM / PO / BA Job Digest — {today}</h2>
    <p>{len(jobs)} matching role(s) found across Remotive, Arbeitnow, Jobicy, and RemoteOK.</p>
    <table style="width:100%;border-collapse:collapse;font-family:Arial,sans-serif;font-size:14px;">
      {rows}
    </table>
    <p style="color:#999;font-size:12px;margin-top:16px;">
      Sent automatically by your GitHub Actions job-alert bot.
    </p>
    """


def send_email(html_body):
    sender = os.environ["GMAIL_ADDRESS"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]
    recipient = os.environ["RECIPIENT_EMAIL"]

    today = datetime.now(timezone.utc).strftime("%d %b %Y")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Remote PM/PO/BA Job Digest — {today}"
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(html_body, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls(context=context)
        server.login(sender, app_password)
        server.sendmail(sender, recipient, msg.as_string())

    print(f"Email sent to {recipient}")


def main():
    jobs = collect_and_filter_jobs()
    print(f"Found {len(jobs)} matching jobs.")
    html = build_email_html(jobs)
    send_email(html)


if __name__ == "__main__":
    main()
