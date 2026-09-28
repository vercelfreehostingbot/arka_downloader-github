"""Arka Downloader section: DATABASE."""

from .s08_logging import *

# ══════════════════════════════════════════════════════════════
# DATABASE
# ══════════════════════════════════════════════════════════════
_local = threading.local()


def _make_conn():
    c = sqlite3.connect(str(DB_PATH), timeout=30,
                        isolation_level=None, check_same_thread=False)
    c.row_factory = sqlite3.Row
    with contextlib.suppress(Exception):
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA busy_timeout=10000")
    return c


def get_conn():
    c = getattr(_local, "conn", None)
    if c is None:
        c = _make_conn()
        _local.conn = c
    return c


def close_conn():
    c = getattr(_local, "conn", None)
    if c is not None:
        with contextlib.suppress(Exception):
            c.close()
        _local.conn = None


@contextmanager
def transaction():
    c = get_conn()
    try:
        c.execute("BEGIN IMMEDIATE")
        yield c
        c.execute("COMMIT")
    except Exception:
        with contextlib.suppress(Exception):
            c.execute("ROLLBACK")
        raise


MIGRATIONS = ["""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    chat_id INTEGER NOT NULL,
    username TEXT,
    first_name TEXT,
    downloads INTEGER NOT NULL DEFAULT 0,
    success_dl INTEGER NOT NULL DEFAULT 0,
    failed_dl INTEGER NOT NULL DEFAULT 0,
    is_blocked INTEGER NOT NULL DEFAULT 0,
    is_vip INTEGER NOT NULL DEFAULT 0,
    lang TEXT NOT NULL DEFAULT 'fa',
    lang_chosen INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    chat_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    title TEXT,
    quality TEXT NOT NULL DEFAULT 'best',
    duration INTEGER NOT NULL DEFAULT 0,
    filesize INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'queued',
    progress REAL NOT NULL DEFAULT 0,
    speed TEXT, eta TEXT, file_path TEXT, thumbnail TEXT,
    msg_id INTEGER, notice_msg_id INTEGER,
    delete_at REAL, error TEXT,
    created_at REAL NOT NULL,
    started_at REAL, finished_at REAL
);
CREATE INDEX IF NOT EXISTS idx_jobs_user ON jobs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    answer TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    created_at REAL NOT NULL,
    answered_at REAL
);
CREATE TABLE IF NOT EXISTS favorites (
    user_id INTEGER NOT NULL,
    job_id TEXT NOT NULL,
    created_at REAL NOT NULL,
    PRIMARY KEY (user_id, job_id)
);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS custom_texts (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS rate_limits (
    user_id INTEGER NOT NULL,
    mode TEXT NOT NULL DEFAULT 'video',
    hour_start REAL NOT NULL, hour_count INTEGER NOT NULL DEFAULT 0,
    day_start REAL NOT NULL, day_count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, mode)
);
CREATE TABLE IF NOT EXISTS menu_buttons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope TEXT NOT NULL, btn_key TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0,
    is_visible INTEGER DEFAULT 1,
    color TEXT DEFAULT 'default',
    label TEXT, emoji_id TEXT, emoji_fb TEXT,
    created_at REAL NOT NULL,
    UNIQUE(scope, btn_key)
);
CREATE TABLE IF NOT EXISTS emoji_map (
    normal_emoji TEXT PRIMARY KEY,
    premium_id TEXT NOT NULL,
    fallback_emoji TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS custom_buttons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL, callback TEXT NOT NULL,
    row_order INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS extra_admins (
    user_id INTEGER PRIMARY KEY,
    added_by INTEGER NOT NULL,
    added_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER, action TEXT NOT NULL,
    details TEXT, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS backups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL, size INTEGER NOT NULL,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS update_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL, prev_version TEXT,
    applied INTEGER NOT NULL DEFAULT 1,
    backup_path TEXT, note TEXT,
    created_at REAL NOT NULL
);
"""]


