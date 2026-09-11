import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import fetch_bookmarks


class BookmarkSyncTests(unittest.TestCase):
    def _run_archive_only(self, root: Path, urls: list[str], contents):
        session_file = root / "x_session.json"
        session_file.write_text("{}", encoding="utf-8")

        page = MagicMock()
        context = MagicMock()
        context.new_page.return_value = page
        context.cookies.return_value = []
        browser = MagicMock()
        browser.new_context.return_value = context
        playwright = MagicMock()
        playwright.chromium.launch.return_value = browser
        playwright_manager = MagicMock()
        playwright_manager.__enter__.return_value = playwright

        patches = [
            patch.object(fetch_bookmarks, "SESSION_FILE", session_file),
            patch.object(fetch_bookmarks, "OUTDIR", root / "outbox"),
            patch.object(fetch_bookmarks, "sync_playwright", return_value=playwright_manager),
            patch.object(fetch_bookmarks, "get_bookmark_urls", return_value=urls),
            patch.object(fetch_bookmarks, "wait_for_content"),
            patch.object(fetch_bookmarks, "extract_content_from_page", side_effect=contents),
            patch.object(fetch_bookmarks, "save_article_archive", return_value=root / "archive.md"),
            patch.object(fetch_bookmarks, "send_article"),
            patch.object(fetch_bookmarks, "save_sent_history"),
            patch.object(sys, "argv", ["fetch_bookmarks.py", "--archive-only", "--count", "2"]),
            patch("builtins.print"),
            patch.object(fetch_bookmarks, "KINDLE_EMAIL", "test@example.com"),
        ]
        entered = [item.start() for item in patches]
        self.addCleanup(lambda: [item.stop() for item in reversed(patches)])
        return page, entered

    def test_archive_only_skips_existing_url_and_archives_short_post_without_delivery(self):
        archived_url = "https://x.com/old/status/100"
        new_url = "https://x.com/new/status/200"
        short_post = {
            "title": "Short post",
            "author": "Writer",
            "is_article": False,
            "items": [{"type": "para", "text": "brief"}],
        }

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(fetch_bookmarks, "load_archived_urls", return_value={archived_url}), patch.object(
                fetch_bookmarks,
                "load_sent_history",
                return_value={new_url: {"url": new_url}},
            ):
                page, mocks = self._run_archive_only(root, [archived_url, new_url], [short_post])
                fetch_bookmarks.main()

        extract_mock = mocks[5]
        archive_mock = mocks[6]
        send_mock = mocks[7]
        save_history_mock = mocks[8]
        self.assertEqual(page.goto.call_args_list[0].args[0], new_url)
        extract_mock.assert_called_once_with(page)
        archive_mock.assert_called_once()
        self.assertEqual(archive_mock.call_args.kwargs["url"], new_url)
        self.assertEqual(archive_mock.call_args.kwargs["chars"], 5)
        send_mock.assert_not_called()
        save_history_mock.assert_not_called()

    def test_archive_only_exits_nonzero_after_an_extraction_failure(self):
        failed_url = "https://x.com/user/status/300"

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(fetch_bookmarks, "load_archived_urls", return_value=set()), patch.object(
                fetch_bookmarks, "load_sent_history", return_value={}
            ):
                _, mocks = self._run_archive_only(root, [failed_url], [RuntimeError("page failed")])
                with self.assertRaises(SystemExit) as raised:
                    fetch_bookmarks.main()

        self.assertEqual(raised.exception.code, 1)
        mocks[6].assert_not_called()
        mocks[7].assert_not_called()
        mocks[8].assert_not_called()

    def test_archive_only_skips_unavailable_content_without_failing(self):
        unavailable_url = "https://x.com/user/status/400"
        empty_post = {
            "title": "",
            "author": "",
            "is_article": False,
            "items": [],
        }

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(fetch_bookmarks, "load_archived_urls", return_value=set()), patch.object(
                fetch_bookmarks, "load_sent_history", return_value={}
            ):
                page, mocks = self._run_archive_only(root, [unavailable_url], [empty_post])
                fetch_bookmarks.main()

        self.assertEqual(page.goto.call_args_list[0].args[0], unavailable_url)
        mocks[6].assert_not_called()
        mocks[7].assert_not_called()
        mocks[8].assert_not_called()

    def test_archive_only_publishes_successes_despite_other_failures(self):
        successful_url = "https://x.com/user/status/500"
        failed_url = "https://x.com/user/status/600"
        post = {
            "title": "Publish me",
            "author": "Writer",
            "is_article": False,
            "items": [{"type": "para", "text": "body"}],
        }

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(fetch_bookmarks, "load_archived_urls", return_value=set()), patch.object(
                fetch_bookmarks, "load_sent_history", return_value={}
            ):
                _, mocks = self._run_archive_only(
                    root,
                    [successful_url, failed_url],
                    [post, RuntimeError("page failed")],
                )
                fetch_bookmarks.main()

        archive_mock = mocks[6]
        archive_mock.assert_called_once()
        self.assertEqual(archive_mock.call_args.kwargs["url"], successful_url)


if __name__ == "__main__":
    unittest.main()
