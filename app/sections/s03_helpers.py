"""Arka Downloader section: HELPERS."""

from .s02_terminal import *

# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════
def esc(v) -> str:
    return html.escape(str(v if v is not None else ""))


def fmt_bytes(v) -> str:
    if not v:
        return "—"
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "—"
    for u in ("B", "KB", "MB", "GB", "TB"):
        if v < 1024:
            return f"{v:.1f} {u}"
        v /= 1024
    return f"{v:.1f} PB"


def fmt_duration(s) -> str:
    if not s:
        return "—"
    try:
        s = int(s)
    except (TypeError, ValueError):
        return "—"
    h, m, x = s // 3600, (s % 3600) // 60, s % 60
    return f"{h:02d}:{m:02d}:{x:02d}" if h else f"{m:02d}:{x:02d}"


def progress_bar(p: float, length: int = 12) -> str:
    try:
        p = max(0.0, min(100.0, float(p)))
    except (TypeError, ValueError):
        p = 0.0
    filled = int(length * p / 100)
    if p >= 100:
        return "🟩" * length
    return "🟩" * filled + ("🟨" if filled < length else "") + \
           "⬜" * max(0, length - filled - 1)


def now_ts() -> float:
    return time.time()


def fmt_time(ts) -> str:
    try:
        return time.strftime("%Y-%m-%d %H:%M", time.localtime(float(ts)))
    except Exception:
        return "—"


def fmt_dt_short(ts) -> str:
    try:
        return time.strftime("%Y%m%d_%H%M%S", time.localtime(ts))
    except Exception:
        return "unknown"


def safe_cb(data: str) -> str:
    if data is None:
        return ""
    b = data.encode("utf-8")
    if len(b) <= 64:
        return data
    truncated = b[:64]
    while truncated:
        try:
            return truncated.decode("utf-8")
        except UnicodeDecodeError:
            truncated = truncated[:-1]
    return ""


def new_id() -> str:
    return uuid.uuid4().hex[:8].upper()


_URL_RE = re.compile(r"^https?://[^\s]+$", re.IGNORECASE)


def is_valid_url(t: str) -> bool:
    return bool(_URL_RE.match((t or "").strip()))



__all__ = [name for name in globals() if not name.startswith("__")]