DEFAULT_SETTINGS = {
    "max_file_size_mb": "2048",
    "max_photo_size_mb": "2048",
    "max_dl_hour": "10",
    "max_dl_day": "50",
    "max_concurrent": "2",
    "delete_delay": "60",
    "max_retries": "2",
    "maintenance": "0",
    "maintenance_text": "🔧 ربات در حال تعمیر است.",
    "allowed_quality": (
        "best,4320p,2160p,1440p,1080p,720p,480p,360p,"
        "audio_best,audio,audio_320,audio_128"
    ),
    "broadcast_delay": "0.05",
    "send_thumbnail": "1",
    "download_subtitles": "0",
    "force_join": "0",
    "channel_username": "",
    "premium_emoji_enabled": "1",
    "start_emoji_id": "",
    "start_emoji_fb": "✨",
    "start_emoji_kind": "",
    "start_sticker_file_id": "",
    "start_sticker_enabled": "1",
    "bot_version": FILE_VERSION,
    "prev_version": "",
    "menu_cols_user": "2",
    "menu_cols_admin": "2",
    "menu_download": "1", "menu_history": "1", "menu_favs": "1",
    "menu_stats": "1", "menu_support": "1", "menu_help": "1",
    "menu_admin": "1",
    "miniapp_url": "", "miniapp_enabled": "0",
    "auto_backup_enabled": "0",
    "auto_backup_hours": "24",
    "auto_backup_last": "0",
    "show_custom_buttons": "1",
    "photo_download_enabled": "1",
    "video_download_enabled": "1",
    "music_download_enabled": "1",
    "max_photo_hour": "30",
    "max_photo_day": "200",
    "max_music_hour": "30",
    "max_music_day": "200",
    "music_send_as_audio": "1",
    "keep_state_after_download": "1",
    "photo_delete_delay": "60",
    "compress_large_photos": "1",
    "announce_enabled": "0",
    "announce_audience": "all",
    "announce_pin": "0",
    "announce_silent": "0",
    "announce_preview": "1",
    "announce_schedule": "",
    "announce_schedule_ts": "0",
    "announce_last_ts": "0",
    "announce_total_sent": "0",
    "announce_total_failed": "0",
    "announce_auto_delete": "0",
    "announce_delete_after": "3600",
    "announce_channel_id": "",
    "announce_channel_enabled": "0",
    "announce_channel_pin": "0",
    "announce_channel_silent": "0",
    "announce_channel_last_ts": "0",
    "announce_channel_total": "0",
    "limit_vip_unlimited": "1",
    "limit_owner_unlimited": "1",
    "limit_cooldown_sec": "3",
    "smart_quality": "1",
    "migration_v530_quality": "0",
    "migration_v530_lang_chosen": "0",
}


def _table_exists(table: str) -> bool:
    try:
        r = get_conn().execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,)).fetchone()
        return bool(r)
    except Exception:
        return False


def ensure_columns(table: str, columns: dict):
    try:
        if not _table_exists(table):
            return
        cur = get_conn().execute(f"PRAGMA table_info({table})")
        existing = {row["name"] for row in cur.fetchall()}
        for col_name, col_def in columns.items():
            if col_name not in existing:
                with contextlib.suppress(Exception):
                    get_conn().execute(
                        f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}")
    except Exception as e:
        logging.warning(f"ensure_columns({table}) failed: {e}")


