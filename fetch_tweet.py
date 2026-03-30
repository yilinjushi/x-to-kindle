"""
fetch_tweet.py — X.com tweet content fetcher using Playwright + dedicated profile

Usage:
  First-time setup (launch browser, log in manually, save session):
    python fetch_tweet.py --setup

  Fetch a tweet (headless, reuses saved session):
    python fetch_tweet.py https://x.com/xxx/status/123456
"""

import sys
import time
from playwright.sync_api import sync_playwright
from pathlib import Path
from app_config import CHROME_EXE, LAUNCH_ARGS, SESSION_FILE, USER_AGENT

PROFILE_DIR = r"L:\GoogleChromePortable\PlaywrightProfile"


def setup_session():
    """Open browser with dedicated profile, wait for user to log in, then save storage state."""
    print("=== Setup mode ===")
    print("A browser window will open. Log in to X.com, then come back here and press Enter.")

    with sync_playwright() as p:
        launch_kwargs = {
            "user_data_dir": PROFILE_DIR,
            "headless": False,
            "args": LAUNCH_ARGS,
        }
        if CHROME_EXE:
            launch_kwargs["executable_path"] = CHROME_EXE

        context = p.chromium.launch_persistent_context(**launch_kwargs)
        page = context.new_page()
        page.goto("https://x.com/login")

        print("Waiting for login (up to 5 minutes)... Close the browser after logging in.")
        # Poll until URL contains /home or browser is closed
        deadline = time.time() + 300
        while time.time() < deadline:
            try:
                current_url = page.url
                if "/home" in current_url:
                    break
            except Exception:
                # Browser was closed by user — treat as signal to save
                break
            time.sleep(2)
        time.sleep(1)

        try:
            context.storage_state(path=SESSION_FILE)
            print(f"Session saved to: {SESSION_FILE}")
        except Exception as e:
            print(f"Could not save session: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            try:
                context.close()
            except Exception:
                pass

    print("Setup complete. You can now run: python fetch_tweet.py <URL>")


def fetch_tweet(url: str) -> str:
    """Fetch tweet text from a given X.com/Twitter URL using saved session."""
    if not Path(SESSION_FILE).exists():
        print("ERROR: No session file found. Run with --setup first.", file=sys.stderr)
        sys.exit(1)

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

        page.goto(url, wait_until="domcontentloaded", timeout=60000)

        # Wait specifically for tweetText to appear
        try:
            page.wait_for_selector("[data-testid='tweetText']", timeout=20000)
        except Exception:
            # Try waiting for the article at minimum
            try:
                page.wait_for_selector("article[data-testid='tweet']", timeout=10000)
            except Exception:
                pass
            time.sleep(3)

        # Extract tweet text — first element is the main tweet
        tweet_text_elements = page.query_selector_all("[data-testid='tweetText']")
        if tweet_text_elements:
            # Take only the first one (the main tweet, not replies)
            text = tweet_text_elements[0].inner_text()
        else:
            article = page.query_selector("article[data-testid='tweet']")
            text = article.inner_text() if article else "(tweet text not found)"

        # Get author info from the first User-Name element
        author = ""
        author_el = page.query_selector("[data-testid='User-Name']")
        if author_el:
            author = author_el.inner_text().replace("\n", " ")

        context.close()
        browser.close()

    result = ""
    if author:
        result += f"Author: {author}\n"
    result += f"URL: {url}\n"
    result += f"---\n{text}"
    return result


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    arg = sys.argv[1]

    if arg == "--setup":
        setup_session()
    elif arg.startswith("http"):
        content = fetch_tweet(arg)
        print(content)
    else:
        print(f"Unknown argument: {arg}", file=sys.stderr)
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
