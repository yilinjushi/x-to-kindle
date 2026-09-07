import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

from archive import save_article_archive
from build_site import build_site
from send_web_article import extract_image_urls


class ArchiveSiteTests(unittest.TestCase):
    def test_extracts_absolute_deduplicated_image_urls(self):
        markup = '<article><p>Text long enough for readability.</p><img src="/hero.jpg"><img src="/hero.jpg"></article>'
        self.assertEqual(extract_image_urls(markup, "https://example.com/post"), ["https://example.com/hero.jpg"])

    def test_archive_downloads_image_and_builds_site(self):
        response = Mock(content=b"image-bytes", headers={"content-type": "image/jpeg"})
        response.raise_for_status.return_value = None
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive_dir = root / "archive"
            site_dir = root / "site"
            with patch("archive.ARCHIVE_DIR", archive_dir), patch("archive.SITE_DIR", site_dir), patch("archive.requests.get", return_value=response):
                archived = save_article_archive(
                    url="https://example.com/story",
                    title="A Story",
                    text="Fallback",
                    items=[{"type": "para", "text": "Opening"}, {"type": "image", "src": "https://example.com/image"}],
                    saved_at=date(2026, 9, 7),
                )
            self.assertTrue(archived.exists())
            self.assertIn("![Article image](/assets/", archived.read_text(encoding="utf-8"))
            self.assertTrue(any((site_dir / "assets").rglob("*.jpg")))
            self.assertTrue((site_dir / "index.html").exists())
            self.assertTrue(any((site_dir / "articles").rglob("index.html")))

    def test_existing_archive_builds_without_frontmatter_images_field(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive_dir = root / "archive" / "2026"
            archive_dir.mkdir(parents=True)
            (archive_dir / "entry.md").write_text('---\ntitle: "Entry"\ndate: 2026-01-01\n---\n\n# Entry\n\nBody', encoding="utf-8")
            site_dir = root / "site"
            build_site(root / "archive", site_dir)
            self.assertIn("Entry", (site_dir / "index.html").read_text(encoding="utf-8"))

    def test_raw_html_from_an_article_is_escaped(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive_dir = root / "archive" / "2026"
            archive_dir.mkdir(parents=True)
            (archive_dir / "unsafe.md").write_text('---\ntitle: "Unsafe"\n---\n\n<script>alert(1)</script>', encoding="utf-8")
            site_dir = root / "site"
            build_site(root / "archive", site_dir)
            page = next((site_dir / "articles").rglob("index.html")).read_text(encoding="utf-8")
            self.assertNotIn("<script>", page)
            self.assertIn("&lt;script&gt;", page)


if __name__ == "__main__":
    unittest.main()
