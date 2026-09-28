"""Arka Downloader section: ANNOUNCE — HELPERS."""

from .s47_admin_update import *

# ══════════════════════════════════════════════════════════════
# ANNOUNCE — HELPERS
# ══════════════════════════════════════════════════════════════
def _audience_count() -> int:
    try:
        a = db_get("announce_audience", "all")
        q = {
            "vip": "SELECT COUNT(*) AS c FROM users WHERE is_blocked=0 AND is_vip=1",
            "active": "SELECT COUNT(*) AS c FROM users WHERE is_blocked=0 AND downloads>0",
            "inactive": "SELECT COUNT(*) AS c FROM users WHERE is_blocked=0 AND downloads=0",
        }.get(a, "SELECT COUNT(*) AS c FROM users WHERE is_blocked=0")
        r = get_conn().execute(q).fetchone()
        return int(r["c"] or 0)
    except Exception:
        return 0


def _audience_uids() -> list:
    a = db_get("announce_audience", "all")
    q = {
        "vip": "SELECT user_id FROM users WHERE is_blocked=0 AND is_vip=1",
        "active": "SELECT user_id FROM users WHERE is_blocked=0 AND downloads>0",
        "inactive": "SELECT user_id FROM users WHERE is_blocked=0 AND downloads=0",
    }.get(a, "SELECT user_id FROM users WHERE is_blocked=0")
    try:
        rows = get_conn().execute(q).fetchall()
        return [int(r["user_id"]) for r in rows]
    except Exception:
        return []


async def _auto_delete_msg(bot, chat_id, msg_id, delay):
    try:
        await asyncio.sleep(delay)
        await bot.delete_message(chat_id, msg_id)
    except Exception:
        pass


def _spawn_auto_delete(c: Container, bot, chat_id, msg_id, delay):
    task = asyncio.create_task(_auto_delete_msg(bot, chat_id, msg_id, delay))
    if c and hasattr(c, 'bg_tasks'):
        c.bg_tasks.append(task)

        def _cleanup(t):
            with contextlib.suppress(Exception):
                if t in c.bg_tasks:
                    c.bg_tasks.remove(t)

        task.add_done_callback(_cleanup)
    return task



__all__ = [name for name in globals() if not name.startswith("__")]
