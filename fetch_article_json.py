"""Fetch a single X.com tweet/article using the saved authenticated session and write JSON.

Usage:
    python fetch_article_json.py <URL> [--output article.json]
"""

import argparse
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from app_config import CHROME_EXE, LAUNCH_ARGS, SESSION_FILE, USER_AGENT
from tweet_to_docx import extract_content_from_page, wait_for_content


def fetch_article(url: str) -> dict:
    session_path = Path(SESSION_FILE)
    if not session_path.exists():
        raise RuntimeError(
            f"X session file not found: {session_path}. Restore X_SESSION_JSON first."
        )

    with sync_playwright() as p:
        launch_kwargs = {
            "headless": True,
            "args": LAUNCH_ARGS,
        }
        if CHROME_EXE:
            launch_kwargs["executable_path"] = CHROME_EXE

        browser = p.chromium.launch(**launch_kwargs)
        context = browser.new_context(
            storage_state=str(session_path),
            user_agent=USER_AGENT,
        )
        page = context.new_page()

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            wait_for_content(page)
            content = extract_content_from_page(page)
        finally:
            context.close()
            browser.close()

    text_parts = [
        item.get("text", "")
        for item in content.get("items", [])
        if item.get("type") != "image" and item.get("text")
    ]

    return {
        "url": url,
        "title": content.get("title", ""),
        "author": content.get("author", ""),
        "is_article": bool(content.get("is_article")),
        "text": "\n\n".join(text_parts),
        "items": content.get("items", []),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch an X tweet/article as JSON")
    parser.add_argument("url", help="X.com/Twitter status or article URL")
    parser.add_argument("--output", default="article.json", help="Output JSON path")
    args = parser.parse_args()

    try:
        result = fetch_article(args.url)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Title: {result['title']}")
    print(f"Author: {result['author']}")
    print(f"X Article: {result['is_article']}")
    print(f"Characters: {len(result['text'])}")
    print(f"Output: {output}")


if __name__ == "__main__":
    main()
