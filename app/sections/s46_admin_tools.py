"""Arka Downloader section: ADMIN — TOOLS."""

from .s45_admin_logs import *

# ══════════════════════════════════════════════════════════════
# ADMIN — TOOLS
# ══════════════════════════════════════════════════════════════
@router.callback_query(F.data == "admin:tools")
async def cb_admin_tools(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    try:
        db_size = fmt_bytes(DB_PATH.stat().st_size)
    except Exception:
        db_size = "—"
    r = get_conn().execute("SELECT COUNT(*) AS c FROM backups").fetchone()
    backups = int(r["c"] or 0)
    text = tr(lang, "ad_tools_title", db_size=db_size, backups=backups)
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=tr(lang, "ad_tools_backup"),
                                callback_data="tools:backup"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_tools_vacuum"),
                                callback_data="tools:vacuum"))
    b.row(
        InlineKeyboardButton(text=tr(lang, "ad_tools_clear_logs"),
                              callback_data="tools:clear_logs"),
        InlineKeyboardButton(text=tr(lang, "ad_tools_clear_dl"),
                              callback_data="tools:clear_dl"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_tools_auto_backup"),
                                callback_data="tools:auto_backup"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_back"),
                                callback_data="admin:home"))
    await safe_edit(cb.message, text, b.as_markup())


@router.callback_query(F.data == "tools:backup")
async def cb_tools_backup(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    try:
        name = f"backup_{fmt_dt_short(now_ts())}.db"
        dst = BACKUP_DIR / name
        checkpoint_db()
        shutil.copy2(DB_PATH, dst)
        size = dst.stat().st_size
        get_conn().execute(
            "INSERT INTO backups(path, size, created_at) VALUES (?, ?, ?)",
            (str(dst), size, now_ts()))
        db_log(cb.from_user.id, "backup", name)
        await c.bot.send_document(chat_id=cb.from_user.id,
                                    document=FSInputFile(str(dst)),
                                    caption=tr(lang, "ad_tools_backup_ok", name=name))
    except Exception as e:
        with contextlib.suppress(Exception):
            await cb.message.answer(f"❌ {esc(str(e))}")


@router.callback_query(F.data == "tools:vacuum")
async def cb_tools_vacuum(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer("⚡", show_alert=True)
    with contextlib.suppress(Exception):
        get_conn().execute("VACUUM")


@router.callback_query(F.data == "tools:clear_logs")
async def cb_tools_clear_logs(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    n = 0
    for f in LOG_DIR.glob("*.log*"):
        with contextlib.suppress(Exception):
            f.unlink()
            n += 1
    await cb.answer(f"🗑 {n}", show_alert=True)


@router.callback_query(F.data == "tools:clear_dl")
async def cb_tools_clear_dl(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    n = 0
    if DOWNLOAD_DIR.exists():
        for d in DOWNLOAD_DIR.iterdir():
            with contextlib.suppress(Exception):
                if d.is_dir():
                    shutil.rmtree(d, ignore_errors=True)
                else:
                    d.unlink()
                n += 1
    await cb.answer(f"🧹 {n}", show_alert=True)


@router.callback_query(F.data == "tools:auto_backup")
async def cb_auto_backup_menu(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    enabled = db_get("auto_backup_enabled", "0") == "1"
    hours = db_get("auto_backup_hours", "24")
    try:
        last_ts = float(db_get("auto_backup_last", "0") or "0")
    except ValueError:
        last_ts = 0.0
    last_str = fmt_time(last_ts) if last_ts else "—"
    status = tr(lang, "active") if enabled else tr(lang, "disabled")
    text = tr(lang, "ad_auto_backup_title", status=status, hours=hours,
              last=last_str)
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=tr(lang, "ad_auto_backup_toggle"),
                                callback_data="auto_backup:toggle"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_auto_backup_hours"),
                                callback_data="auto_backup:hours"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_back"),
                                callback_data="admin:tools"))
    await safe_edit(cb.message, text, b.as_markup())


@router.callback_query(F.data == "auto_backup:toggle")
async def cb_auto_backup_toggle(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    cur = db_get("auto_backup_enabled", "0")
    db_set("auto_backup_enabled", "0" if cur == "1" else "1")
    await cb.answer("✅")
    await cb_auto_backup_menu(cb, c)


@router.callback_query(F.data == "auto_backup:hours")
async def cb_auto_backup_hours(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    await state.set_state(Flow.a_auto_backup_hours)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "ad_back"),
                             callback_data="tools:auto_backup")]])
    await safe_edit(cb.message, tr(lang, "ad_auto_backup_ask"), kb)


@router.message(Flow.a_auto_backup_hours, F.text)
async def msg_auto_backup_hours(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    val = (message.text or "").strip()
    if not val.replace(".", "").isdigit():
        await message.answer("⚠️")
        return
    db_set("auto_backup_hours", val)
    await state.clear()
    await message.answer("✅")



__all__ = [name for name in globals() if not name.startswith("__")]
