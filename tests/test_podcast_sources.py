import json
import os
import sys
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import MagicMock, patch

import fetch_bookmarks
import podcast_sources
from podcast_sources import enqueue_source


class PodcastSourceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.state = self.root / "queue.json"
        self.env = patch.dict(os.environ, {"PODCAST_SOURCE_DIR": str(self.root / "sources"), "PODCAST_STATE_FILE": str(self.state)})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.url = "https://x.com/writer/status/123"
        self.content = {"title": "Title", "author": "Writer", "is_article": True,
                        "items": [{"type": "para", "text": "Complete body with a 2026 date."}, {"type": "image", "src": "https://example.com/image.png"}]}

    def enqueue(self):
        return enqueue_source(url=self.url, **{key: self.content[key] for key in ("title", "author", "items")})

    def test_full_snapshot_and_versioned_deduplication(self):
        first = self.enqueue()
        snapshot_path = self.state.parent / first["source_path"]
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        self.assertEqual(snapshot["items"], self.content["items"])
        self.assertEqual(snapshot["metadata"]["author"], "Writer")
        self.assertEqual(snapshot["text"], self.content["items"][0]["text"])
        self.assertNotIn("Writer", snapshot_path.with_suffix(".md").read_text())
        self.assertFalse(self.enqueue()["enqueued"])
        self.content["title"] = "Changed title"
        self.assertTrue(self.enqueue()["enqueued"])
        self.assertEqual(len(json.loads(self.state.read_text())["tasks"]), 2)

    def test_retired_task_stays_retired_and_unknown_status_fails_closed(self):
        task = self.enqueue()
        queue = json.loads(self.state.read_text())
        queue["tasks"][task["id"]]["status"] = "retired"
        self.state.write_text(json.dumps(queue))
        self.assertEqual(self.enqueue()["status"], "retired")
        queue["tasks"][task["id"]]["status"] = "surprise"
        self.state.write_text(json.dumps(queue))
        with self.assertRaises(ValueError):
            self.enqueue()

    def test_rejects_unsafe_identity_and_empty_text(self):
        with self.assertRaises(ValueError):
            enqueue_source(url="https://x.com/u/status/../../escape", title="x", author="", items=[])
        with self.assertRaises(ValueError):
            enqueue_source(url=self.url, title="x", author="", items=[])
        self.assertFalse(self.state.exists())

    def test_failed_atomic_queue_commit_leaves_prior_queue_and_retries(self):
        self.enqueue()
        original = self.state.read_bytes()
        self.content["title"] = "Second revision"
        real_replace = os.replace

        def fail_queue_replace(source, destination):
            if Path(destination) == self.state:
                raise OSError("simulated commit failure")
            return real_replace(source, destination)

        with patch.object(podcast_sources.os, "replace", side_effect=fail_queue_replace):
            with self.assertRaises(OSError):
                self.enqueue()
        self.assertEqual(self.state.read_bytes(), original)
        self.assertEqual(list(self.root.rglob(".pending-*")), [])
        self.assertTrue(self.enqueue()["enqueued"])
        self.assertEqual(len(json.loads(self.state.read_text())["tasks"]), 2)

    def run_fetch(self, flags, sent=False, snapshot_error=False):
        session = self.root / "session.json"
        session.write_text("{}")
        manager = MagicMock()
        browser = manager.__enter__.return_value.chromium.launch.return_value
        browser.new_context.return_value.cookies.return_value = []
        with ExitStack() as stack:
            for name, value in {"SESSION_FILE": session, "OUTDIR": self.root / "out",
                                "KINDLE_EMAIL": "test@example.com"}.items():
                stack.enter_context(patch.object(fetch_bookmarks, name, value))
            for name, value in {"sync_playwright": manager, "get_bookmark_urls": [self.url],
                                "extract_content_from_page": self.content,
                                "load_sent_history": {self.url: {"url": self.url}} if sent else {}}.items():
                stack.enter_context(patch.object(fetch_bookmarks, name, return_value=value))
            stack.enter_context(patch.object(fetch_bookmarks, "wait_for_content"))
            stack.enter_context(patch.object(sys, "argv", ["fetch_bookmarks.py", *flags]))
            archive = stack.enter_context(patch.object(fetch_bookmarks, "save_article_archive"))
            send = stack.enter_context(patch.object(fetch_bookmarks, "send_article", return_value=True))
            stack.enter_context(patch.object(fetch_bookmarks, "save_sent_history"))
            doc = MagicMock()
            doc.save.side_effect = lambda path: Path(path).write_bytes(b"docx-test")
            build = stack.enter_context(patch.object(fetch_bookmarks, "build_docx", return_value=(doc, 0)))
            stack.enter_context(patch.object(fetch_bookmarks, "make_all_black"))
            if snapshot_error:
                stack.enter_context(patch.object(fetch_bookmarks, "enqueue_source", side_effect=OSError("disk full")))
            fetch_bookmarks.main()
            return archive, send, build

    def test_already_sent_still_enqueues_and_does_not_resend_or_archive(self):
        archive, send, build = self.run_fetch(["--send-only", "--podcast-queue"], sent=True)
        self.assertEqual(len(json.loads(self.state.read_text())["tasks"]), 1)
        self.run_fetch(["--send-only", "--podcast-queue"], sent=True)
        self.assertEqual(len(json.loads(self.state.read_text())["tasks"]), 1)
        archive.assert_not_called()
        send.assert_not_called()
        build.assert_not_called()

    def test_podcast_only_has_no_mail_docx_or_blog(self):
        archive, send, build = self.run_fetch(["--podcast-only"])
        self.assertTrue(self.state.exists())
        archive.assert_not_called()
        send.assert_not_called()
        build.assert_not_called()

    def test_snapshot_failure_does_not_block_kindle(self):
        archive, send, build = self.run_fetch(["--send-only", "--podcast-queue"], snapshot_error=True)
        send.assert_called_once()
        build.assert_called_once()
        archive.assert_not_called()
        self.assertFalse(self.state.exists())

    def test_podcast_only_snapshot_failure_is_nonzero(self):
        with self.assertRaises(SystemExit) as error:
            self.run_fetch(["--podcast-only"], snapshot_error=True)
        self.assertEqual(error.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
