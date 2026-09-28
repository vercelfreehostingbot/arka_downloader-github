"""Arka Downloader section: KEYBOARD."""

from .s18_downloader_core import *

# ══════════════════════════════════════════════════════════════
# KEYBOARD
# ══════════════════════════════════════════════════════════════
def build_menu(scope: str, lang: str,
               is_admin_flag: bool = False) -> InlineKeyboardMarkup:
    rows = list(MenuButtonRepo.by_scope(scope, visible_only=True))
    try:
        cols = int(db_get(f"menu_cols_{scope}", "2"))
    except ValueError:
        cols = 2
    if cols not in (1, 2, 3, 4):
        cols = 2

    valid_keys = (MenuButtonRepo.USER_KEYS if scope == "user"
                  else MenuButtonRepo.ADMIN_KEYS)
    buttons = []
    for r in rows:
        key = r["btn_key"]
        if key not in valid_keys:
            continue
        if db_get(key, "1") != "1":
            continue
        if scope == "user" and key == "menu_admin" and not is_admin_flag:
            continue
        if r["label"]:
            label = r["label"]
        else:
            if scope == "user":
                dk = MenuButtonRepo.DEFAULTS_USER.get(key, ("back", ""))[0]
            else:
                dk = MenuButtonRepo.DEFAULTS_ADMIN.get(key, ("ad_back", ""))[0]
            label = tr(lang, dk)
        try:
            if r["emoji_id"] and r["emoji_fb"] and \
                    not label.startswith(r["emoji_fb"]):
                label = f"{r['emoji_fb']} {label}"
        except Exception:
            pass
        if scope == "user":
            cb_data = MenuButtonRepo.DEFAULTS_USER.get(key, ("", "noop"))[1]
        else:
            cb_data = MenuButtonRepo.DEFAULTS_ADMIN.get(key, ("", "noop"))[1]
        color = (r["color"] if r["color"] in
                 ("primary", "success", "danger") else None)
        kwargs = {"text": label[:64], "callback_data": safe_cb(cb_data)}
        if color:
            with contextlib.suppress(Exception):
                kwargs["style"] = color
        try:
            buttons.append(InlineKeyboardButton(**kwargs))
        except Exception:
            kwargs.pop("style", None)
            kwargs["text"] = label[:64]
            with contextlib.suppress(Exception):
                buttons.append(InlineKeyboardButton(**kwargs))

    if not buttons:
        return InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="•", callback_data="noop")]])
    keyboard = [buttons[i:i + cols] for i in range(0, len(buttons), cols)]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def _load_custom_buttons() -> list:
    try:
        rows = get_conn().execute(
            "SELECT * FROM custom_buttons WHERE is_active=1 "
            "ORDER BY row_order, id LIMIT 10").fetchall()
        return [{"label": str(r["label"])[:40],
                 "callback": str(r["callback"])[:60]} for r in rows]
    except Exception as e:
        logging.warning(f"load custom_buttons failed: {e}")
        return []


def _keyboard_is_admin(uid: int) -> bool:
    try:
        raw = os.getenv("OWNER_IDS", "")
        owners = {int(x.strip().lstrip("@")) for x in raw.replace(",", " ").replace(";", " ").split() if x.strip().lstrip("@").lstrip("-").isdigit()}
        if uid in owners or uid in OWNER_IDS:
            return True
        row = get_conn().execute(
            "SELECT 1 FROM extra_admins WHERE user_id=?", (uid,)
        ).fetchone()
        return bool(row)
    except Exception:
        return False

def main_menu(user: User) -> InlineKeyboardMarkup:
    is_admin_flag = _keyboard_is_admin(user.user_id)
    kb = build_menu("user", user_lang(user), is_admin_flag=is_admin_flag)

    if db_get("show_custom_buttons", "1") == "1":
        customs = _load_custom_buttons()
        if customs:
            rows = list(kb.inline_keyboard)
            for cbt in customs:
                rows.append([InlineKeyboardButton(
                    text=cbt["label"],
                    callback_data=safe_cb(cbt["callback"]))])
            kb = InlineKeyboardMarkup(inline_keyboard=rows)
    return kb


def admin_menu(lang: str) -> InlineKeyboardMarkup:
    kb = build_menu("admin", lang)
    rows = list(kb.inline_keyboard)
    rows.append([InlineKeyboardButton(text=tr(lang, "home_back"),
                                       callback_data="menu:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def quality_kb(job_id: str, lang: str, available: set = None,
               mode: str = "video") -> InlineKeyboardMarkup:
    admin_allowed = allowed_qualities()
    labels = QUALITY_LABELS.get(lang, QUALITY_LABELS["fa"])
    b = InlineKeyboardBuilder()

    if mode == "music":
        order = MUSIC_QUALITIES
        show = admin_allowed & set(MUSIC_QUALITIES)
        prefix = "mq"
    else:
        order = VIDEO_QUALITIES
        show = admin_allowed & set(VIDEO_QUALITIES)
        if available is not None and db_get("smart_quality", "1") == "1":
            show = show & (available | {"best"})
        prefix = "q"

    shown = [q for q in order if q in show]
    if not shown:
        shown = ["audio"] if mode == "music" else ["best"]

    for q in shown:
        b.row(InlineKeyboardButton(
            text=labels.get(q, q),
            callback_data=safe_cb(f"{prefix}:{job_id}:{q}")))

    b.row(InlineKeyboardButton(text=tr(lang, "cancel"),
                                callback_data=safe_cb(f"jback:{job_id}")))
    return b.as_markup()


def join_kb(channel: str, lang: str) -> InlineKeyboardMarkup:
    ch = channel.lstrip("@")
    b = InlineKeyboardBuilder()
    if ch and not ch.lstrip("-").isdigit():
        b.row(InlineKeyboardButton(text=f"📢 @{ch}", url=f"https://t.me/{ch}"))
    b.row(InlineKeyboardButton(text=tr(lang, "check_join"),
                                callback_data="check_join"))
    return b.as_markup()



__all__ = [name for name in globals() if not name.startswith("__")]
