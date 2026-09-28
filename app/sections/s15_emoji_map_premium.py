"""Arka Downloader section: EMOJI MAP (PREMIUM)."""

from .s14_rate_cooldown_helpers import *

# ══════════════════════════════════════════════════════════════
# EMOJI MAP (PREMIUM)
# ══════════════════════════════════════════════════════════════
_emoji_cache: dict = {}
_emoji_cache_ts: float = 0.0
_EMOJI_TTL = 2.0


def invalidate_emoji_cache():
    global _emoji_cache_ts
    _emoji_cache_ts = 0.0


def get_emoji_map() -> dict:
    global _emoji_cache, _emoji_cache_ts
    now = now_ts()
    if now - _emoji_cache_ts > _EMOJI_TTL:
        try:
            rows = get_conn().execute(
                "SELECT * FROM emoji_map ORDER BY created_at DESC").fetchall()
            _emoji_cache = {r["normal_emoji"]: (r["premium_id"], r["fallback_emoji"])
                            for r in rows}
            _emoji_cache_ts = now
        except Exception:
            _emoji_cache = {}
    return _emoji_cache


def emoji_map_count() -> int:
    r = get_conn().execute("SELECT COUNT(*) AS c FROM emoji_map").fetchone()
    return int(r["c"] or 0)


def premiumize(text: str) -> str:
    if not text:
        return text
    if db_get("premium_emoji_enabled", "1") != "1":
        return text
    emap = get_emoji_map()
    if not emap:
        return text
    keys = sorted(emap.keys(), key=len, reverse=True)
    pattern = re.compile("|".join(re.escape(k) for k in keys))

    def _sub(m):
        normal = m.group(0)
        pid, _ = emap[normal]
        return f'<tg-emoji emoji-id="{pid}">{normal}</tg-emoji>'

    def _replace(chunk):
        return pattern.sub(_sub, chunk)

    parts, last = [], 0
    for m in _TG_EMOJI_TAG_RE.finditer(text):
        parts.append(_replace(text[last:m.start()]))
        parts.append(m.group(0))
        last = m.end()
    parts.append(_replace(text[last:]))
    return "".join(parts)


def strip_premium(text: str) -> str:
    if not text:
        return text
    return _TG_EMOJI_STRIP_RE.sub(r'\1', text)


class PremiumEmojiRequestMiddleware(BaseRequestMiddleware):
    async def __call__(self, make_request, bot, method):
        try:
            pm = getattr(method, "parse_mode", None)
            html_mode = pm is not None and (
                (isinstance(pm, str) and pm.upper() == "HTML")
                or type(pm).__name__ == "Default")
            if html_mode:
                for attr, ent in (("text", "entities"),
                                  ("caption", "caption_entities")):
                    val = getattr(method, attr, None)
                    if isinstance(val, str) and val and \
                            not getattr(method, ent, None):
                        new = premiumize(val)
                        if new != val:
                            setattr(method, attr, new)
        except Exception as e:
            logging.debug(f"premium emoji middleware: {e}")
        return await make_request(bot, method)



__all__ = [name for name in globals() if not name.startswith("__")]
