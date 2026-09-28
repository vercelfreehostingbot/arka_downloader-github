"""Arka Downloader section: PATHS."""

from .s00_auto_version import *

# ══════════════════════════════════════════════════════════════
# PATHS
# ══════════════════════════════════════════════════════════════
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DOWNLOAD_DIR = BASE_DIR / "downloads"
LOG_DIR = BASE_DIR / "logs"
BACKUP_DIR = BASE_DIR / "backups"
UPDATE_DIR = BASE_DIR / "updates"
ENV_FILE = BASE_DIR / ".env"

for _d in (DATA_DIR, DOWNLOAD_DIR, LOG_DIR, BACKUP_DIR, UPDATE_DIR):
    _d.mkdir(parents=True, exist_ok=True)

LOCAL_TG_API = "http://127.0.0.1:8081"
LOCAL_TG_DATA = DATA_DIR / "tg-api"
PHOTO_TG_LIMIT = 9 * 1024 * 1024



__all__ = [name for name in globals() if not name.startswith("__")]
