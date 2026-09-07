"""Build a framework-free static blog from archived Markdown articles."""

import html
import re
from pathlib import Path

import markdown

from app_config import ARCHIVE_DIR, SITE_DIR


def _read_article(path: Path) -> dict[str, str]:
    raw = path.read_text(encoding="utf-8")
    metadata: dict[str, str] = {}
    body = raw
    if raw.startswith("---\n"):
        _, frontmatter, body = raw.split("---", 2)
        for line in frontmatter.strip().splitlines():
            key, separator, value = line.partition(":")
            if separator:
                metadata[key.strip()] = value.strip().strip('"').replace('\\"', '"')
    metadata["body"] = body.strip()
    metadata["id"] = path.stem
    return metadata


def _page(title: str, content: str, description: str = "") -> str:
    safe_title = html.escape(title)
    safe_description = html.escape(description or title, quote=True)
    return f"""<!doctype html>
<html lang="zh-Hant"><head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{safe_description}">
  <title>{safe_title} · Reading Archive</title><link rel="stylesheet" href="/style.css">
</head><body>
  <header class="masthead"><a href="/">Reading Archive</a></header><main>{content}</main>
  <footer>Saved for thoughtful reading.</footer>
</body></html>
"""


def build_site(archive_dir: Path = ARCHIVE_DIR, site_dir: Path = SITE_DIR) -> None:
    site_dir.mkdir(parents=True, exist_ok=True)
    articles = [_read_article(path) for path in archive_dir.glob("**/*.md")]
    articles.sort(key=lambda item: (item.get("date", ""), item["id"]), reverse=True)
    for article in articles:
        article_dir = site_dir / "articles" / article["id"]
        article_dir.mkdir(parents=True, exist_ok=True)
        # Extracted web text is untrusted; escape raw HTML while retaining Markdown syntax.
        rendered = markdown.markdown(html.escape(article["body"]), extensions=["extra", "sane_lists"], output_format="html5")
        source = article.get("url", "")
        byline = " · ".join(filter(None, [article.get("author", ""), article.get("date", "")]))
        source_link = f'<a class="source" href="{html.escape(source, quote=True)}" rel="noopener noreferrer">查看原文 ↗</a>' if source else ""
        content = f'<article><a class="back" href="/">← 返回文章列表</a><div class="meta">{html.escape(byline)}</div><div class="prose">{rendered}</div>{source_link}</article>'
        (article_dir / "index.html").write_text(_page(article.get("title", "Article"), content, article.get("title", "")), encoding="utf-8")
    cards = []
    for article in articles:
        body_text = re.sub(r"[#>*_`\[\]()]", " ", article["body"])
        excerpt = re.sub(r"\s+", " ", body_text).strip()[:180]
        cards.append(f'<li><a href="/articles/{html.escape(article["id"])}/"><time>{html.escape(article.get("date", ""))}</time><h2>{html.escape(article.get("title", "Untitled"))}</h2><p>{html.escape(excerpt)}{"…" if len(body_text) > 180 else ""}</p></a></li>')
    listing = f'<ul class="articles">{"".join(cards)}</ul>' if cards else '<p class="empty">文章归档尚未开始。</p>'
    home = f'<section class="intro"><p class="eyebrow">PERSONAL READING LOG</p><h1>值得留下的文章。</h1><p>一个安静、可持续的阅读归档。</p></section>{listing}'
    (site_dir / "index.html").write_text(_page("Reading Archive", home), encoding="utf-8")


if __name__ == "__main__":
    build_site()
