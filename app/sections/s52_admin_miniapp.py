"""Arka Downloader section: ADMIN — MINIAPP."""

from .s51_announce_channel import *

# ══════════════════════════════════════════════════════════════
# ADMIN — MINIAPP
# ══════════════════════════════════════════════════════════════
async def _render_miniapp_panel(cb: CallbackQuery, c: Container):
    lang = await _admin_lang(c, cb.from_user.id)
    st = tr(lang, "active") if db_get("miniapp_enabled", "0") == "1" else tr(lang, "disabled")
    url = db_get("miniapp_url", "") or "-"
    text = tr(lang, "ad_ma_title", status=st, url=esc(url))
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=tr(lang, "ad_ma_set_url"),
                                callback_data="ma:set"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_ma_toggle"),
                                callback_data="ma:toggle"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_back"),
                                callback_data="admin:home"))
    await safe_edit(cb.message, text, b.as_markup())


@router.callback_query(F.data == "admin:miniapp")
async def cb_admin_miniapp(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    await _render_miniapp_panel(cb, c)


@router.callback_query(F.data == "ma:set")
async def cb_ma_set(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    await state.set_state(Flow.a_miniapp_url)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "ad_back"),
                             callback_data="admin:miniapp")]])
    await safe_edit(cb.message, tr(lang, "ad_ma_ask_url"), kb)


@router.message(Flow.a_miniapp_url, F.text)
async def msg_ma_url(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    val = (message.text or "").strip()
    if not val.startswith("http"):
        await message.answer("⚠️")
        return
    db_set("miniapp_url", val)
    await state.clear()
    await message.answer("✅")


@router.callback_query(F.data == "ma:toggle")
async def cb_ma_toggle(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    cur = db_get("miniapp_enabled", "0")
    db_set("miniapp_enabled", "0" if cur == "1" else "1")
    await cb.answer("✅")
    await _render_miniapp_panel(cb, c)



__all__ = [name for name in globals() if not name.startswith("__")]
