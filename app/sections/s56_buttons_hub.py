"""Arka Downloader section: BUTTONS — HUB."""

from .s55_start_emoji_sticker import *

# ══════════════════════════════════════════════════════════════
# BUTTONS — HUB
# ══════════════════════════════════════════════════════════════
@router.callback_query(F.data == "admin:buttons")
async def cb_admin_buttons(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    await state.clear()
    lang = await _admin_lang(c, cb.from_user.id)
    total = MenuButtonRepo.count_all()
    text = tr(lang, "btns_title", total=total)
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=tr(lang, "btns_user_menu"),
                                callback_data="style:menu:user"))
    b.row(InlineKeyboardButton(text=tr(lang, "btns_admin_menu"),
                                callback_data="style:menu:admin"))
    b.row(InlineKeyboardButton(text=tr(lang, "btns_custom"),
                                callback_data="admin:custom_buttons"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_back"),
                                callback_data="admin:home"))
    await safe_edit(cb.message, text, b.as_markup())



__all__ = [name for name in globals() if not name.startswith("__")]
