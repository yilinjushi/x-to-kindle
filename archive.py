"""Persist article text and images, then rebuild the static reading archive."""

import hashlib
import mimetypes
import re
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

from app_config import ARCHIVE_DIR, SITE_DIR, USER_AGENT
from tweet_to_docx import title_to_filename


def _slug(title: str) -> str:
    safe = title_to_filename(title, max_len=60)
    return re.sub(r"\s+", "-", safe).strip("-").lower() or "article"


def _yaml_escape(value: str) -> str:
    return value.replace('"', '\\"')


def _image_extension(url: str, content_type: str) -> str:
    extension = Path(urlparse(url).path).suffix.lower()
    if extension in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        return ".jpg" if extension == ".jpeg" else extension
    guessed = mimetypes.guess_extension(content_type.split(";", 1)[0].strip())
    return ".jpg" if guessed == ".jpe" else (guessed or ".jpg")


def _save_images(article_id: str, urls: list[str], cookies: dict) -> dict[str, str]:
    saved: dict[str, str] = {}
    asset_dir = SITE_DIR / "assets" / article_id
    for index, image_url in enumerate(dict.fromkeys(urls), 1):
        try:
            response = requests.get(
                image_url,
                headers={"User-Agent": USER_AGENT, "Referer": "https://x.com/"},
                cookies=cookies,
                timeout=30,
            )
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if not content_type.lower().startswith("image/"):
                raise requests.RequestException(f"unexpected content type: {content_type or 'unknown'}")
            if len(response.content) > 20 * 1024 * 1024:
                raise requests.RequestException("image exceeds the 20 MiB archive limit")
            extension = _image_extension(image_url, content_type)
            asset_dir.mkdir(parents=True, exist_ok=True)
            filename = f"{index:02d}{extension}"
            (asset_dir / filename).write_bytes(response.content)
            saved[image_url] = f"/assets/{article_id}/{filename}"
        except requests.RequestException as exc:
            # Archiving must never break the established Kindle delivery path.
            print(f"  Archive image unavailable: {image_url} ({exc})")
    return saved


def _markdown_body(fallback_text: str, items: list[dict] | None, image_urls: list[str], saved_images: dict[str, str]) -> str:
    if not items:
        parts = [fallback_text]
        parts.extend(f"![Article image]({saved_images[url]})" for url in image_urls if url in saved_images)
        return "\n\n".join(part for part in parts if part)
    parts: list[str] = []
    for item in items:
        item_type = item.get("type", "para")
        if item_type == "image":
            if item.get("src") in saved_images:
                parts.append(f"![Article image]({saved_images[item['src']]})")
            continue
        value = item.get("text", "").strip()
        if not value:
            continue
        if item_type in {"h1", "h2", "h3"}:
            parts.append(f"{'#' * int(item_type[1])} {value}")
        elif item_type == "li":
            parts.append(f"- {value}")
        elif item_type == "blockquote":
            parts.append("\n".join(f"> {line}" for line in value.splitlines()))
        else:
            parts.append(value)
    return "\n\n".join(parts) or fallback_text


def save_article_archive(
    url: str,
    title: str,
    text: str,
    author: str = "",
    source: str = "",
    chars: int | None = None,
    n_images: int = 0,
    saved_at: date | None = None,
    image_urls: list[str] | None = None,
    items: list[dict] | None = None,
    cookies: dict | None = None,
) -> Path:
    """Save an article and rebuild the public site without affecting delivery."""
    saved_at = saved_at or datetime.now(timezone.utc).date()
    url_digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    slug = _slug(title)
    article_id = f"{saved_at.isoformat()}-{slug}-{url_digest}"
    year_dir = ARCHIVE_DIR / str(saved_at.year)
    year_dir.mkdir(parents=True, exist_ok=True)
    filepath = year_dir / f"{article_id}.md"
    requested_images = image_urls or [item["src"] for item in (items or []) if item.get("type") == "image" and item.get("src")]
    saved_images = _save_images(article_id, requested_images, cookies or {})
    chars = chars if chars is not None else len(text)
    frontmatter = ["---", f'url: "{_yaml_escape(url)}"', f'title: "{_yaml_escape(title)}"']
    if author:
        frontmatter.append(f'author: "{_yaml_escape(author)}"')
    if source:
        frontmatter.append(f'source: "{_yaml_escape(source)}"')
    frontmatter.extend([f"date: {saved_at.isoformat()}", f"chars: {chars}", f"images: {len(saved_images)}", "---"])
    body = _markdown_body(text, items, requested_images, saved_images)
    filepath.write_text("\n".join(frontmatter) + f"\n\n# {title or '(no title)'}\n\n{body}\n", encoding="utf-8")
    from build_site import build_site
    build_site(ARCHIVE_DIR, SITE_DIR)
    return filepath
