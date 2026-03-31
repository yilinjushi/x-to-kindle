"""
fetch_bookmarks.py — Export X.com bookmarks as individual DOCX files and email each one

Usage:
    python fetch_bookmarks.py [--count 10] [--send-to email@kindle.com] [--outdir DIR]
"""

import sys
import time
import re
import json
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
from app_config import (
    BOOKMARKS_URL,
    CHROME_EXE,
    KINDLE_EMAIL,
    LAUNCH_ARGS,
    MAX_SCROLLS,
    MIN_TEXT_CHARS,
    OUTDIR,
    PYTHON_EXE,
    SENT_HISTORY_FILE,
    SESSION_FILE,
    TARGET_COUNT,
    USER_AGENT,
    ensure_parent_dir,
    load_json_file,
)

# Reuse content extraction + DOCX building from tweet_to_docx
sys.path.insert(0, str(Path(__file__).parent))
from tweet_to_docx import (
    wait_for_content,
    extract_content_from_page,
    build_docx,
    make_all_black,
    title_to_filename,
)
SEND_EMAIL_SCRIPT = Path(__file__).resolve().parent / "send_email.py"


def get_bookmark_urls(page, target_count: int) -> list[str]:
    """Scroll the bookmarks feed and collect tweet URLs."""
    seen = []
    seen_set = set()
    status_pattern = re.compile(r"https://x\.com/[^/]+/status/\d+$")

    print("Loading bookmarks page...")
    page.goto(BOOKMARKS_URL, wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_selector("article[data-testid='tweet']", timeout=20000)
    except Exception:
        pass
    time.sleep(3)

    scroll_attempts = 0
    while len(seen) < target_count and scroll_attempts < MAX_SCROLLS:
        links = page.eval_on_selector_all(
            "a[href*='/status/']",
            "els => [...new Set(els.map(e => e.href))]"
        )
        for link in links:
            if status_pattern.match(link) and link not in seen_set:
                seen.append(link)
                seen_set.add(link)

        print(f"  Found {len(seen)} bookmarks so far...", end="\r")

        if len(seen) >= target_count:
            break

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
        scroll_attempts += 1

    print(f"\nCollected {len(seen)} bookmark URLs.")
    return seen[:target_count]


def status_id_from_url(url: str) -> str:
    match = re.search(r"/status/(\d+)$", url)
    return match.group(1) if match else "unknown"


def send_article(filepath: str, title: str, send_to: str) -> bool:
    """Send a single DOCX file via email."""
    subject = title[:60] if title else Path(filepath).stem
    python_exe = PYTHON_EXE or sys.executable
    result = subprocess.run(
        [python_exe, str(SEND_EMAIL_SCRIPT),
         "--to", send_to,
         "--subject", subject,
         "--attach", filepath],
        capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode == 0:
        print(f"  Sent: {subject!r} → {send_to}")
        return True
    else:
        print(f"  Email error: {result.stderr.strip()}", file=sys.stderr)
        return False


def load_sent_history() -> dict[str, dict]:
    history = load_json_file(SENT_HISTORY_FILE, [])
    return {
        item["url"]: item
        for item in history
        if isinstance(item, dict) and item.get("url")
    }


def save_sent_history(history: dict[str, dict]) -> None:
    ensure_parent_dir(SENT_HISTORY_FILE)
    with open(SENT_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(history.values()), f, ensure_ascii=False, indent=2)


def is_long_article(content: dict, total_chars: int) -> bool:
    return content.get("is_article", False) or total_chars >= MIN_TEXT_CHARS


def main():
    if not Path(SESSION_FILE).exists():
        print("ERROR: No session file found. Run fetch_tweet.py --setup first.", file=sys.stderr)
        sys.exit(1)

    target_count = TARGET_COUNT
    send_to = KINDLE_EMAIL or None
    outdir = OUTDIR

    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == "--count" and i + 1 < len(args):
            target_count = int(args[i + 1])
        elif arg == "--send-to" and i + 1 < len(args):
            send_to = args[i + 1]
        elif arg == "--outdir" and i + 1 < len(args):
            outdir = args[i + 1]

    Path(outdir).mkdir(parents=True, exist_ok=True)
    sent_history = load_sent_history()

    with sync_playwright() as p:
        launch_kwargs = {
            "headless": True,
            "args": LAUNCH_ARGS,
        }
        if CHROME_EXE:
            launch_kwargs["executable_path"] = CHROME_EXE

        browser = p.chromium.launch(**launch_kwargs)
        context = browser.new_context(
            storage_state=SESSION_FILE,
            user_agent=USER_AGENT,
        )
        page = context.new_page()

        # Step 1: collect bookmark URLs
        urls = get_bookmark_urls(page, target_count)
        if not urls:
            print("No bookmarks found. Check that your session is valid.")
            context.close()
            browser.close()
            sys.exit(1)

        # Step 2: for each URL — fetch, convert to DOCX, email
        results = []
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] {url}")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                wait_for_content(page)

                content = extract_content_from_page(page)
                title = content["title"] or f"article_{i}"
                author = content["author"]
                items = content["items"]

                n_img = sum(1 for x in items if x["type"] == "image")
                n_txt = sum(1 for x in items if x["type"] != "image")
                total_chars = sum(len(x.get("text", "")) for x in items if x["type"] != "image")
                print(f"  {title!r} | {n_txt} text blocks, {n_img} images, {total_chars} chars")

                if url in sent_history:
                    print("  SKIP: this URL was already sent before.")
                    results.append((title, None, 0))
                    continue

                if not is_long_article(content, total_chars):
                    print(
                        f"  SKIP: not a long article "
                        f"(needs X Article or at least {MIN_TEXT_CHARS} chars)."
                    )
                    results.append((title, None, 0))
                    continue

                filename = f"{title_to_filename(title)}-{status_id_from_url(url)}.docx"
                filepath = str(Path(outdir) / filename)

                if Path(filepath).exists():
                    print(f"  Reusing existing file: {filename}")

                cookies = {c["name"]: c["value"] for c in context.cookies()}

                if not Path(filepath).exists():
                    doc, n_inserted = build_docx(title, author, url, items, cookies)
                    make_all_black(doc)
                    doc.save(filepath)
                    size_kb = Path(filepath).stat().st_size // 1024
                    print(f"  Saved: {filename} ({size_kb} KB)")
                else:
                    n_inserted = 0

                results.append((title, filepath, n_inserted))

                if send_to and send_article(filepath, title, send_to):
                    sent_history[url] = {
                        "url": url,
                        "title": title,
                        "author": author,
                        "chars": total_chars,
                    }
                    save_sent_history(sent_history)

            except Exception as e:
                print(f"  ERROR: {e}")
                results.append((f"article_{i}", None, 0))

        context.close()
        browser.close()

    # Summary
    print(f"\n{'='*50}")
    print(f"Done. {len(results)} article(s) processed.")
    succeeded = [(t, f, n) for t, f, n in results if f]
    print(f"  Saved:  {len(succeeded)} DOCX file(s) → {outdir}")
    if send_to:
        print(f"  Emails: sent individually to {send_to}")
        print(f"  History: {len(sent_history)} sent URL(s) tracked in {SENT_HISTORY_FILE}")
    else:
        print("  Emails: skipped (no KINDLE_EMAIL configured)")


if __name__ == "__main__":
    main()
