# X Bookmarks to Kindle

This project fetches your X bookmarks, keeps only long-form items, converts them to DOCX, and emails each new item to Kindle.

## What counts as a long article

- Any native X Article is always eligible.
- Regular bookmarked posts are only sent when their extracted text length is at least `MIN_TEXT_CHARS`.
- The default threshold is `1200` characters and can be changed with an environment variable.

## Duplicate protection

- Sent items are tracked by URL in [state/sent_articles.json](/L:/FilenPersonal/aitool/state/sent_articles.json).
- If a bookmarked URL already exists there, it is skipped.
- This is more reliable than checking only whether a DOCX filename already exists.

## Local run

1. Install dependencies: `pip install -r requirements.txt`
2. Install Playwright Chromium: `python -m playwright install chromium`
3. Put your X login state in `x_session.json`
4. Set environment variables:
   `KINDLE_EMAIL`, `GMAIL_USER`, `GMAIL_APP_PASSWORD`
5. Run: `python fetch_bookmarks.py`

## GitHub Actions setup

Create a new **private** GitHub repository and add these repository secrets:

- `KINDLE_EMAIL`: your Send-to-Kindle email address
- `GMAIL_USER`: the Gmail sender account
- `GMAIL_APP_PASSWORD`: the Gmail app password
- `X_SESSION_JSON`: the full contents of your local `x_session.json`

The workflow in `.github/workflows/kindle-delivery.yml` runs twice a day:

- `02:00 UTC` = `10:00` China Standard Time
- `06:00 UTC` = `14:00` China Standard Time

It also supports manual runs through `workflow_dispatch`.
