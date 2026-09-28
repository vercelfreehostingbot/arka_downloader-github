"""Arka Downloader section: FALLBACK — CALLBACK ناشناخته."""

from .s63_mini_app_webappdata import *

# ══════════════════════════════════════════════════════════════
# FALLBACK — CALLBACK ناشناخته
# ══════════════════════════════════════════════════════════════
@router.callback_query()
async def cb_unknown(cb: CallbackQuery, c: Container):
    user = UserRepo.get(cb.from_user.id)
    lang = user_lang(user)
    with contextlib.suppress(Exception):
        await cb.answer(tr(lang, "button_inactive"), show_alert=False)
    if not user:
        return
    with contextlib.suppress(Exception):
        await cb.message.answer(
            tr(lang, "fallback_info"),
            reply_markup=main_menu(user))



__all__ = [name for name in globals() if not name.startswith("__")]
