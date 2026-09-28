"""Arka Downloader section: ADMIN — LIMITS."""

from .s41_admin_settings import *

# ══════════════════════════════════════════════════════════════
# ADMIN — LIMITS
# ══════════════════════════════════════════════════════════════
async def _render_limits_panel(cb: CallbackQuery, c: Container,
                                tab: str = "video"):
    if tab not in ("video", "photo", "music", "adv"):
        tab = "video"
    lang = await _admin_lang(c, cb.from_user.id)
    hour = db_get("max_dl_hour", "10")
    day = db_get("max_dl_day", "50")
    concurrent = db_get("max_concurrent", "2")
    phour = db_get("max_photo_hour", "30")
    pday = db_get("max_photo_day", "200")
    mhour = db_get("max_music_hour", "30")
    mday = db_get("max_music_day", "200")
    cooldown = db_get("limit_cooldown_sec", "3")
    vip_u = "✅" if db_get("limit_vip_unlimited", "1") == "1" else "❌"
    owner_u = "✅" if db_get("limit_owner_unlimited", "1") == "1" else "❌"

    title_txt = tr(lang, "ad_lm_title")
    video_txt = f"🎬 {tr(lang, 'ad_lm_video_tab')}"
    photo_txt = f"🖼 {tr(lang, 'ad_lm_photo_tab')}"
    music_txt = f"🎵 {tr(lang, 'ad_lm_music_tab')}"
    hour_lbl = tr(lang, "ad_lm_hour")
    day_lbl = tr(lang, "ad_lm_day")
    conc_lbl = tr(lang, "ad_lm_concurrent")

    text = (
        f"{title_txt}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"{video_txt}:\n  {hour_lbl}: {hour}  |  {day_lbl}: {day}\n\n"
        f"{photo_txt}:\n  {hour_lbl}: {phour}  |  {day_lbl}: {pday}\n\n"
        f"{music_txt}:\n  {hour_lbl}: {mhour}  |  {day_lbl}: {mday}\n\n"
        f"{conc_lbl}: <b>{concurrent}</b>\n"
        f"{tr(lang, 'cooldown_lbl')}: <b>{cooldown}s</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"{tr(lang, 'vip_unlimited_lbl')}: {vip_u}  |  "
        f"{tr(lang, 'owner_unlimited_lbl')}: {owner_u}"
    )

    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text=tr(lang, "ad_lm_video_tab"),
                              callback_data="limits:tab:video"),
        InlineKeyboardButton(text=tr(lang, "ad_lm_photo_tab"),
                              callback_data="limits:tab:photo"),
        InlineKeyboardButton(text=tr(lang, "ad_lm_music_tab"),
                              callback_data="limits:tab:music"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_lm_advanced"),
                                callback_data="limits:tab:adv"))

    if tab == "video":
        b.row(InlineKeyboardButton(
            text=f"{hour_lbl}: {hour}",
            callback_data="limit:max_dl_hour:video"))
        b.row(InlineKeyboardButton(
            text=f"{day_lbl}: {day}",
            callback_data="limit:max_dl_day:video"))
        b.row(InlineKeyboardButton(
            text=f"{conc_lbl}: {concurrent}",
            callback_data="limit:max_concurrent:video"))
    elif tab == "photo":
        b.row(InlineKeyboardButton(
            text=f"{hour_lbl}: {phour}",
            callback_data="limit:max_photo_hour:photo"))
        b.row(InlineKeyboardButton(
            text=f"{day_lbl}: {pday}",
            callback_data="limit:max_photo_day:photo"))
        b.row(InlineKeyboardButton(
            text=f"{conc_lbl}: {concurrent}",
            callback_data="limit:max_concurrent:photo"))
    elif tab == "music":
        b.row(InlineKeyboardButton(
            text=f"{hour_lbl}: {mhour}",
            callback_data="limit:max_music_hour:music"))
        b.row(InlineKeyboardButton(
            text=f"{day_lbl}: {mday}",
            callback_data="limit:max_music_day:music"))
        b.row(InlineKeyboardButton(
            text=f"{conc_lbl}: {concurrent}",
            callback_data="limit:max_concurrent:music"))
    else:
        b.row(InlineKeyboardButton(
            text=f"{tr(lang, 'cooldown_lbl')}: {cooldown}s",
            callback_data="limit:limit_cooldown_sec:adv"))
        b.row(InlineKeyboardButton(
            text=f"{tr(lang, 'vip_unlimited_lbl')}: {vip_u}",
            callback_data="limit:toggle_vip:adv"))
        b.row(InlineKeyboardButton(
            text=f"{tr(lang, 'owner_unlimited_lbl')}: {owner_u}",
            callback_data="limit:toggle_owner:adv"))

    b.row(InlineKeyboardButton(text=tr(lang, "ad_back"),
                                callback_data="admin:home"))
    await safe_edit(cb.message, text, b.as_markup())


@router.callback_query(F.data == "admin:limits")
async def cb_admin_limits(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    await _render_limits_panel(cb, c, "video")


@router.callback_query(F.data.startswith("limits:tab:"))
async def cb_limits_tab(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    tab = cb.data.rsplit(":", 1)[1]
    await _render_limits_panel(cb, c, tab)


@router.callback_query(F.data.startswith("limit:toggle_"))
async def cb_limit_toggle(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    which = cb.data.rsplit(":", 1)[1]
    if which == "toggle_vip":
        cur = db_get("limit_vip_unlimited", "1")
        db_set("limit_vip_unlimited", "0" if cur == "1" else "1")
    elif which == "toggle_owner":
        cur = db_get("limit_owner_unlimited", "1")
        db_set("limit_owner_unlimited", "0" if cur == "1" else "1")
    await cb.answer("✅")
    await _render_limits_panel(cb, c, "adv")


@router.callback_query(F.data.startswith("limit:"))
async def cb_limit_value(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    parts = cb.data.split(":")
    if len(parts) != 3:
        await cb.answer()
        return
    _, setting_key, tab = parts
    valid_keys = {"max_dl_hour", "max_dl_day", "max_photo_hour",
                  "max_photo_day", "max_music_hour", "max_music_day",
                  "max_concurrent", "limit_cooldown_sec"}
    if setting_key not in valid_keys:
        await cb.answer()
        return
    if tab not in ("video", "photo", "music", "adv"):
        tab = "video"
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    await state.set_state(Flow.a_limit_value)
    await state.update_data(setting_key=setting_key, return_tab=tab)
    labels = {
        "max_dl_hour": "⏱ Video/Hour",
        "max_dl_day": "📅 Video/Day",
        "max_photo_hour": "⏱ Photo/Hour",
        "max_photo_day": "📅 Photo/Day",
        "max_music_hour": "⏱ Music/Hour",
        "max_music_day": "📅 Music/Day",
        "max_concurrent": "⚡ Concurrent",
        "limit_cooldown_sec": "⏸ Cooldown",
    }
    label = labels.get(setting_key, setting_key)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "ad_lm_back_to_limits"),
                             callback_data=safe_cb(f"limits:tab:{tab}"))]])
    await safe_edit(cb.message, tr(lang, "ad_lm_ask", label=label), kb)


@router.message(Flow.a_limit_value, F.text)
async def msg_limit_value(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    key = data.get("setting_key")
    tab = data.get("return_tab", "video")
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
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "ad_lm_back_to_limits"),
                             callback_data=safe_cb(f"limits:tab:{tab}"))]])
    await message.answer(tr(lang, "saved"), reply_markup=kb)



__all__ = [name for name in globals() if not name.startswith("__")]
