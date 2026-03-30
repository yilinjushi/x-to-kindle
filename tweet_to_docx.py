"""
tweet_to_docx.py — Convert a single X.com tweet/article to DOCX with images inline

Supports both X Articles (long-form, Draft.js) and regular tweets.

Usage:
    python tweet_to_docx.py <URL> [--output path/to/file.docx]

If --output is omitted the file is named after the article title and saved in
the current working directory.
"""

import sys
import time
import io
import re
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from app_config import CHROME_EXE, LAUNCH_ARGS, SESSION_FILE, USER_AGENT

# ── JavaScript snippets ────────────────────────────────────────────────────────

JS_ARTICLE_ITEMS = """
() => {
    const comp = document.querySelector('[data-testid="longformRichTextComponent"]');
    if (!comp) return null;
    const items = [];
    const seen = new Set();
    const all = comp.querySelectorAll('[data-block="true"], [data-testid="tweetPhoto"]');
    for (const el of all) {
        const tid = el.getAttribute('data-testid') || '';
        if (tid === 'tweetPhoto') {
            const img = el.querySelector('img');
            if (img && img.src && img.src.includes('pbs.twimg.com')) {
                const src = img.src.replace(/&name=\\w+$/, '&name=large');
                if (!seen.has(src)) { seen.add(src); items.push({type:'image', src}); }
            }
            continue;
        }
        let parent = el.parentElement;
        let nested = false;
        while (parent && parent !== comp) {
            if (parent.hasAttribute('data-block')) { nested = true; break; }
            parent = parent.parentElement;
        }
        if (nested) continue;
        const tag = el.tagName.toLowerCase();
        const cls = el.className || '';
        const text = (el.innerText || '').trim();
        if (!text) continue;
        let blockType = 'para';
        if (tag === 'li') blockType = 'li';
        else if (tag === 'h1') blockType = 'h1';
        else if (tag === 'h2') blockType = 'h2';
        else if (tag === 'h3' || tag === 'h4') blockType = 'h3';
        else if (cls.includes('longform-header-two') || cls.includes('longform-header-one')) blockType = 'h2';
        items.push({type: blockType, text});
    }
    return items;
}
"""

JS_TWEET_ITEMS = """
() => {
    const container = document.querySelector('article[data-testid="tweet"]');
    if (!container) return null;
    const items = [];
    const seen = new Set();
    const elems = container.querySelectorAll('[data-testid="tweetText"],[data-testid="tweetPhoto"]');
    for (const el of elems) {
        let nested = false;
        let par = el.parentElement;
        while (par && par !== container) {
            const pid = par.getAttribute && par.getAttribute('data-testid');
            if (pid === 'tweetText' || pid === 'tweetPhoto') { nested = true; break; }
            par = par.parentElement;
        }
        if (nested) continue;
        const tid = el.getAttribute('data-testid');
        if (tid === 'tweetText') {
            const text = (el.innerText || '').trim();
            if (text) items.push({type:'para', text});
        } else if (tid === 'tweetPhoto') {
            const img = el.querySelector('img');
            if (img && img.src && img.src.includes('pbs.twimg.com')) {
                const src = img.src.replace(/&name=\\w+$/, '&name=large');
                if (!seen.has(src)) { seen.add(src); items.push({type:'image', src}); }
            }
        }
    }
    return items;
}
"""

JS_TITLE = """
() => {
    const t = document.querySelector('[data-testid="twitter-article-title"]');
    return t ? (t.innerText || '').trim() : '';
}
"""

JS_AUTHOR = """
() => {
    const el = document.querySelector('[data-testid="User-Name"]');
    if (!el) return '';
    return (el.innerText || '').split('\\n').join(' ').trim();
}
"""

# ── Text cleaning ─────────────────────────────────────────────────────────────

CUTOFF_PHRASES = [
    "Want to publish your own Article?",
    "Upgrade to Premium",
    "View quotes",
]
STATS_LINE = re.compile(r"^\d+(\.\d+)?[KkMm]?$")


def is_junk_line(s: str) -> bool:
    s = s.strip()
    return not s or s.startswith("@") or bool(STATS_LINE.match(s))


def strip_tweet_header(raw: str, author_name: str) -> tuple[str, str]:
    """Remove author/handle/stats header from raw tweetText. Returns (title, body)."""
    for phrase in CUTOFF_PHRASES:
        idx = raw.find(phrase)
        if idx != -1:
            raw = raw[:idx]
    lines = raw.strip().splitlines()
    display_name = author_name.split("@")[0].strip()
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not s or is_junk_line(lines[i]):
            i += 1
            continue
        if s == display_name or s.replace(" ", "") == display_name.replace(" ", ""):
            i += 1
            continue
        break
    remaining = lines[i:]
    title, body_start = "", 0
    for j, line in enumerate(remaining):
        if not is_junk_line(line):
            title = line.strip()
            body_start = j + 1
            break
    body_lines, skip_stats = [], True
    for line in remaining[body_start:]:
        if skip_stats and is_junk_line(line):
            continue
        skip_stats = False
        body_lines.append(line)
    return title, "\n".join(body_lines).strip()


def strip_cutoff(text: str) -> str:
    for phrase in CUTOFF_PHRASES:
        idx = text.find(phrase)
        if idx != -1:
            text = text[:idx]
    return text.strip()


# ── Filename helper ───────────────────────────────────────────────────────────

def title_to_filename(title: str, max_len: int = 60) -> str:
    """Sanitize an article title for use as a filename (no extension)."""
    safe = re.sub(r'[\\/:*?"<>|]', '', title)
    safe = re.sub(r'\s+', ' ', safe).strip()
    if len(safe) > max_len:
        safe = safe[:max_len].rstrip()
    return safe or "article"


