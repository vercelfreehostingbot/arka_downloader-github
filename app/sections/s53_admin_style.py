"""Arka Downloader section: ADMIN — STYLE."""

from .s52_admin_miniapp import *

# ══════════════════════════════════════════════════════════════
# ADMIN — STYLE
# ══════════════════════════════════════════════════════════════
async def _render_style_panel(cb: CallbackQuery, c: Container):
    lang = await _admin_lang(c, cb.from_user.id)
    premium_yn = "✅" if db_get("premium_emoji_enabled", "1") == "1" else "❌"
    map_count = emoji_map_count()
    text = tr(lang, "style_title", premium=premium_yn,
              map_count=map_count, total_btns=MenuButtonRepo.count_all())
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(
        text=f"{tr(lang, 'style_emoji_map')} ({map_count})",
        callback_data="style:emoji_map"))
    b.row(InlineKeyboardButton(
        text=f"{tr(lang, 'style_premium_toggle')}: {premium_yn}",
        callback_data="style:premium_toggle"))
    b.row(InlineKeyboardButton(text=tr(lang, "style_start_emoji"),
                                callback_data="style:start_emoji"))
    b.row(InlineKeyboardButton(text=tr(lang, "style_start_sticker"),
                                callback_data="style:start_sticker"))
    b.row(InlineKeyboardButton(text=tr(lang, "style_reset_all"),
                                callback_data="style:reset_colors"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_back"),
                                callback_data="admin:home"))
    await safe_edit(cb.message, text, b.as_markup())


@router.callback_query(F.data == "admin:style")
async def cb_admin_style(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    await state.clear()
    await _render_style_panel(cb, c)


@router.callback_query(F.data == "style:premium_toggle")
async def cb_style_premium_toggle(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    cur = db_get("premium_emoji_enabled", "1")
    db_set("premium_emoji_enabled", "0" if cur == "1" else "1")
    invalidate_emoji_cache()
    await cb.answer("✅")
    await _render_style_panel(cb, c)


@router.callback_query(F.data == "style:reset_colors")
async def cb_style_reset_colors(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    get_conn().execute("UPDATE menu_buttons SET color='default'")
    await cb.answer("✅", show_alert=True)
    await _render_style_panel(cb, c)



__all__ = [name for name in globals() if not name.startswith("__")]
