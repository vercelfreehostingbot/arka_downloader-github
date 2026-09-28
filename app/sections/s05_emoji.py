"""Arka Downloader section: EMOJI."""

from .s04_photo_video_audio_support import *

# ══════════════════════════════════════════════════════════════
# EMOJI
# ══════════════════════════════════════════════════════════════
_NORMAL_EMOJI_RE = re.compile(
    "(?:"
    "[\U0001F1E0-\U0001F1FF]"
    "|[\U0001F300-\U0001F5FF]"
    "|[\U0001F600-\U0001F64F]"
    "|[\U0001F680-\U0001F6FF]"
    "|[\U0001F700-\U0001F77F]"
    "|[\U0001F780-\U0001F7FF]"
    "|[\U0001F800-\U0001F8FF]"
    "|[\U0001F900-\U0001F9FF]"
    "|[\U0001FA00-\U0001FAFF]"
    "|[\U00002600-\U000026FF]"
    "|[\U00002700-\U000027BF]"
    "|[\U00002B00-\U00002BFF]"
    ")[\U0001F3FB-\U0001F3FF\uFE0F]?", re.UNICODE
)

_TG_EMOJI_TAG_RE = re.compile(
    r'<tg-emoji\s+emoji-id="[^"]*">.*?</tg-emoji>', re.DOTALL
)

_TG_EMOJI_STRIP_RE = re.compile(
    r'<tg-emoji\s+emoji-id="[^"]*">(.*?)</tg-emoji>', re.DOTALL
)


def extract_premium_emojis(message: Message):
    out = []
    try:
        text = message.text or message.caption or ""
        ents = list(getattr(message, "entities", None) or [])
        ents += list(getattr(message, "caption_entities", None) or [])
        for ent in ents:
            cid = str(getattr(ent, "custom_emoji_id", "") or "").strip()
            if not cid:
                continue
            off = int(getattr(ent, "offset", 0) or 0)
            ln = int(getattr(ent, "length", 0) or 0)
            fb = ""
            if text:
                raw = text.encode("utf-16-le")
                fb = raw[off * 2:(off + ln) * 2].decode(
                    "utf-16-le", errors="ignore")
            if not fb or not fb.strip():
                fb = "✨"
            out.append((cid, fb))
    except Exception as e:
        logging.warning(f"extract_premium_emojis failed: {e}")
    return out


def extract_normal_emojis(text: str):
    if not text:
        return []
    return _NORMAL_EMOJI_RE.findall(text)



__all__ = [name for name in globals() if not name.startswith("__")]