# ── Image download ────────────────────────────────────────────────────────────

def download_image(url: str, cookies: dict) -> bytes | None:
    try:
        resp = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
                ),
                "Referer": "https://x.com/",
            },
            cookies=cookies,
            timeout=15,
        )
        if resp.status_code == 200 and len(resp.content) > 500:
            return resp.content
    except Exception as e:
        print(f"  Image download failed: {e}")
    return None


# ── DOCX builder ──────────────────────────────────────────────────────────────

def build_docx(
    title: str, author: str, url: str,
    items: list[dict], cookies: dict,
) -> tuple[Document, int]:
    doc = Document()

    h = doc.add_heading(title or "(no title)", level=1)
    h.alignment = WD_ALIGN_PARAGRAPH.LEFT

    meta = doc.add_paragraph()
    meta.add_run(f"by {author}").italic = True

    doc.add_paragraph().add_run(url).font.size = Pt(9)
    doc.add_paragraph()

    n_images = 0
    for item in items:
        t = item["type"]
        if t == "image":
            src = item["src"]
            print(f"  Downloading: {src[:80]}...")
            img_bytes = download_image(src, cookies)
            if img_bytes:
                try:
                    doc.add_picture(io.BytesIO(img_bytes), width=Inches(5.5))
                    doc.add_paragraph()
                    n_images += 1
                except Exception as e:
                    print(f"  Could not insert image: {e}")
            else:
                doc.add_paragraph().add_run(f"[Image unavailable: {src}]").italic = True
        elif t in ("h1", "h2", "h3"):
            doc.add_heading(item["text"], level=int(t[1]))
        elif t == "li":
            doc.add_paragraph(item["text"], style="List Bullet")
        else:
            p = doc.add_paragraph(item["text"])
            p.paragraph_format.space_after = Pt(6)

    return doc, n_images


def make_all_black(doc: Document):
    """Force every run in the document to black — for Kindle's B&W screen."""
    black = RGBColor(0, 0, 0)
    for para in doc.paragraphs:
        for run in para.runs:
            run.font.color.rgb = black
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        run.font.color.rgb = black


# ── Page content extractor (reusable across sessions) ─────────────────────────

def wait_for_content(page):
    """Wait for the page to expose readable content."""
    try:
        page.wait_for_selector(
            "[data-testid='twitterArticleRichTextView'], [data-testid='tweetText']",
            timeout=20000,
        )
    except Exception:
        try:
            page.wait_for_selector("article[data-testid='tweet']", timeout=10000)
        except Exception:
            pass
        time.sleep(3)
    time.sleep(2)  # let images settle


def extract_content_from_page(page) -> dict:
    """
    Extract ordered content from an already-loaded Playwright page.

    Returns:
        {"title": str, "author": str, "items": list[dict], "is_article": bool}
    """
    author = page.evaluate(JS_AUTHOR) or ""
    title = page.evaluate(JS_TITLE) or ""
    is_article = bool(title)

    if is_article:
        raw_items = page.evaluate(JS_ARTICLE_ITEMS) or []
        items = []
        for item in raw_items:
            if item["type"] == "image":
                items.append(item)
            else:
                text = strip_cutoff(item["text"])
                if text:
                    items.append({**item, "text": text})
    else:
        raw_items = page.evaluate(JS_TWEET_ITEMS) or []
        items = []
        first_done = False
        for item in raw_items:
            if item["type"] == "para" and not first_done:
                first_done = True
                extracted_title, body = strip_tweet_header(item["text"], author)
                if not title:
                    title = extracted_title
                if body:
                    items.append({"type": "para", "text": body})
            elif item["type"] == "para":
                text = strip_cutoff(item["text"])
                if text:
                    items.append({"type": "para", "text": text})
            else:
                items.append(item)

    return {"title": title, "author": author, "items": items, "is_article": is_article}


# ── Standalone fetch + convert ────────────────────────────────────────────────

def fetch_and_convert(url: str, output_path: str = None) -> tuple[str, str, int]:
    """
    Fetch a tweet/article, build a black-themed DOCX with images inline.

    Args:
        url: X.com URL
        output_path: explicit save path; if None, derived from article title.

    Returns:
        (title, saved_path, n_images)
    """
    if not Path(SESSION_FILE).exists():
        print("ERROR: No session file. Run fetch_tweet.py --setup first.", file=sys.stderr)
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

        print(f"Loading: {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        wait_for_content(page)

        content = extract_content_from_page(page)
        title = content["title"]
        author = content["author"]
        items = content["items"]

        n_text = sum(1 for x in items if x["type"] != "image")
        n_img = sum(1 for x in items if x["type"] == "image")
        print(f"Format: {'X Article' if content['is_article'] else 'tweet'} | "
              f"{n_text} text block(s), {n_img} image(s)")

        cookies = {c["name"]: c["value"] for c in context.cookies()}
        context.close()
        browser.close()

    if output_path is None:
        output_path = str(Path(__file__).resolve().parent / (title_to_filename(title) + ".docx"))

    print("Building DOCX...")
    doc, n_inserted = build_docx(title, author, url, items, cookies)
    make_all_black(doc)
    doc.save(output_path)

    size_kb = Path(output_path).stat().st_size // 1024
    print(f"Saved: {output_path} ({size_kb} KB)")
    return title, output_path, n_inserted


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    url = sys.argv[1]
    output_path = None

    args = sys.argv[2:]
    for i, arg in enumerate(args):
        if arg == "--output" and i + 1 < len(args):
            output_path = args[i + 1]

    title, saved_path, n_images = fetch_and_convert(url, output_path)
    print(f"\nDone!")
    print(f"Title   : {title}")
    print(f"Images  : {n_images}")
    print(f"Output  : {saved_path}")


if __name__ == "__main__":
    main()
