"""Mirror categorized archive articles into NotebookLM, one text source per category and month."""

import argparse
import asyncio
import hashlib
import json
import os
import re
import sys
from pathlib import Path

from build_site import _read_article

MAX_SOURCE_CHARS = 300_000
DEFAULT_SOURCE_LIMIT = 50
ADD_TIMEOUT = 300.0
_IMAGE_LINE = re.compile(r"^!\[[^\]]*\]\([^)]*\)\s*$", re.MULTILINE)


def load_categories(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {item["slug"]: item["name"] for item in data["categories"]}


def _clean_body(article: dict) -> str:
    body = article["body"]
    heading = f"# {article.get('title', '')}".strip()
    if body.startswith(heading):
        body = body[len(heading):]
    body = _IMAGE_LINE.sub("", body)
    return re.sub(r"\n{3,}", "\n\n", body).strip()


def load_articles(archive_dir: Path, categories: dict[str, str]) -> tuple[list[dict], dict[str, int]]:
    """Return syncable articles plus counts of skipped ones."""
    articles, skipped = [], {"empty": 0, "uncategorized": 0, "unknown_category": 0}
    for path in sorted(Path(archive_dir).glob("**/*.md")):
        article = _read_article(path)
        article["text"] = _clean_body(article)
        category = article.get("category", "")
        if not article["text"]:
            skipped["empty"] += 1
        elif not category:
            skipped["uncategorized"] += 1
        elif category not in categories:
            skipped["unknown_category"] += 1
            print(f"  WARN: unknown category {category!r} in {path.name}")
        else:
            articles.append(article)
    return articles, skipped


def dedupe(articles: list[dict]) -> list[dict]:
    """Drop repeated URLs and identical bodies, keeping the earliest copy."""
    seen_urls, seen_bodies, kept = set(), set(), []
    for article in sorted(articles, key=lambda item: (item.get("date", ""), item["id"])):
        body_key = hashlib.sha256(re.sub(r"\s+", " ", article["text"]).strip().encode("utf-8")).hexdigest()
        url = article.get("url", "")
        if (url and url in seen_urls) or body_key in seen_bodies:
            continue
        seen_urls.add(url)
        seen_bodies.add(body_key)
        kept.append(article)
    return kept


def group(articles: list[dict]) -> dict[tuple[str, str], list[dict]]:
    groups: dict[tuple[str, str], list[dict]] = {}
    for article in sorted(articles, key=lambda item: (item.get("date", ""), item["id"])):
        groups.setdefault((article["category"], article.get("date", "")[:7] or "undated"), []).append(article)
    return groups


def _article_block(article: dict) -> str:
    return (
        f"## {article.get('title', 'Untitled')}\n"
        f"作者：{article.get('author', '')}  日期：{article.get('date', '')}\n"
        f"原文：{article.get('url', '')}\n\n{article['text']}\n\n---\n"
    )


def render(slug: str, name: str, month: str, articles: list[dict]) -> list[dict]:
    """Render one group into one or more sources split on article boundaries."""
    parts: list[list[dict]] = [[]]
    size = 0
    for article in articles:
        block_size = len(_article_block(article))
        if parts[-1] and size + block_size > MAX_SOURCE_CHARS:
            parts.append([])
            size = 0
        parts[-1].append(article)
        size += block_size
    rendered = []
    for index, part in enumerate(parts, 1):
        suffix = f" ({index})" if index > 1 else ""
        title = f"{name} · {month}{suffix}"
        header = f"# {title}\n\n收藏文章合集，共 {len(part)} 篇。\n\n"
        content = header + "\n".join(_article_block(article) for article in part)
        rendered.append({
            "key": f"{slug}|{month}" + (f"|{index}" if index > 1 else ""),
            "slug": slug,
            "title": title,
            "content": content,
            "digest": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "article_ids": [article["id"] for article in part],
        })
    return rendered


def build_sources(archive_dir: Path, categories: dict[str, str]) -> tuple[list[dict], dict[str, int]]:
    articles, skipped = load_articles(archive_dir, categories)
    kept = dedupe(articles)
    skipped["duplicate"] = len(articles) - len(kept)
    sources = []
    for (slug, month), members in sorted(group(kept).items()):
        sources.extend(render(slug, categories[slug], month, members))
    return sources, skipped


def plan(sources: list[dict], state: dict) -> tuple[list[dict], list[str]]:
    """Return sources to upload and state keys whose sources should be removed."""
    known = state.get("sources", {})
    upserts = [source for source in sources if known.get(source["key"], {}).get("digest") != source["digest"]]
    wanted = {source["key"] for source in sources}
    removals = sorted(key for key in known if key not in wanted)
    return upserts, removals


def load_state(path: Path) -> dict:
    state = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    state.setdefault("version", 1)
    state.setdefault("notebooks", {})
    state.setdefault("sources", {})
    return state


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


async def _prune_state(client, state: dict) -> dict[str, int]:
    """Forget notebooks and sources deleted in the web UI so they are re-uploaded."""
    live_notebooks = {notebook.id for notebook in await client.notebooks.list()}
    counts: dict[str, int] = {}
    for slug, notebooks in state["notebooks"].items():
        state["notebooks"][slug] = [notebook for notebook in notebooks if notebook["id"] in live_notebooks]
    for notebooks in state["notebooks"].values():
        for notebook in notebooks:
            live_sources = {source.id for source in await client.sources.list(notebook["id"])}
            counts[notebook["id"]] = len(live_sources)
            for key, entry in list(state["sources"].items()):
                if entry["notebook_id"] == notebook["id"] and entry["source_id"] not in live_sources:
                    del state["sources"][key]
    tracked = set(counts)
    for key, entry in list(state["sources"].items()):
        if entry["notebook_id"] not in tracked:
            del state["sources"][key]
    return counts


async def _target_notebook(client, state: dict, counts: dict[str, int], slug: str, name: str, limit: int) -> str:
    notebooks = state["notebooks"].setdefault(slug, [])
    if notebooks and counts.get(notebooks[-1]["id"], 0) < limit:
        return notebooks[-1]["id"]
    title = name if not notebooks else f"{name} · {len(notebooks) + 1}"
    notebook = await client.notebooks.create(title)
    notebooks.append({"id": notebook.id, "title": title})
    counts[notebook.id] = 0
    print(f"  Created notebook: {title}")
    return notebook.id


async def apply(client, sources: list[dict], state: dict, categories: dict[str, str], state_path: Path, max_uploads: int) -> int:
    """Upload changed sources and delete stale ones; returns the failure count."""
    counts = await _prune_state(client, state)
    save_state(state_path, state)
    try:
        limit = (await client.settings.get_account_limits()).source_limit or DEFAULT_SOURCE_LIMIT
    except Exception as exc:
        print(f"  Account limits unavailable ({exc}); assuming {DEFAULT_SOURCE_LIMIT} sources per notebook.")
        limit = DEFAULT_SOURCE_LIMIT
    upserts, removals = plan(sources, state)
    print(f"Plan: {len(upserts)} upload(s), {len(removals)} removal(s); source limit {limit}.")
    failures = 0

    for key in removals:
        entry = state["sources"][key]
        try:
            await client.sources.delete(entry["notebook_id"], entry["source_id"])
            counts[entry["notebook_id"]] = counts.get(entry["notebook_id"], 1) - 1
            del state["sources"][key]
            save_state(state_path, state)
            print(f"  Removed: {entry['title']}")
        except Exception as exc:
            failures += 1
            print(f"  ERROR removing {entry['title']}: {exc}", file=sys.stderr)

    for done, source in enumerate(upserts):
        if done >= max_uploads:
            print(f"  Upload cap reached; {len(upserts) - done} source(s) left for the next run.")
            break
        old = state["sources"].get(source["key"])
        try:
            if old:
                notebook_id = old["notebook_id"]
                if counts.get(notebook_id, limit) >= limit:
                    # A full notebook has no slot for add-then-delete, so free the old slot first.
                    await client.sources.delete(notebook_id, old["source_id"])
                    counts[notebook_id] -= 1
                    del state["sources"][source["key"]]
                    save_state(state_path, state)
                    old = None
            else:
                notebook_id = await _target_notebook(client, state, counts, source["slug"], categories[source["slug"]], limit)
            added = await client.sources.add_text(notebook_id, source["title"], source["content"], wait=True, wait_timeout=ADD_TIMEOUT)
            counts[notebook_id] = counts.get(notebook_id, 0) + 1
            if old:
                await client.sources.delete(old["notebook_id"], old["source_id"])
                counts[old["notebook_id"]] -= 1
            state["sources"][source["key"]] = {
                "notebook_id": notebook_id,
                "source_id": added.id,
                "title": source["title"],
                "digest": source["digest"],
                "article_ids": source["article_ids"],
            }
            save_state(state_path, state)
            print(f"  Uploaded: {source['title']} ({len(source['article_ids'])} article(s))")
        except Exception as exc:
            failures += 1
            print(f"  ERROR uploading {source['title']}: {exc}", file=sys.stderr)
    return failures


async def _run(args: argparse.Namespace, sources: list[dict], categories: dict[str, str]) -> int:
    from notebooklm import NotebookLMClient

    state_path = Path(args.state)
    state = load_state(state_path)
    async with NotebookLMClient.from_storage() as client:
        return await apply(client, sources, state, categories, state_path, args.max_uploads)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-dir", required=True)
    parser.add_argument("--categories", required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--dry-run", action="store_true", help="print the plan without signing in")
    parser.add_argument("--max-uploads", type=int, default=20)
    args = parser.parse_args()

    categories = load_categories(Path(args.categories))
    sources, skipped = build_sources(Path(args.archive_dir), categories)
    print(
        f"Articles: {sum(len(source['article_ids']) for source in sources)} syncable in {len(sources)} source(s); "
        f"uncategorized {skipped['uncategorized']}, empty {skipped['empty']}, "
        f"duplicate {skipped['duplicate']}, unknown category {skipped['unknown_category']}."
    )
    if args.dry_run:
        upserts, removals = plan(sources, load_state(Path(args.state)))
        for source in upserts:
            print(f"  would upload: {source['title']} ({len(source['article_ids'])} article(s), {len(source['content'])} chars)")
        for key in removals:
            print(f"  would remove: {key}")
        return
    failures = asyncio.run(_run(args, sources, categories))
    if failures:
        print(f"Failed: {failures} action(s); rerun to retry.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
