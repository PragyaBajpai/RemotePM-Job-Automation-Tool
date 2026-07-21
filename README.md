# Remote PM / Product Owner / Business Analyst Job Alert

Automatically fetches remote **Product Manager, Product Owner, and Business
Analyst** roles every day and emails you a digest — highlighting roles that
mention India — via a free GitHub Actions cron job.

## What it does

1. Pulls listings from four free, no-key-required job APIs:
   - [Remotive](https://remotive.com/api-documentation)
   - [Arbeitnow](https://arbeitnow.com/api/job-board-api)
   - [Jobicy](https://jobicy.com/api-remote-jobs)
   - [RemoteOK](https://remoteok.com/api)
2. Filters titles for "product manager", "product owner", "business analyst" (and close variants).
3. Keeps remote roles, and flags 🇮🇳 next to any that explicitly mention India.
4. Emails you an HTML digest.
5. Runs automatically every day at **6:30 PM IST** via GitHub Actions — completely free, no server needed.

> **Note on Google Careers:** Google does not offer a public jobs API, so it
> isn't included. If you want Google listings later, the cleanest option is
> a paid service like [SerpApi's Google Jobs API](https://serpapi.com/google-jobs-api) —
> happy to wire that in if you get a key.

## Setup (takes ~10 minutes)

### 1. Create a GitHub repo
- Go to [github.com/new](https://github.com/new), create a repo (e.g. `remote-pm-job-alert`), and push these files to it:
  ```
  fetch_and_email_jobs.py
  requirements.txt
  .github/workflows/daily-job-alert.yml
  ```
  If you're not comfortable with git commands, you can also just use GitHub's
  "Add file → Upload files" button in the browser and drag these three files/folders in.

### 2. Create a Gmail App Password (so the bot can send email as you)
Gmail blocks plain-password logins from scripts, so you need an "App Password":
1. Go to your Google Account → **Security** → turn on **2-Step Verification** (required for App Passwords).
2. Then go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
3. Create a new app password (name it "job-alert-bot"), and copy the 16-character password shown.

### 3. Add secrets to your GitHub repo
In your repo: **Settings → Secrets and variables → Actions → New repository secret**. Add these three:

| Secret name          | Value                                      |
|-----------------------|---------------------------------------------|
| `GMAIL_ADDRESS`       | Your Gmail address (the sender)             |
| `GMAIL_APP_PASSWORD`  | The 16-character app password from step 2   |
| `RECIPIENT_EMAIL`     | The email address you want the digest sent to (can be the same Gmail address) |

### 4. Test it
- Go to the **Actions** tab in your repo → click **Daily Remote PM/PO/BA Job Alert** → **Run workflow** (this uses the `workflow_dispatch` trigger, so you don't have to wait until 6:30 PM to test).
- Check your inbox — you should get the digest within a minute or two.
- If it fails, click into the run log — the error will point at what's missing (usually a secret typo).

### 5. Let it run
Once secrets are set, it will fire automatically every day at 6:30 PM IST — no server, no laptop required, completely free on GitHub's free tier.

## Customizing

- **Change keywords:** edit `ROLE_KEYWORDS` in `fetch_and_email_jobs.py`.
- **Change the time:** edit the `cron` line in `.github/workflows/daily-job-alert.yml`. GitHub Actions cron is always in UTC — subtract 5 hours 30 minutes from your desired IST time to get the UTC cron time.
- **Add more sources:** add a new `fetch_xxx()` function following the same pattern and include it in `collect_and_filter_jobs()`.
- **Send to Slack/Telegram instead:** let me know and I can swap the email step for a webhook post instead.
