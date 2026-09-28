"""Arka Downloader section: START EMOJI / STICKER."""

from .s54_emoji_map import *

# ══════════════════════════════════════════════════════════════
# START EMOJI / STICKER
# ══════════════════════════════════════════════════════════════
@router.callback_query(F.data == "style:start_emoji")
async def cb_style_start_emoji(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    await state.set_state(Flow.start_emoji)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "cancel"),
                             callback_data="admin:style")]])
    await safe_edit(cb.message, tr(lang, "start_emoji_title"), kb)


@router.message(Flow.start_emoji)
async def msg_start_emoji(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    prems = extract_premium_emojis(message)
    if prems:
        eid, fb = prems[0]
        db_set("start_emoji_id", eid)
        db_set("start_emoji_fb", fb)
        db_set("start_emoji_kind", "premium")
        await state.clear()
        await message.answer("✅")
        return
    txt = message.text or message.caption or ""
    norms = extract_normal_emojis(txt)
    if norms:
        db_set("start_emoji_id", norms[0])
        db_set("start_emoji_fb", norms[0])
        db_set("start_emoji_kind", "normal")
        await state.clear()
        await message.answer("✅")
        return
    await message.answer("⚠️")


def _build_sticker_panel(lang):
    sid = db_get("start_sticker_file_id", "")
    enabled = db_get("start_sticker_enabled", "1") == "1"
    status = tr(lang, "active") if enabled else tr(lang, "disabled")
    text = tr(lang, "start_sticker_title", status=status)
    if sid:
        text += f"\n\n📎 <code>{sid[:60]}...</code>"
    else:
        text += f"\n\n{tr(lang, 'start_sticker_not_set')}"
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=tr(lang, "toggle"),
                                callback_data="sticker:toggle"))
    b.row(InlineKeyboardButton(text=tr(lang, "delete"),
                                callback_data="sticker:delete"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_back"),
                                callback_data="admin:style"))
    return text, b.as_markup()


@router.callback_query(F.data == "style:start_sticker")
async def cb_style_start_sticker(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    await state.set_state(Flow.start_sticker)
    text, kb = _build_sticker_panel(lang)
    await safe_edit(cb.message, text, kb)


@router.message(Flow.start_sticker, F.sticker)
async def msg_start_sticker(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    db_set("start_sticker_file_id", message.sticker.file_id)
    db_set("start_sticker_enabled", "1")
    await state.clear()
    await message.answer("✅")


@router.message(Flow.start_sticker)
async def msg_start_sticker_bad(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    await message.answer("⚠️")


@router.callback_query(F.data == "sticker:toggle")
async def cb_sticker_toggle(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    cur = db_get("start_sticker_enabled", "1")
    db_set("start_sticker_enabled", "0" if cur == "1" else "1")
    await cb.answer("✅")
    lang = await _admin_lang(c, cb.from_user.id)
    await state.set_state(Flow.start_sticker)
    text, kb = _build_sticker_panel(lang)
    await safe_edit(cb.message, text, kb)


@router.callback_query(F.data == "sticker:delete")
async def cb_sticker_delete(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    db_set("start_sticker_file_id", "")
    await cb.answer("🗑", show_alert=True)
    await _render_style_panel(cb, c)



__all__ = [name for name in globals() if not name.startswith("__")]
