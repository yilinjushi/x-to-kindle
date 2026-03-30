import json
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_OUTDIR = BASE_DIR / "kindle_outbox"
DEFAULT_STATE_DIR = BASE_DIR / "state"
DEFAULT_SENT_HISTORY = DEFAULT_STATE_DIR / "sent_articles.json"
DEFAULT_SESSION_FILE = BASE_DIR / "x_session.json"


def env_path(name: str, default: Path) -> Path:
    value = os.environ.get(name, "").strip()
    return Path(value) if value else default


OUTDIR = env_path("OUTDIR", DEFAULT_OUTDIR)
STATE_DIR = env_path("STATE_DIR", DEFAULT_STATE_DIR)
SENT_HISTORY_FILE = env_path("SENT_HISTORY_FILE", DEFAULT_SENT_HISTORY)
SESSION_FILE = env_path("SESSION_FILE", DEFAULT_SESSION_FILE)

KINDLE_EMAIL = os.environ.get("KINDLE_EMAIL", "").strip()
GMAIL_USER = os.environ.get("GMAIL_USER", "").strip()
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
CHROME_EXE = os.environ.get("CHROME_EXE", "").strip() or None
PYTHON_EXE = os.environ.get("PYTHON_EXE", "").strip() or None

BOOKMARKS_URL = "https://x.com/i/bookmarks"
MIN_TEXT_CHARS = int(os.environ.get("MIN_TEXT_CHARS", "1200"))
TARGET_COUNT = int(os.environ.get("TARGET_COUNT", "15"))
MAX_SCROLLS = int(os.environ.get("MAX_SCROLLS", "40"))

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/132.0.0.0 Safari/537.36"
)
LAUNCH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-first-run",
    "--no-default-browser-check",
]


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_json_file(path: Path, default):
    if not path.exists():
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)

