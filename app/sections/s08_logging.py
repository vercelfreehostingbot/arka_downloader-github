"""Arka Downloader section: LOGGING."""

from .s07_docker_manager import *

# ══════════════════════════════════════════════════════════════
# LOGGING
# ══════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S", stream=sys.stdout)
logging.getLogger("aiogram.event").setLevel(logging.ERROR)
logging.getLogger("aiohttp.access").setLevel(logging.ERROR)
logging.getLogger("yt_dlp").setLevel(logging.ERROR)
logging.getLogger("gallery_dl").setLevel(logging.ERROR)



__all__ = [name for name in globals() if not name.startswith("__")]
