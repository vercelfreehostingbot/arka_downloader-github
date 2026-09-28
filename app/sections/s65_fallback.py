"""Arka Downloader section: FALLBACK — پیام."""

from .s64_fallback_callback_unknown import *

# ══════════════════════════════════════════════════════════════
# FALLBACK — پیام
# ══════════════════════════════════════════════════════════════
@router.message()
async def fallback(message: Message, state: FSMContext, c: Container):
    if await state.get_state() is not None:
        return
    u = message.from_user
    if not u:
        return
    user = UserRepo.get(u.id)
    lang = user_lang(user)
    with contextlib.suppress(Exception):
        await message.answer(tr(lang, "fallback_info"))



__all__ = [name for name in globals() if not name.startswith("__")]
