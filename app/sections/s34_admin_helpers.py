"""Arka Downloader section: ADMIN HELPERS."""

from .s33_help import *

# ══════════════════════════════════════════════════════════════
# ADMIN HELPERS
# ══════════════════════════════════════════════════════════════
def is_admin(uid: int) -> bool:
    # Read owners dynamically so wildcard-imported OWNER_IDS cannot become stale.
    try:
        raw = os.getenv("OWNER_IDS", "")
        owners = {
            int(x.strip().lstrip("@"))
            for x in raw.replace(",", " ").replace(";", " ").split()
            if x.strip().lstrip("@").lstrip("-").isdigit()
        }
        if uid in owners or uid in OWNER_IDS:
            return True
    except Exception:
        if uid in OWNER_IDS:
            return True
    try:
        r = get_conn().execute(
            "SELECT 1 FROM extra_admins WHERE user_id=?", (uid,)).fetchone()
        return bool(r)
    except Exception:
        return False


async def require_admin(cb: CallbackQuery) -> bool:
    if not is_admin(cb.from_user.id):
        with contextlib.suppress(Exception):
            await cb.answer("⛔", show_alert=True)
        return False
    return True


async def _admin_lang(c, uid: int) -> str:
    user = UserRepo.get(uid)
    return user_lang(user)


def _restart_process(current_file):
    with contextlib.suppress(Exception):
        close_conn()
    try:
        sys.stdout.flush()
        os.execv(sys.executable,
                 [sys.executable, str(current_file)] + sys.argv[1:])
    except Exception:
        os._exit(0)



__all__ = [name for name in globals() if not name.startswith("__")]
