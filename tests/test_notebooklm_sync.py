import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import notebooklm_sync as sync

CATEGORIES = {"agent-engineering": "Agent 工程方法论", "musings": "杂谈与思考"}


def write_article(root: Path, name: str, *, url: str, title: str, date: str, body: str, category: str | None) -> None:
    lines = ["---", f'url: "{url}"', f'title: "{title}"', f"date: {date}"]
    if category:
        lines.append(f'category: "{category}"')
    lines.append("---")
    (root / f"{name}.md").write_text("\n".join(lines) + f"\n\n# {title}\n\n{body}\n", encoding="utf-8")


class FakeClient:
    def __init__(self, source_limit=50):
        self.notebooks_data: dict[str, list[str]] = {}
        self.calls: list[tuple] = []
        self._next = 0
        self.notebooks = SimpleNamespace(list=self._list_notebooks, create=self._create_notebook)
        self.sources = SimpleNamespace(list=self._list_sources, add_text=self._add_text, delete=self._delete)
        self.settings = SimpleNamespace(get_account_limits=self._limits)
        self.source_limit = source_limit

    def _id(self, prefix):
        self._next += 1
        return f"{prefix}{self._next}"

    async def _limits(self):
        return SimpleNamespace(source_limit=self.source_limit)

    async def _list_notebooks(self):
        return [SimpleNamespace(id=notebook_id) for notebook_id in self.notebooks_data]

    async def _create_notebook(self, title):
        notebook_id = self._id("nb")
        self.notebooks_data[notebook_id] = []
        self.calls.append(("create", title))
        return SimpleNamespace(id=notebook_id, title=title)

    async def _list_sources(self, notebook_id):
        return [SimpleNamespace(id=source_id) for source_id in self.notebooks_data[notebook_id]]

    async def _add_text(self, notebook_id, title, content, wait=False, wait_timeout=0):
        source_id = self._id("src")
        self.notebooks_data[notebook_id].append(source_id)
        self.calls.append(("add", notebook_id, title))
        return SimpleNamespace(id=source_id)

    async def _delete(self, notebook_id, source_id):
        self.notebooks_data[notebook_id].remove(source_id)
        self.calls.append(("delete", notebook_id, source_id))


class NotebookLMSyncTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.archive = self.root / "archive"
        self.archive.mkdir()
        self.state_path = self.root / "state" / "notebooklm.json"
        patcher = patch("builtins.print")
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_apply(self, client, sources, max_uploads=20):
        state = sync.load_state(self.state_path)
        failures = asyncio.run(sync.apply(client, sources, state, CATEGORIES, self.state_path, max_uploads))
        return failures, json.loads(self.state_path.read_text(encoding="utf-8"))

    def test_build_sources_skips_uncategorized_empty_unknown_and_duplicates(self):
        write_article(self.archive, "a", url="u1", title="A", date="2026-09-07", body="alpha", category="agent-engineering")
        write_article(self.archive, "b", url="u1", title="A copy", date="2026-09-08", body="other", category="agent-engineering")
        write_article(self.archive, "c", url="u3", title="C", date="2026-09-09", body="alpha", category="musings")
        write_article(self.archive, "d", url="u4", title="D", date="2026-09-09", body="delta", category=None)
        write_article(self.archive, "e", url="u5", title="E", date="2026-09-09", body="![Article image](/assets/x/01.jpg)", category="musings")
        write_article(self.archive, "f", url="u6", title="F", date="2026-10-01", body="fox", category="nope")
        write_article(self.archive, "g", url="u7", title="G", date="2026-10-02", body="golf", category="agent-engineering")

        sources, skipped = sync.build_sources(self.archive, CATEGORIES)

        self.assertEqual(skipped, {"empty": 1, "uncategorized": 1, "unknown_category": 1, "duplicate": 2})
        self.assertEqual([source["key"] for source in sources], ["agent-engineering|2026-09", "agent-engineering|2026-10"])
        self.assertEqual(sources[0]["title"], "Agent 工程方法论 · 2026-09")
        self.assertIn("原文：u1", sources[0]["content"])
        self.assertNotIn("# A\n\nalpha", sources[0]["content"])

    def test_render_splits_large_groups_on_article_boundaries(self):
        articles = [
            {"id": f"id{i}", "title": f"T{i}", "date": "2026-09-01", "url": f"u{i}", "text": "x" * 200}
            for i in range(3)
        ]
        with patch.object(sync, "MAX_SOURCE_CHARS", 500):
            rendered = sync.render("musings", "杂谈与思考", "2026-09", articles)
        self.assertEqual([source["key"] for source in rendered], ["musings|2026-09", "musings|2026-09|2"])
        self.assertEqual(rendered[1]["title"], "杂谈与思考 · 2026-09 (2)")
        self.assertEqual(sum(len(source["article_ids"]) for source in rendered), 3)

    def test_plan_detects_new_changed_and_removed_sources(self):
        sources = [{"key": "a|1", "digest": "same"}, {"key": "b|1", "digest": "new"}, {"key": "c|1", "digest": "x"}]
        state = {"sources": {"a|1": {"digest": "same"}, "b|1": {"digest": "old"}, "z|1": {"digest": "gone"}}}
        upserts, removals = sync.plan(sources, state)
        self.assertEqual([source["key"] for source in upserts], ["b|1", "c|1"])
        self.assertEqual(removals, ["z|1"])

    def test_apply_creates_notebooks_replaces_changed_sources_and_is_idempotent(self):
        write_article(self.archive, "a", url="u1", title="A", date="2026-09-07", body="alpha", category="agent-engineering")
        client = FakeClient()
        sources, _ = sync.build_sources(self.archive, CATEGORIES)
        failures, state = self.run_apply(client, sources)
        self.assertEqual(failures, 0)
        self.assertEqual(client.calls[0], ("create", "Agent 工程方法论"))
        first_source = state["sources"]["agent-engineering|2026-09"]["source_id"]

        client.calls.clear()
        self.run_apply(client, sources)
        self.assertEqual(client.calls, [])

        write_article(self.archive, "b", url="u2", title="B", date="2026-09-08", body="beta", category="agent-engineering")
        sources, _ = sync.build_sources(self.archive, CATEGORIES)
        _, state = self.run_apply(client, sources)
        self.assertEqual([call[0] for call in client.calls], ["add", "delete"])
        self.assertEqual(client.calls[1][2], first_source)
        self.assertEqual(state["sources"]["agent-engineering|2026-09"]["article_ids"], ["a", "b"])

    def test_apply_rolls_over_to_new_notebook_and_deletes_first_when_full(self):
        for month in ("09", "10"):
            write_article(self.archive, f"a{month}", url=f"u{month}", title=f"A{month}", date=f"2026-{month}-01", body=f"body {month}", category="musings")
        client = FakeClient(source_limit=1)
        sources, _ = sync.build_sources(self.archive, CATEGORIES)
        _, state = self.run_apply(client, sources)
        self.assertEqual([title for kind, title in [c for c in client.calls if c[0] == "create"]], ["杂谈与思考", "杂谈与思考 · 2"])
        self.assertEqual(len(state["notebooks"]["musings"]), 2)

        write_article(self.archive, "b09", url="u9b", title="B", date="2026-09-02", body="more", category="musings")
        sources, _ = sync.build_sources(self.archive, CATEGORIES)
        client.calls.clear()
        self.run_apply(client, sources)
        self.assertEqual([call[0] for call in client.calls], ["delete", "add"])

    def test_apply_reuploads_sources_deleted_in_web_ui_and_respects_upload_cap(self):
        write_article(self.archive, "a", url="u1", title="A", date="2026-09-07", body="alpha", category="agent-engineering")
        write_article(self.archive, "b", url="u2", title="B", date="2026-09-07", body="beta", category="musings")
        client = FakeClient()
        sources, _ = sync.build_sources(self.archive, CATEGORIES)
        _, state = self.run_apply(client, sources, max_uploads=1)
        self.assertEqual(len(state["sources"]), 1)
        _, state = self.run_apply(client, sources, max_uploads=1)
        self.assertEqual(len(state["sources"]), 2)

        entry = state["sources"]["musings|2026-09"]
        client.notebooks_data[entry["notebook_id"]].remove(entry["source_id"])
        client.calls.clear()
        _, state = self.run_apply(client, sources)
        self.assertEqual([call[0] for call in client.calls], ["add"])
        self.assertIn("musings|2026-09", state["sources"])

    def test_apply_removes_sources_for_groups_that_no_longer_exist(self):
        write_article(self.archive, "a", url="u1", title="A", date="2026-09-07", body="alpha", category="agent-engineering")
        client = FakeClient()
        sources, _ = sync.build_sources(self.archive, CATEGORIES)
        self.run_apply(client, sources)
        client.calls.clear()
        _, state = self.run_apply(client, [])
        self.assertEqual([call[0] for call in client.calls], ["delete"])
        self.assertEqual(state["sources"], {})


if __name__ == "__main__":
    unittest.main()
