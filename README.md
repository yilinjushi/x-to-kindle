# X Bookmarks to Kindle

This project fetches your X bookmarks, keeps only long-form items, converts them to DOCX, and emails each new item to Kindle.

Every extracted article is also preserved as Markdown with locally downloaded images and published as a framework-free static blog from `site/`.

## Public reading archive

- Durable source: Markdown under `archive/<year>/` in the private repository `yilinjushi/x-to-kindle-archive`, and images under `site/assets/`
- Workflows check the private repository out to `archive-repo/` with the `ARCHIVE_DEPLOY_KEY` deploy key and point `ARCHIVE_DIR` at `archive-repo/archive`. Local runs write to `archive/` (gitignored) unless `ARCHIVE_DIR` is set.
- Published output: plain HTML and CSS under `site/`
- Rebuild locally: `python build_site.py`
- Cloudflare Pages output directory: `site`
- No build command is required because the delivery workflows regenerate the HTML before committing.
- To publish recent bookmarks without sending them to Kindle, run the `Publish Bookmarks To Blog` workflow.
- Blog synchronization also runs hourly at minute 17 (UTC), scanning the latest 50 bookmarks. GitHub scheduling and Pages deployment can add delay; saving a bookmark does not instantly update the site.
- Blog sync includes short posts and skips URLs already present in the archive, independently of Kindle sent history. Manual runs default to 15 bookmarks; increase `count` for a larger backlog.
- Failed extractions make the sync fail visibly; successful archives are still committed so the next run can retry only missing items.

## NotebookLM mirror

- A Claude Code routine (Haiku, every 3 days at 12:00 UTC) writes `category: "<slug>"` into new archive files, using `categories.json` in the private repository as the fixed category table.
- `.github/workflows/notebooklm-sync.yml` runs daily at 13:00 UTC and calls `notebooklm_sync.py`: categorized articles are deduplicated, merged into one text source per category and month, and uploaded to one NotebookLM notebook per category (a new notebook `<name> · 2` is created when one is full). Changed sources are replaced; sources or notebooks deleted in the NotebookLM web UI are re-uploaded on the next run.
- Sync state lives in `state/notebooklm.json` in the private repository. Preview the plan without signing in: `python notebooklm_sync.py --archive-dir <archive> --categories <categories.json> --state <state.json> --dry-run`.
- It uses the unofficial [`notebooklm-py`](https://github.com/teng-lin/notebooklm-py) client, which can break when Google changes internal endpoints.

## What counts as a long article

- Any native X Article is always eligible.
- Regular bookmarked posts are only sent when their extracted text length is at least `MIN_TEXT_CHARS`.
- The default threshold is `1200` characters and can be changed with an environment variable.

## Duplicate protection

- Sent items are tracked by URL in `state/sent_articles.json`.
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
- `ARCHIVE_DEPLOY_KEY`: private SSH key whose public half is a write-enabled deploy key on `yilinjushi/x-to-kindle-archive`
- `NOTEBOOKLM_STORAGE_STATE`, `NOTEBOOKLM_MASTER_TOKEN`: contents of `storage_state.json` and `master_token.json` from `notebooklm login --master-token`

The workflow in `.github/workflows/kindle-delivery.yml` runs twice a day:

- `02:00 UTC` = `10:00` China Standard Time
- `06:00 UTC` = `14:00` China Standard Time

It also supports manual runs through `workflow_dispatch`.

## iPhone Share Shortcut Flow

For single web articles shared from iPhone:

- Use `.github/workflows/send-web-to-kindle.yml`
- Trigger it with `workflow_dispatch`
- Provide the article URL as the `url` input
- Sent web URLs are tracked in `state/sent_web_articles.json`.
