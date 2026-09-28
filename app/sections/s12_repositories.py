"""Arka Downloader section: REPOSITORIES."""

from .s11_models import *

# ══════════════════════════════════════════════════════════════
# REPOSITORIES
# ══════════════════════════════════════════════════════════════
class UserRepo:
    @staticmethod
    def upsert(user_id, chat_id, username, first_name):
        t = now_ts()
        get_conn().execute(
            """INSERT INTO users(user_id, chat_id, username, first_name,
                                 created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                 chat_id=excluded.chat_id,
                 username=excluded.username,
                 first_name=excluded.first_name,
                 updated_at=excluded.updated_at""",
            (user_id, chat_id, username, first_name, t, t))

    @staticmethod
    def get(uid) -> Optional[User]:
        r = get_conn().execute(
            "SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
        return User.from_row(r) if r else None

    @staticmethod
    def set_blocked(uid, value):
        get_conn().execute(
            "UPDATE users SET is_blocked=?, updated_at=? WHERE user_id=?",
            (int(value), now_ts(), uid))

    @staticmethod
    def set_vip(uid, value):
        get_conn().execute(
            "UPDATE users SET is_vip=?, updated_at=? WHERE user_id=?",
            (int(value), now_ts(), uid))

    @staticmethod
    def set_lang(uid, lang):
        get_conn().execute(
            "UPDATE users SET lang=?, lang_chosen=1, updated_at=? "
            "WHERE user_id=?", (lang, now_ts(), uid))

    @staticmethod
    def bump(uid, col, d=1):
        if col not in {"downloads", "success_dl", "failed_dl"}:
            return
        get_conn().execute(
            f"UPDATE users SET {col}={col}+?, updated_at=? WHERE user_id=?",
            (d, now_ts(), uid))

    @staticmethod
    def active_jobs(uid) -> int:
        ph = ",".join("?" for _ in ACTIVE_STATUSES)
        r = get_conn().execute(
            f"SELECT COUNT(*) AS c FROM jobs WHERE user_id=? AND status IN ({ph})",
            (uid, *ACTIVE_STATUSES)).fetchone()
        return int(r["c"] or 0)

    @staticmethod
    def list_recent(limit=20, offset=0):
        rows = get_conn().execute(
            "SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)).fetchall()
        return [User.from_row(r) for r in rows]

    @staticmethod
    def list_vip(limit=20, offset=0):
        rows = get_conn().execute(
            "SELECT * FROM users WHERE is_vip=1 ORDER BY updated_at DESC "
            "LIMIT ? OFFSET ?", (limit, offset)).fetchall()
        return [User.from_row(r) for r in rows]

    @staticmethod
    def count_all() -> int:
        r = get_conn().execute("SELECT COUNT(*) AS c FROM users").fetchone()
        return int(r["c"] or 0)

    @staticmethod
    def count_vip() -> int:
        r = get_conn().execute(
            "SELECT COUNT(*) AS c FROM users WHERE is_vip=1").fetchone()
        return int(r["c"] or 0)

    @staticmethod
    def stats() -> dict:
        r = get_conn().execute(
            """SELECT COUNT(*) AS total,
                      SUM(CASE WHEN is_blocked=1 THEN 1 ELSE 0 END) AS blocked,
                      SUM(CASE WHEN is_vip=1 THEN 1 ELSE 0 END) AS vip
               FROM users""").fetchone()
        return {"total": int(r["total"] or 0),
                "blocked": int(r["blocked"] or 0),
                "vip": int(r["vip"] or 0)}


class JobRepo:
    @staticmethod
    def create(user_id, chat_id, url, status=STATUS_QUEUED) -> Job:
        jid = new_id()
        get_conn().execute(
            """INSERT INTO jobs(job_id, user_id, chat_id, url, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (jid, user_id, chat_id, url, status, now_ts()))
        return JobRepo.get(jid)

    @staticmethod
    def get(jid) -> Optional[Job]:
        r = get_conn().execute(
            "SELECT * FROM jobs WHERE job_id=?", (jid,)).fetchone()
        return Job.from_row(r) if r else None

    ALLOWED_UPD = {
        "title", "quality", "duration", "filesize", "status", "progress",
        "speed", "eta", "file_path", "thumbnail", "msg_id", "notice_msg_id",
        "delete_at", "error", "started_at", "finished_at",
    }

    @staticmethod
    def update(jid, **fields):
        f = {k: v for k, v in fields.items() if k in JobRepo.ALLOWED_UPD}
        if not f:
            return
        sets = ", ".join(f"{k}=?" for k in f)
        get_conn().execute(
            f"UPDATE jobs SET {sets} WHERE job_id=?", (*f.values(), jid))

    @staticmethod
    def history(uid, limit=10, offset=0):
        rows = get_conn().execute(
            """SELECT * FROM jobs WHERE user_id=?
               ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (uid, limit, offset)).fetchall()
        return [Job.from_row(r) for r in rows]

    @staticmethod
    def count_for_user(uid) -> int:
        r = get_conn().execute(
            "SELECT COUNT(*) AS c FROM jobs WHERE user_id=?", (uid,)).fetchone()
        return int(r["c"] or 0)

    @staticmethod
    def by_status(status, limit=10, offset=0):
        rows = get_conn().execute(
            "SELECT * FROM jobs WHERE status=? "
            "ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (status, limit, offset)).fetchall()
        return [Job.from_row(r) for r in rows]

    @staticmethod
    def count_by_status(status) -> int:
        r = get_conn().execute(
            "SELECT COUNT(*) AS c FROM jobs WHERE status=?", (status,)).fetchone()
        return int(r["c"] or 0)

    @staticmethod
    def active(limit=20, offset=0):
        ph = ",".join("?" for _ in ACTIVE_STATUSES)
        rows = get_conn().execute(
            f"SELECT * FROM jobs WHERE status IN ({ph}) "
            f"ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (*ACTIVE_STATUSES, limit, offset)).fetchall()
        return [Job.from_row(r) for r in rows]

    @staticmethod
    def count_active() -> int:
        ph = ",".join("?" for _ in ACTIVE_STATUSES)
        r = get_conn().execute(
            f"SELECT COUNT(*) AS c FROM jobs WHERE status IN ({ph})",
            ACTIVE_STATUSES).fetchone()
        return int(r["c"] or 0)

    @staticmethod
    def list_paginated(status: str, limit=10, offset=0):
        if status == "active":
            return JobRepo.active(limit=limit, offset=offset)
        if status == "recent":
            rows = get_conn().execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)).fetchall()
            return [Job.from_row(r) for r in rows]
        return JobRepo.by_status(status, limit=limit, offset=offset)

    @staticmethod
    def count_for_filter(status: str) -> int:
        if status == "active":
            return JobRepo.count_active()
        if status == "recent":
            r = get_conn().execute("SELECT COUNT(*) AS c FROM jobs").fetchone()
            return int(r["c"] or 0)
        return JobRepo.count_by_status(status)

    @staticmethod
    def due_for_delete(now):
        rows = get_conn().execute(
            """SELECT * FROM jobs
               WHERE delete_at IS NOT NULL AND delete_at <= ?
                 AND notice_msg_id IS NULL
                 AND (file_path IS NOT NULL OR msg_id IS NOT NULL)""",
            (now,)).fetchall()
        return [Job.from_row(r) for r in rows]

    @staticmethod
    def stuck_queued(older_than):
        rows = get_conn().execute(
            "SELECT * FROM jobs WHERE status='queued' AND created_at < ?",
            (older_than,)).fetchall()
        return [Job.from_row(r) for r in rows]

    @staticmethod
    def totals() -> dict:
        r = get_conn().execute(
            """SELECT COUNT(*) AS total,
                      SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS completed,
                      SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) AS failed
               FROM jobs""").fetchone()
        return {"total": int(r["total"] or 0),
                "completed": int(r["completed"] or 0),
                "failed": int(r["failed"] or 0)}


class FavRepo:
    @staticmethod
    def add(uid: int, jid: str):
        get_conn().execute(
            "INSERT OR IGNORE INTO favorites(user_id, job_id, created_at) "
            "VALUES (?, ?, ?)", (uid, jid, now_ts()))

    @staticmethod
    def remove(uid: int, jid: str):
        get_conn().execute(
            "DELETE FROM favorites WHERE user_id=? AND job_id=?", (uid, jid))

    @staticmethod
    def is_fav(uid: int, jid: str) -> bool:
        r = get_conn().execute(
            "SELECT 1 FROM favorites WHERE user_id=? AND job_id=?",
            (uid, jid)).fetchone()
        return bool(r)

    @staticmethod
    def list(uid: int, limit: int = 10, offset: int = 0):
        rows = get_conn().execute(
            """SELECT j.* FROM favorites f
               JOIN jobs j ON j.job_id = f.job_id
               WHERE f.user_id=?
               ORDER BY f.created_at DESC LIMIT ? OFFSET ?""",
            (uid, limit, offset)).fetchall()
        return [Job.from_row(r) for r in rows]

    @staticmethod
    def count(uid: int) -> int:
        r = get_conn().execute(
            "SELECT COUNT(*) AS c FROM favorites WHERE user_id=?",
            (uid,)).fetchone()
        return int(r["c"] or 0)


class RateRepo:
    _HOUR = 3600
    _DAY = 86400

    @staticmethod
    def check_and_consume(uid, mode, hour_limit, day_limit):
        if mode not in ("photo", "video", "music"):
            mode = "video"
        now = now_ts()
        with transaction() as c:
            row = c.execute(
                "SELECT * FROM rate_limits WHERE user_id=? AND mode=?",
                (uid, mode)).fetchone()
            if not row:
                c.execute(
                    """INSERT INTO rate_limits(user_id, mode, hour_start,
                       hour_count, day_start, day_count)
                       VALUES (?, ?, ?, 1, ?, 1)""", (uid, mode, now, now))
                return
            hs = float(row["hour_start"] or now)
            hc = int(row["hour_count"] or 0)
            ds = float(row["day_start"] or now)
            dc = int(row["day_count"] or 0)
            if now - hs >= RateRepo._HOUR:
                hs, hc = now, 0
            if now - ds >= RateRepo._DAY:
                ds, dc = now, 0
            if day_limit > 0 and dc >= day_limit:
                raise PermissionError("rate_day")
            if hour_limit > 0 and hc >= hour_limit:
                raise PermissionError("rate_hour")
            c.execute(
                """UPDATE rate_limits
                   SET hour_start=?, hour_count=?, day_start=?, day_count=?
                   WHERE user_id=? AND mode=?""",
                (hs, hc + 1, ds, dc + 1, uid, mode))


class TicketRepo:
    @staticmethod
    def create(uid, msg) -> int:
        cur = get_conn().execute(
            "INSERT INTO tickets(user_id, message, status, created_at) "
            "VALUES (?, ?, 'open', ?)", (uid, msg, now_ts()))
        return cur.lastrowid or 0

    @staticmethod
    def get(tid):
        return get_conn().execute(
            "SELECT * FROM tickets WHERE ticket_id=?", (tid,)).fetchone()

    @staticmethod
    def answer(tid, answer):
        get_conn().execute(
            "UPDATE tickets SET answer=?, status='answered', answered_at=? "
            "WHERE ticket_id=?", (answer, now_ts(), tid))

    @staticmethod
    def close(tid):
        get_conn().execute(
            "UPDATE tickets SET status='closed' WHERE ticket_id=?", (tid,))

    @staticmethod
    def by_status(status, limit=10, offset=0):
        if status == "all":
            return get_conn().execute(
                "SELECT * FROM tickets ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)).fetchall()
        return get_conn().execute(
            """SELECT * FROM tickets WHERE status=?
               ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (status, limit, offset)).fetchall()

    @staticmethod
    def count_by_status(status) -> int:
        if status == "all":
            r = get_conn().execute("SELECT COUNT(*) AS c FROM tickets").fetchone()
        else:
            r = get_conn().execute(
                "SELECT COUNT(*) AS c FROM tickets WHERE status=?",
                (status,)).fetchone()
        return int(r["c"] or 0)

    @staticmethod
    def by_user(uid: int, limit: int = 10):
        return get_conn().execute(
            "SELECT * FROM tickets WHERE user_id=? "
            "ORDER BY created_at DESC LIMIT ?", (uid, limit)).fetchall()

    @staticmethod
    def open_count() -> int:
        r = get_conn().execute(
            "SELECT COUNT(*) AS c FROM tickets WHERE status='open'").fetchone()
        return int(r["c"] or 0)


class MenuButtonRepo:
    USER_KEYS = [
        "menu_download", "menu_history", "menu_favs", "menu_stats",
        "menu_support", "menu_help", "menu_admin",
    ]
    ADMIN_KEYS = [
        "admin_stats", "admin_users", "admin_jobs", "admin_broadcast",
        "admin_tickets", "admin_settings", "admin_limits", "admin_channel",
        "admin_quality", "admin_style", "admin_announce", "admin_miniapp",
        "admin_tools", "admin_update", "admin_logs",
        "admin_buttons", "admin_texts", "admin_guide", "admin_admins",
    ]
    DEFAULTS_USER = {
        "menu_download": ("btn_download", "menu:download"),
        "menu_history": ("btn_history", "menu:history"),
        "menu_favs": ("btn_favs", "menu:favs"),
        "menu_stats": ("btn_stats", "menu:stats"),
        "menu_support": ("btn_support", "menu:support"),
        "menu_help": ("btn_help", "menu:help"),
        "menu_admin": ("btn_admin", "admin:home"),
    }
    DEFAULTS_ADMIN = {
        "admin_stats": ("ad_stats", "admin:stats"),
        "admin_users": ("ad_users", "admin:users"),
        "admin_jobs": ("ad_jobs", "admin:jobs"),
        "admin_broadcast": ("ad_broadcast", "admin:broadcast"),
        "admin_tickets": ("ad_tickets", "admin:tickets"),
        "admin_settings": ("ad_settings", "admin:settings"),
        "admin_limits": ("ad_limits", "admin:limits"),
        "admin_channel": ("ad_channel", "admin:channel"),
        "admin_quality": ("ad_quality", "admin:quality"),
        "admin_style": ("ad_style", "admin:style"),
        "admin_announce": ("ad_announce", "admin:announce"),
        "admin_miniapp": ("ad_miniapp", "admin:miniapp"),
        "admin_tools": ("ad_tools", "admin:tools"),
        "admin_update": ("ad_update", "admin:update"),
        "admin_logs": ("ad_logs", "admin:logs"),
        "admin_buttons": ("ad_buttons", "admin:buttons"),
        "admin_texts": ("ad_texts", "admin:texts"),
        "admin_guide": ("ad_guide", "admin:guide"),
        "admin_admins": ("ad_admins", "admin:admins"),
    }

    @staticmethod
    def seed_defaults():
        now = now_ts()
        for i, k in enumerate(MenuButtonRepo.USER_KEYS):
            get_conn().execute(
                """INSERT OR IGNORE INTO menu_buttons
                   (scope, btn_key, position, is_visible, color, created_at)
                   VALUES ('user', ?, ?, 1, 'default', ?)""", (k, i, now))
        for i, k in enumerate(MenuButtonRepo.ADMIN_KEYS):
            get_conn().execute(
                """INSERT OR IGNORE INTO menu_buttons
                   (scope, btn_key, position, is_visible, color, created_at)
                   VALUES ('admin', ?, ?, 1, 'default', ?)""", (k, i, now))

    @staticmethod
    def get(scope, key):
        return get_conn().execute(
            "SELECT * FROM menu_buttons WHERE scope=? AND btn_key=?",
            (scope, key)).fetchone()

    @staticmethod
    def by_scope(scope, visible_only=True):
        q = "SELECT * FROM menu_buttons WHERE scope=?"
        if visible_only:
            q += " AND is_visible=1"
        q += " ORDER BY position, id"
        return get_conn().execute(q, (scope,)).fetchall()

    @staticmethod
    def update(scope, key, **fields):
        allowed = {"label", "color", "is_visible",
                   "emoji_id", "emoji_fb", "position"}
        f = {k: v for k, v in fields.items() if k in allowed}
        if not f:
            return
        sets = ", ".join(f"{k}=?" for k in f)
        get_conn().execute(
            f"UPDATE menu_buttons SET {sets} WHERE scope=? AND btn_key=?",
            (*f.values(), scope, key))

    @staticmethod
    def toggle_visible(scope, key):
        cur = MenuButtonRepo.get(scope, key)
        if not cur:
            return
        MenuButtonRepo.update(
            scope, key, is_visible=0 if cur["is_visible"] else 1)

    @staticmethod
    def reset(scope, key):
        get_conn().execute(
            """UPDATE menu_buttons SET label=NULL, color='default',
               emoji_id=NULL, emoji_fb=NULL, is_visible=1
               WHERE scope=? AND btn_key=?""", (scope, key))

    @staticmethod
    def set_color(scope, key, color):
        if color not in ("default", "success", "danger", "primary"):
            return
        MenuButtonRepo.update(scope, key, color=color)

    @staticmethod
    def count_all() -> int:
        r = get_conn().execute(
            "SELECT COUNT(*) AS c FROM menu_buttons").fetchone()
        return int(r["c"] or 0)

    @staticmethod
    def move(scope, key, direction):
        rows = list(MenuButtonRepo.by_scope(scope, visible_only=False))
        idx = next((i for i, r in enumerate(rows) if r["btn_key"] == key), -1)
        if idx < 0:
            return False
        try:
            cols = int(db_get(f"menu_cols_{scope}", "2"))
        except ValueError:
            cols = 2
        if direction == "left":
            new_idx = idx - 1
        elif direction == "right":
            new_idx = idx + 1
        elif direction == "up":
            new_idx = idx - cols
        elif direction == "down":
            new_idx = idx + cols
        elif direction == "top":
            new_idx = 0
        elif direction == "bottom":
            new_idx = len(rows) - 1
        else:
            return False
        if not (0 <= new_idx < len(rows)) or new_idx == idx:
            return False
        a, b = rows[idx], rows[new_idx]
        with transaction() as c:
            c.execute("UPDATE menu_buttons SET position=? WHERE id=?",
                      (b["position"], a["id"]))
            c.execute("UPDATE menu_buttons SET position=? WHERE id=?",
                      (a["position"], b["id"]))
        return True


def cleanup_menu_buttons():
    try:
        valid_user = set(MenuButtonRepo.USER_KEYS)
        valid_admin = set(MenuButtonRepo.ADMIN_KEYS)
        c = get_conn()
        rows = c.execute("SELECT scope, btn_key FROM menu_buttons").fetchall()
        for row in rows:
            s, k = row["scope"], row["btn_key"]
            if (s == "user" and k not in valid_user) or \
               (s == "admin" and k not in valid_admin):
                c.execute("DELETE FROM menu_buttons WHERE scope=? AND btn_key=?",
                          (s, k))
    except Exception as e:
        logging.warning(f"cleanup_menu_buttons failed: {e}")



__all__ = [name for name in globals() if not name.startswith("__")]
