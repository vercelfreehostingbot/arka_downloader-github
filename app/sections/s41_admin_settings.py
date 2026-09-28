"""Arka Downloader section: ADMIN — SETTINGS."""

from .s40_admin_tickets import *

# ══════════════════════════════════════════════════════════════
# ADMIN — SETTINGS
# ══════════════════════════════════════════════════════════════
async def _render_settings_panel(cb: CallbackQuery, c: Container):
    lang = await _admin_lang(c, cb.from_user.id)
    thumb = "✅" if db_get("send_thumbnail", "1") == "1" else "❌"
    subs = "✅" if db_get("download_subtitles", "0") == "1" else "❌"
    maint = "✅" if db_get("maintenance", "0") == "1" else "❌"
    photo = "✅" if db_get("photo_download_enabled", "1") == "1" else "❌"
    video = "✅" if db_get("video_download_enabled", "1") == "1" else "❌"
    compress = "✅" if db_get("compress_large_photos", "1") == "1" else "❌"
    smart = "✅" if db_get("smart_quality", "1") == "1" else "❌"
    text = tr(lang, "ad_set_title",
              maxsize=db_get("max_file_size_mb", "2048"),
              delay=db_get("delete_delay", "60"),
              retry=db_get("max_retries", "2"),
              thumb=thumb, subs=subs, maint=maint,
              photo=photo, video=video, compress=compress)
    text += f"\n{tr(lang, 'smart_quality_lbl')}: {smart}"
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text=tr(lang, "ad_set_maxsize"),
                              callback_data="set:maxsize"),
        InlineKeyboardButton(text=tr(lang, "ad_set_delay"),
                              callback_data="set:delay"))
    b.row(
        InlineKeyboardButton(text=tr(lang, "ad_set_retry"),
                              callback_data="set:retry"),
        InlineKeyboardButton(text=tr(lang, "ad_set_thumb"),
                              callback_data="set:thumb"))
    b.row(
        InlineKeyboardButton(text=tr(lang, "ad_set_subs"),
                              callback_data="set:subs"),
        InlineKeyboardButton(text=tr(lang, "ad_set_maint"),
                              callback_data="set:maint"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_set_compress"),
                                callback_data="set:compress"))
    b.row(InlineKeyboardButton(
        text=f"{tr(lang, 'smart_quality_lbl')}: {smart}",
        callback_data="set:smart"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_set_maint_text"),
                                callback_data="set:maint_text"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_set_dl_types"),
                                callback_data="admin:dl_types"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_back"),
                                callback_data="admin:home"))
    await safe_edit(cb.message, text, b.as_markup())


@router.callback_query(F.data == "admin:settings")
async def cb_admin_settings(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    await _render_settings_panel(cb, c)


@router.callback_query(F.data == "set:smart")
async def cb_set_smart(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    cur = db_get("smart_quality", "1")
    db_set("smart_quality", "0" if cur == "1" else "1")
    await cb.answer("✅")
    await _render_settings_panel(cb, c)


@router.callback_query(F.data == "set:thumb")
async def cb_set_thumb(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    cur = db_get("send_thumbnail", "1")
    db_set("send_thumbnail", "0" if cur == "1" else "1")
    await cb.answer("✅")
    await _render_settings_panel(cb, c)


@router.callback_query(F.data == "set:subs")
async def cb_set_subs(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    cur = db_get("download_subtitles", "0")
    db_set("download_subtitles", "0" if cur == "1" else "1")
    await cb.answer("✅")
    await _render_settings_panel(cb, c)


@router.callback_query(F.data == "set:maint")
async def cb_set_maint(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    cur = db_get("maintenance", "0")
    db_set("maintenance", "0" if cur == "1" else "1")
    await cb.answer("✅")
    await _render_settings_panel(cb, c)


@router.callback_query(F.data == "set:compress")
async def cb_set_compress(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    cur = db_get("compress_large_photos", "1")
    db_set("compress_large_photos", "0" if cur == "1" else "1")
    await cb.answer("✅")
    await _render_settings_panel(cb, c)


@router.callback_query(F.data == "set:maint_text")
async def cb_set_maint_text(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    await state.set_state(Flow.a_setting_maint)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "ad_back"),
                             callback_data="admin:settings")]])
    await safe_edit(cb.message, tr(lang, "ad_set_ask_maint"), kb)


@router.message(Flow.a_setting_maint, F.text)
async def msg_set_maint(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    val = (message.text or "").strip()
    lang = await _admin_lang(c, message.from_user.id)
    if not val:
        await message.answer(tr(lang, "empty"))
        return
    db_set("maintenance_text", val)
    await state.clear()
    await message.answer(tr(lang, "saved"))


@router.callback_query(F.data.startswith("set:"))
async def cb_set_value(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    key = cb.data.split(":", 1)[1]
    mapping = {"maxsize": ("max_file_size_mb", "ad_set_maxsize"),
               "delay": ("delete_delay", "ad_set_delay"),
               "retry": ("max_retries", "ad_set_retry")}
    if key not in mapping:
        return
    await cb.answer()
    setting_key, label_key = mapping[key]
    lang = await _admin_lang(c, cb.from_user.id)
    await state.set_state(Flow.a_setting_value)
    await state.update_data(setting_key=setting_key)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "ad_back"),
                             callback_data="admin:settings")]])
    await safe_edit(cb.message,
                    tr(lang, "ad_set_ask", label=tr(lang, label_key)), kb)


@router.message(Flow.a_setting_value, F.text)
async def msg_set_value(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    key = data.get("setting_key")
    lang = await _admin_lang(c, message.from_user.id)
    if not key:
        await state.clear()
        return
    val = (message.text or "").strip()
    if not val.isdigit():
        await message.answer(tr(lang, "invalid"))
        return
    db_set(key, val)
    await state.clear()
    await message.answer(tr(lang, "saved"))



__all__ = [name for name in globals() if not name.startswith("__")]
