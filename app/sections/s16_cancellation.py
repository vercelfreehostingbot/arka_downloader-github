"""Arka Downloader section: CANCELLATION."""

from .s15_emoji_map_premium import *

# ══════════════════════════════════════════════════════════════
# CANCELLATION
# ══════════════════════════════════════════════════════════════
_cancelled: set = set()
_cancel_lock = threading.Lock()
_MAX_CANCEL = 5000


def mark_cancelled(jid):
    with _cancel_lock:
        if len(_cancelled) >= _MAX_CANCEL:
            half = list(_cancelled)[:_MAX_CANCEL // 2]
            for x in half:
                _cancelled.discard(x)
        _cancelled.add(jid)


def is_cancelled(jid):
    with _cancel_lock:
        return jid in _cancelled


def clear_cancelled(jid):
    with _cancel_lock:
        _cancelled.discard(jid)



__all__ = [name for name in globals() if not name.startswith("__")]