def run_migrations():
    c = get_conn()
    for sql in MIGRATIONS:
        c.executescript(sql)

    with contextlib.suppress(Exception):
        cols = {r["name"] for r in c.execute(
            "PRAGMA table_info(rate_limits)").fetchall()}
        if "mode" not in cols:
            c.execute("ALTER TABLE rate_limits RENAME TO rate_limits_old")
            c.execute("""CREATE TABLE rate_limits (
                user_id INTEGER NOT NULL,
                mode TEXT NOT NULL DEFAULT 'video',
                hour_start REAL NOT NULL, hour_count INTEGER NOT NULL DEFAULT 0,
                day_start REAL NOT NULL, day_count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, mode))""")
            c.execute("""INSERT INTO rate_limits
                (user_id, mode, hour_start, hour_count, day_start, day_count)
                SELECT user_id, 'video', hour_start, hour_count,
                       day_start, day_count FROM rate_limits_old""")
            c.execute("DROP TABLE rate_limits_old")

    for k, v in DEFAULT_SETTINGS.items():
        c.execute("INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)",
                  (k, v))
    db_set("bot_version", FILE_VERSION)

    with contextlib.suppress(Exception):
        if db_get("migration_v530_quality", "0") != "1":
            cur_val = db_get("allowed_quality", "")
            if cur_val:
                parts = {x.strip() for x in cur_val.split(",") if x.strip()}
                for q in ("audio_best", "audio", "audio_320", "audio_128"):
                    parts.add(q)
                db_set("allowed_quality", ",".join(sorted(parts)))
            db_set("migration_v530_quality", "1")

    with contextlib.suppress(Exception):
        if db_get("migration_v530_lang_chosen", "0") != "1":
            c.execute("UPDATE users SET lang_chosen=1")
            db_set("migration_v530_lang_chosen", "1")

    with contextlib.suppress(Exception):
        c.execute("DELETE FROM menu_buttons WHERE btn_key='menu_lang'")

    ensure_columns("users", {
        "chat_id": "INTEGER NOT NULL DEFAULT 0",
        "username": "TEXT", "first_name": "TEXT",
        "downloads": "INTEGER NOT NULL DEFAULT 0",
        "success_dl": "INTEGER NOT NULL DEFAULT 0",
        "failed_dl": "INTEGER NOT NULL DEFAULT 0",
        "is_blocked": "INTEGER NOT NULL DEFAULT 0",
        "is_vip": "INTEGER NOT NULL DEFAULT 0",
        "lang": "TEXT NOT NULL DEFAULT 'fa'",
        "lang_chosen": "INTEGER NOT NULL DEFAULT 0",
        "created_at": "REAL NOT NULL DEFAULT 0",
        "updated_at": "REAL NOT NULL DEFAULT 0",
    })
    ensure_columns("jobs", {
        "user_id": "INTEGER NOT NULL DEFAULT 0",
        "chat_id": "INTEGER NOT NULL DEFAULT 0",
        "url": "TEXT NOT NULL DEFAULT ''",
        "title": "TEXT", "quality": "TEXT NOT NULL DEFAULT 'best'",
        "duration": "INTEGER NOT NULL DEFAULT 0",
        "filesize": "INTEGER NOT NULL DEFAULT 0",
        "status": "TEXT NOT NULL DEFAULT 'queued'",
        "progress": "REAL NOT NULL DEFAULT 0",
        "speed": "TEXT", "eta": "TEXT",
        "file_path": "TEXT", "thumbnail": "TEXT",
        "msg_id": "INTEGER", "notice_msg_id": "INTEGER",
        "delete_at": "REAL", "error": "TEXT",
        "created_at": "REAL NOT NULL DEFAULT 0",
        "started_at": "REAL", "finished_at": "REAL",
    })


def db_get(key: str, default: str = "") -> str:
    r = get_conn().execute(
        "SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return str(r["value"]) if r else default


def db_set(key: str, value):
    get_conn().execute(
        "INSERT INTO settings(key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value)))


def db_log(admin_id: int, action: str, details: str = ""):
    with contextlib.suppress(Exception):
        get_conn().execute(
            "INSERT INTO logs(admin_id, action, details, created_at) "
            "VALUES (?, ?, ?, ?)", (admin_id, action, details, now_ts()))


def checkpoint_db():
    with contextlib.suppress(Exception):
        get_conn().execute("PRAGMA wal_checkpoint(TRUNCATE)")



__all__ = [name for name in globals() if not name.startswith("__")]
