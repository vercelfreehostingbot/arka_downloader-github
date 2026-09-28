"""Arka Downloader section: QUALITY."""

from .s09_database import *

# ══════════════════════════════════════════════════════════════
# QUALITY
# ══════════════════════════════════════════════════════════════
VIDEO_QUALITIES = ("best", "4320p", "2160p", "1440p",
                   "1080p", "720p", "480p", "360p")
MUSIC_QUALITIES = ("audio_best", "audio", "audio_320", "audio_128")
ALL_QUALITIES   = VIDEO_QUALITIES + MUSIC_QUALITIES
QUALITY_ORDER   = ALL_QUALITIES


def is_audio_quality(q) -> bool:
    return isinstance(q, str) and q in MUSIC_QUALITIES


QUALITY_HEIGHTS = {
    "4320p": 4320, "2160p": 2160, "1440p": 1440,
    "1080p": 1080, "720p": 720, "480p": 480, "360p": 360,
}

QUALITY_LABELS = {
    "fa": {
        "best":       "🌟 بهترین کیفیت",
        "4320p":      "🔥 کیفیت 8K",
        "2160p":      "🎬 کیفیت 4K",
        "1440p":      "🎬 کیفیت 2K",
        "1080p":      "🎬 کیفیت 1080p",
        "720p":       "🎥 کیفیت 720p",
        "480p":       "📺 کیفیت 480p",
        "360p":       "📱 کیفیت 360p",
        "audio_best": "🌟 بهترین کیفیت صوتی",
        "audio":      "🎵 MP3 (192kbps)",
        "audio_320":  "🎵 MP3 320kbps",
        "audio_128":  "🎵 MP3 128kbps",
    },
    "en": {
        "best":       "🌟 Best Quality",
        "4320p":      "🔥 8K",
        "2160p":      "🎬 4K",
        "1440p":      "🎬 2K",
        "1080p":      "🎬 1080p",
        "720p":       "🎥 720p",
        "480p":       "📺 480p",
        "360p":       "📱 360p",
        "audio_best": "🌟 Best Audio Quality",
        "audio":      "🎵 MP3 (192kbps)",
        "audio_320":  "🎵 MP3 320kbps",
        "audio_128":  "🎵 MP3 128kbps",
    },
}


def allowed_qualities() -> set:
    raw = db_get("allowed_quality", ",".join(ALL_QUALITIES))
    return {x.strip() for x in raw.split(",") if x.strip()}



__all__ = [name for name in globals() if not name.startswith("__")]
