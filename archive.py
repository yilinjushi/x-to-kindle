"""
archive.py — Persist the full text of a fetched article as a Markdown file.

This is the long-term storage layer: every article whose text we extract gets
saved here, independent of whether the Kindle email succeeds, so the full
text is always available for later reading or analysis.
"""

import hashlib
import re
from datetime import date, datetime, timezone
from pathlib import Path

from app_config import ARCHIVE_DIR
from tweet_to_docx import title_to_filename


def _slug(title: str) -> str:
    safe = title_to_filename(title, max_len=60)
    return re.sub(r"\s+", "-", safe).strip("-").lower() or "article"


def _yaml_escape(value: str) -> str:
    return value.replace('"', '\\"')


def save_article_archive(
    url: str,
    title: str,
    text: str,
    author: str = "",
    source: str = "",
    chars: int | None = None,
    n_images: int = 0,
    saved_at: date | None = None,
) -> Path:
    """Save the full extracted text of an article as a Markdown file.

    Returns the path of the saved file.
    """
    saved_at = saved_at or datetime.now(timezone.utc).date()
    url_digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    slug = _slug(title)

    year_dir = ARCHIVE_DIR / str(saved_at.year)
    year_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{saved_at.isoformat()}-{slug}-{url_digest}.md"
    filepath = year_dir / filename

    chars = chars if chars is not None else len(text)

    frontmatter_lines = [
        "---",
        f'url: "{_yaml_escape(url)}"',
        f'title: "{_yaml_escape(title)}"',
    ]
    if author:
        frontmatter_lines.append(f'author: "{_yaml_escape(author)}"')
    if source:
        frontmatter_lines.append(f'source: "{_yaml_escape(source)}"')
    frontmatter_lines.append(f"date: {saved_at.isoformat()}")
    frontmatter_lines.append(f"chars: {chars}")
    if n_images:
        frontmatter_lines.append(f"images: {n_images}")
    frontmatter_lines.append("---")

    content = "\n".join(frontmatter_lines) + f"\n\n# {title or '(no title)'}\n\n{text}\n"
    filepath.write_text(content, encoding="utf-8")
    return filepath
