"""Arka Downloader section: ADMIN — CHANNEL."""

from .s42_admin_limits import *

# ══════════════════════════════════════════════════════════════
# ADMIN — CHANNEL
# ══════════════════════════════════════════════════════════════
async def _render_channel_panel(cb: CallbackQuery, c: Container):
    lang = await _admin_lang(c, cb.from_user.id)
    status = (tr(lang, "active") if db_get("force_join", "0") == "1"
              else tr(lang, "disabled"))
    channel = db_get("channel_username", "") or "-"
    text = tr(lang, "ad_ch_title", status=status, channel=esc(channel))
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=tr(lang, "ad_ch_toggle"),
                                callback_data="ch:toggle"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_ch_set"),
                                callback_data="ch:set"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_back"),
                                callback_data="admin:home"))
    await safe_edit(cb.message, text, b.as_markup())


@router.callback_query(F.data == "admin:channel")
async def cb_admin_channel(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    await _render_channel_panel(cb, c)


@router.callback_query(F.data == "ch:toggle")
async def cb_ch_toggle(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    cur = db_get("force_join", "0")
    db_set("force_join", "0" if cur == "1" else "1")
    await cb.answer("✅")
    await _render_channel_panel(cb, c)


@router.callback_query(F.data == "ch:set")
async def cb_ch_set(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    await state.set_state(Flow.a_channel)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "ad_back"),
                             callback_data="admin:channel")]])
    await safe_edit(cb.message, tr(lang, "ad_ch_ask"), kb)


@router.message(Flow.a_channel, F.text)
async def msg_channel(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    val = (message.text or "").strip()
    lang = await _admin_lang(c, message.from_user.id)
    if not val:
        await message.answer(tr(lang, "empty"))
        return
    if not val.startswith("@") and not val.lstrip("-").isdigit():
        val = "@" + val
    db_set("channel_username", val)
    await state.clear()
    await message.answer(tr(lang, "saved"))



__all__ = [name for name in globals() if not name.startswith("__")]
