"""Arka Downloader section: RATE / COOLDOWN HELPERS."""

from .s13_i18n import *

# ══════════════════════════════════════════════════════════════
# RATE / COOLDOWN HELPERS
# ══════════════════════════════════════════════════════════════
_last_dl_req: dict = {}


def is_limit_exempt(uid: int) -> bool:
    if uid in OWNER_IDS:
        return db_get("limit_owner_unlimited", "1") == "1"
    if db_get("limit_vip_unlimited", "1") == "1":
        u = UserRepo.get(uid)
        if u and u.is_vip:
            return True
    return False


def cooldown_remaining(uid: int) -> int:
    if is_limit_exempt(uid):
        return 0
    try:
        cd = int(float(db_get("limit_cooldown_sec", "3") or 0))
    except (TypeError, ValueError):
        cd = 0
    if cd <= 0:
        return 0
    now = now_ts()
    last = _last_dl_req.get(uid, 0.0)
    if now - last < cd:
        return max(1, int(cd - (now - last) + 0.999))
    _last_dl_req[uid] = now
    if len(_last_dl_req) > 5000:
        _last_dl_req.clear()
    return 0


def user_lang(user) -> str:
    if user is None:
        return "fa"
    return user.lang if user.lang in I18N else "fa"


def user_has_chosen_lang(uid: int) -> bool:
    try:
        r = get_conn().execute(
            "SELECT lang_chosen FROM users WHERE user_id=?",
            (uid,)).fetchone()
        return bool(r and r["lang_chosen"])
    except Exception:
        return True


def mark_lang_chosen(uid: int, lang: str):
    with contextlib.suppress(Exception):
        get_conn().execute(
            "UPDATE users SET lang=?, lang_chosen=1, updated_at=? "
            "WHERE user_id=?", (lang, now_ts(), uid))



__all__ = [name for name in globals() if not name.startswith("__")]
