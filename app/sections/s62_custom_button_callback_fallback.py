"""Arka Downloader section: CUSTOM BUTTON CALLBACK FALLBACK."""

from .s61_sub_admins import *

# ══════════════════════════════════════════════════════════════
# CUSTOM BUTTON CALLBACK FALLBACK
# ══════════════════════════════════════════════════════════════
@router.callback_query(F.data.startswith("custom:"))
async def cb_custom_button(cb: CallbackQuery, c: Container):
    await cb.answer("✅")
    user = UserRepo.get(cb.from_user.id)
    lang = user_lang(user)
    with contextlib.suppress(Exception):
        await cb.message.answer(tr(lang, "fallback_info"),
                                 reply_markup=main_menu(user))



__all__ = [name for name in globals() if not name.startswith("__")]
