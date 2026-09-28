"""Arka Downloader section: HELP."""

from .s32_support import *

# ══════════════════════════════════════════════════════════════
# HELP
# ══════════════════════════════════════════════════════════════
@router.callback_query(F.data == "menu:help")
async def cb_help(cb: CallbackQuery, c: Container):
    await cb.answer()
    user = UserRepo.get(cb.from_user.id)
    lang = user_lang(user)
    custom = db_get(f"guide_{lang}", "") or db_get("custom_text_help_text", "")
    text = custom if custom else tr(lang, "help_text")
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "back"), callback_data="menu:home")]])
    await safe_edit(cb.message, text, kb)



__all__ = [name for name in globals() if not name.startswith("__")]
