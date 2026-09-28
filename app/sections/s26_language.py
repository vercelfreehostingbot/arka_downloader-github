"""Arka Downloader section: LANGUAGE."""

from .s25_start_main import *

# ══════════════════════════════════════════════════════════════
# LANGUAGE
# ══════════════════════════════════════════════════════════════
@router.callback_query(F.data.startswith("lang:set:"))
async def cb_lang_set(cb: CallbackQuery, c: Container):
    new_lang = cb.data.split(":")[-1]
    if new_lang not in ("fa", "en"):
        await cb.answer()
        return
    user = UserRepo.get(cb.from_user.id)
    if not user:
        await cb.answer()
        return
    if user.lang == new_lang and user_has_chosen_lang(user.user_id):
        await cb.answer(tr(user_lang(user), "lang_same"), show_alert=True)
        return
    mark_lang_chosen(user.user_id, new_lang)
    user = UserRepo.get(user.user_id)
    await cb.answer(tr(user_lang(user), "saved"))
    await send_home(cb, user, edit=True)



__all__ = [name for name in globals() if not name.startswith("__")]
