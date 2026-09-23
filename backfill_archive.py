"""Archive articles that reached Kindle before the archive existed, dated by their first send."""

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

from playwright.sync_api import sync_playwright

from app_config import CHROME_EXE, LAUNCH_ARGS, SESSION_FILE, USER_AGENT
from archive import save_article_archive
from fetch_bookmarks import load_archived_urls
from fetch_bookmarks import load_sent_history as load_sent_x_history
from send_web_article import extract_article, extract_image_urls, fetch_html
from send_web_article import load_sent_history as load_sent_web_history
from tweet_to_docx import extract_content_from_page, wait_for_content

HISTORY_FILES = ("state/sent_articles.json", "state/sent_web_articles.json")
_URL_LINE = re.compile(r'^\+\s*"url":\s*"([^"]+)"')


def first_sent_dates() -> dict[str, date]:
    """Map each URL to the date of the commit that first added it to a send history file."""
    output = subprocess.run(
        ["git", "log", "--reverse", "--format=@@%ad", "--date=short", "-p", "--", *HISTORY_FILES],
        capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout
    dates: dict[str, date] = {}
    current = None
    for line in output.splitlines():
        if line.startswith("@@") and not line.startswith("@@ "):
            current = date.fromisoformat(line[2:12])
        elif current and (match := _URL_LINE.match(line)):
            dates.setdefault(match.group(1), current)
    return dates


def _archive_x(page, context, url: str, saved_at: date) -> bool:
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    wait_for_content(page)
    content = extract_content_from_page(page)
    items = content["items"]
    total_chars = sum(len(x.get("text", "")) for x in items if x["type"] != "image")
    if not total_chars and not any(x["type"] == "image" for x in items):
        print("  SKIP: no readable content (deleted or protected post).")
        return False
    path = save_article_archive(
        url=url,
        title=content["title"] or url,
        text="\n\n".join(x["text"] for x in items if x["type"] != "image" and x.get("text")),
        author=content["author"],
        source="x_bookmark",
        chars=total_chars,
        saved_at=saved_at,
        items=items,
        cookies={c["name"]: c["value"] for c in context.cookies()},
    )
    print(f"  Archived: {path.name}")
    return True


def _archive_web(url: str, record: dict, saved_at: date) -> bool:
    html = fetch_html(url)
    title, paragraphs = extract_article(html, record.get("title") or None)
    if not paragraphs:
        print("  SKIP: text extraction failed.")
        return False
    path = save_article_archive(
        url=url,
        title=title,
        text="\n\n".join(paragraphs),
        source=record.get("source", "web"),
        chars=sum(len(p) for p in paragraphs),
        saved_at=saved_at,
        image_urls=extract_image_urls(html, url),
    )
    print(f"  Archived: {path.name}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=0, help="stop after this many attempts (0 = all)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    archived = load_archived_urls()
    dates = first_sent_dates()
    x_history, web_history = load_sent_x_history(), load_sent_web_history()
    x_todo = [url for url in x_history if url not in archived]
    web_todo = [url for url in web_history if url not in archived]
    fallback = date(2026, 3, 30)
    print(f"Missing from archive: {len(x_todo)} X, {len(web_todo)} web; {len(dates)} URLs dated from git history.")
    if args.dry_run:
        for url in x_todo + web_todo:
            print(f"  {dates.get(url, fallback)} {url}")
        return

    attempts = archived_count = 0
    with sync_playwright() as p:
        launch_kwargs = {"headless": True, "args": LAUNCH_ARGS}
        if CHROME_EXE:
            launch_kwargs["executable_path"] = CHROME_EXE
        browser = p.chromium.launch(**launch_kwargs)
        context = browser.new_context(storage_state=SESSION_FILE, user_agent=USER_AGENT)
        page = context.new_page()
        for url in x_todo:
            if args.limit and attempts >= args.limit:
                break
            attempts += 1
            print(f"\n[X {attempts}] {url}")
            try:
                archived_count += _archive_x(page, context, url, dates.get(url, fallback))
            except Exception as exc:
                print(f"  ERROR: {exc}")
        context.close()
        browser.close()

    for url in web_todo:
        if args.limit and attempts >= args.limit:
            break
        attempts += 1
        print(f"\n[web {attempts}] {url}")
        try:
            archived_count += _archive_web(url, web_history[url], dates.get(url, fallback))
        except Exception as exc:
            print(f"  ERROR: {exc}")

    print(f"\nDone. Archived {archived_count} of {attempts} attempted.")
    if attempts and not archived_count:
        sys.exit(1)


if __name__ == "__main__":
    main()
