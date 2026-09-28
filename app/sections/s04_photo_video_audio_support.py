"""Arka Downloader section: PHOTO / VIDEO / AUDIO SUPPORT."""

from .s03_helpers import *

# ══════════════════════════════════════════════════════════════
# PHOTO / VIDEO / AUDIO SUPPORT
# ══════════════════════════════════════════════════════════════
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".gif",
              ".bmp", ".tiff", ".heic", ".svg", ".avif")

VIDEO_EXTS = (".mp4", ".webm", ".mov", ".mkv", ".m4v",
              ".avi", ".3gp", ".flv", ".ts", ".mpeg", ".mpg")

AUDIO_EXTS = (".mp3", ".m4a", ".opus", ".ogg",
              ".flac", ".wav", ".aac", ".wma")

IMAGE_HOST_HINTS = (
    "pinimg.com", "i.imgur.com", "images.unsplash.com",
    "cdninstagram.com", "fbcdn.net", "pbs.twimg.com",
    "pixabay.com", "pexels.com", "wikimedia.org",
    "ggpht.com", "staticflickr.com", "imagebam.com",
    "postimg.cc", "imgbox.com", "flickr.com",
)

_IMG_CTYPE_EXT = {
    "image/jpeg": ".jpg", "image/jpg": ".jpg",
    "image/png": ".png", "image/webp": ".webp",
    "image/gif": ".gif", "image/bmp": ".bmp",
    "image/tiff": ".tiff", "image/heic": ".heic",
    "image/avif": ".avif", "image/svg+xml": ".svg",
}


def is_direct_image_url(url: str) -> bool:
    low = (url or "").lower().split("?")[0].split("#")[0]
    if low.endswith(IMAGE_EXTS):
        return True
    return any(h in low for h in IMAGE_HOST_HINTS)


def is_image_file(path) -> bool:
    try:
        return Path(path).suffix.lower() in IMAGE_EXTS
    except Exception:
        return False


def is_video_file(path) -> bool:
    try:
        return Path(path).suffix.lower() in VIDEO_EXTS
    except Exception:
        return False


def is_audio_file(path) -> bool:
    try:
        return Path(path).suffix.lower() in AUDIO_EXTS
    except Exception:
        return False


def cleanup_empty_dir(path_like) -> bool:
    try:
        p = Path(path_like)
        if p.exists() and p.is_dir() and not any(p.iterdir()):
            p.rmdir()
            return True
    except Exception:
        pass
    return False


def _probe_duration(path: Path) -> int:
    if not shutil.which("ffprobe"):
        return 0
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error",
             "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=30,
        )
        val = (r.stdout or "").strip()
        if val and val not in ("N/A", "nan"):
            return int(float(val))
    except Exception:
        pass
    return 0


def compress_image_for_tg(path: Path, max_bytes: int = PHOTO_TG_LIMIT) -> Path:
    if not HAS_PIL:
        return path
    try:
        if not path.exists() or path.stat().st_size <= max_bytes:
            return path
    except Exception:
        return path
    try:
        img = Image.open(path)
        if img.mode in ("RGBA", "P", "LA"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")
        out = path.with_name(path.stem + "_tg.jpg")
        for scale in (1.0, 0.85, 0.7, 0.55, 0.4):
            if scale < 1.0:
                ns = (max(1, int(img.width * scale)),
                      max(1, int(img.height * scale)))
                cur = img.resize(ns, Image.LANCZOS)
            else:
                cur = img
            for q in (88, 78, 68, 55, 45, 35):
                try:
                    cur.save(out, "JPEG", quality=q, optimize=True)
                except Exception:
                    continue
                if out.stat().st_size <= max_bytes:
                    return out
        if out.exists():
            return out
    except Exception as e:
        logging.warning(f"compress failed: {e}")
    return path


async def download_tg_file(bot: Bot, file_id: str, dest: Path) -> None:
    tg_file = await bot.get_file(file_id)
    file_path = (tg_file.file_path or "").strip()
    if file_path.startswith("/var/lib/telegram-bot-api/"):
        rel = file_path[len("/var/lib/telegram-bot-api/"):]
        for src in (LOCAL_TG_DATA / rel,
                    Path("/var/lib/telegram-bot-api") / rel):
            if src.exists() and src.is_file():
                shutil.copy2(src, dest)
                return
        raise FileNotFoundError("Local TG API file not accessible")
    await bot.download_file(file_path, dest)



__all__ = [name for name in globals() if not name.startswith("__")]
