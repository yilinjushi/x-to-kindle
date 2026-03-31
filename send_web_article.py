"""
send_web_article.py — Fetch a shared web article, convert text content to DOCX, and email it to Kindle.

Usage:
    python send_web_article.py --url https://example.com/article
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from readability import Document as ReadabilityDocument

from app_config import (
    GMAIL_APP_PASSWORD,
    GMAIL_USER,
    KINDLE_EMAIL,
    OUTDIR,
    PYTHON_EXE,
    SENT_WEB_HISTORY_FILE,
    ensure_parent_dir,
    load_json_file,
)
from tweet_to_docx import make_all_black, title_to_filename


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/132.0.0.0 Safari/537.36"
)
TRACKING_QUERY_PREFIXES = ("utm_", "fbclid", "gclid", "igshid", "mc_", "ref")
SEND_EMAIL_SCRIPT = Path(__file__).resolve().parent / "send_email.py"
WEB_OUTDIR = OUTDIR / "web"


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not any(key.lower().startswith(prefix) for prefix in TRACKING_QUERY_PREFIXES)
    ]
    cleaned = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower(),
        fragment="",
        query=urlencode(query, doseq=True),
    )
    normalized = urlunparse(cleaned)
    return normalized[:-1] if normalized.endswith("/") else normalized


def load_sent_history() -> dict[str, dict]:
    history = load_json_file(SENT_WEB_HISTORY_FILE, [])
    return {
        item["url"]: item
        for item in history
        if isinstance(item, dict) and item.get("url")
    }


def save_sent_history(history: dict[str, dict]) -> None:
    ensure_parent_dir(SENT_WEB_HISTORY_FILE)
    with open(SENT_WEB_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(history.values()), f, ensure_ascii=False, indent=2)


def fetch_html(url: str) -> str:
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    response.raise_for_status()
    response.encoding = response.encoding or response.apparent_encoding
    return response.text


def extract_article(html: str, fallback_title: str | None = None) -> tuple[str, list[str]]:
    readable = ReadabilityDocument(html)
    content_html = readable.summary(html_partial=True)
    title = readable.short_title() or fallback_title or "article"

    soup = BeautifulSoup(content_html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    paragraphs = []
    for node in soup.find_all(["p", "h1", "h2", "h3", "blockquote", "li"]):
        text = re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip()
        if text and len(text) >= 20:
            paragraphs.append(text)

    if not paragraphs:
        fallback_soup = BeautifulSoup(html, "html.parser")
        text = fallback_soup.get_text("\n", strip=True)
        paragraphs = [
            re.sub(r"\s+", " ", line).strip()
            for line in text.splitlines()
            if len(re.sub(r"\s+", " ", line).strip()) >= 40
        ]

    return title.strip(), paragraphs


def build_docx(title: str, url: str, paragraphs: list[str], output_path: Path) -> None:
    doc = Document()

    heading = doc.add_heading(title or "(no title)", level=1)
    heading.alignment = WD_ALIGN_PARAGRAPH.LEFT

    meta = doc.add_paragraph()
    meta.add_run(url).font.size = Pt(9)
    doc.add_paragraph()

    for paragraph in paragraphs:
        p = doc.add_paragraph(paragraph)
        p.paragraph_format.space_after = Pt(6)

    make_all_black(doc)
    doc.save(output_path)


def send_docx(filepath: Path, title: str, send_to: str) -> bool:
    python_exe = PYTHON_EXE or sys.executable
    subject = title[:60] if title else filepath.stem
    result = subprocess.run(
        [
            python_exe,
            str(SEND_EMAIL_SCRIPT),
            "--to",
            send_to,
            "--subject",
            subject,
            "--attach",
            str(filepath),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode == 0:
        print(f"Sent: {subject!r} → {send_to}")
        return True

    print(f"Email error: {result.stderr.strip()}", file=sys.stderr)
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a shared web article to Kindle")
    parser.add_argument("--url", required=True, help="Web article URL")
    parser.add_argument("--title", default="", help="Optional title override from Shortcut")
    parser.add_argument("--source", default="manual", help="Optional source label")
    args = parser.parse_args()

    if not KINDLE_EMAIL:
        print("ERROR: KINDLE_EMAIL is required.", file=sys.stderr)
        sys.exit(1)
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        print("ERROR: GMAIL_USER and GMAIL_APP_PASSWORD are required.", file=sys.stderr)
        sys.exit(1)

    normalized_url = normalize_url(args.url)
    history = load_sent_history()
    if normalized_url in history:
        print("SKIP: this web article was already sent before.")
        return

    html = fetch_html(args.url)
    title, paragraphs = extract_article(html, args.title or None)
    if not paragraphs:
        print("ERROR: Could not extract article text.", file=sys.stderr)
        sys.exit(1)

    WEB_OUTDIR.mkdir(parents=True, exist_ok=True)
    url_digest = hashlib.sha1(normalized_url.encode("utf-8")).hexdigest()[:10]
    filename = f"{title_to_filename(title)}-{url_digest}.docx"
    output_path = WEB_OUTDIR / filename
    build_docx(title, normalized_url, paragraphs, output_path)

    total_chars = sum(len(p) for p in paragraphs)
    print(f"Prepared {len(paragraphs)} paragraph(s), {total_chars} chars")

    if send_docx(output_path, title, KINDLE_EMAIL):
        history[normalized_url] = {
            "url": normalized_url,
            "title": title,
            "source": args.source,
            "chars": total_chars,
        }
        save_sent_history(history)
        print(f"History updated: {SENT_WEB_HISTORY_FILE}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
