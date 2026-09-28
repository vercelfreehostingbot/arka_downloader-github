"""Arka Downloader section: MINI APP — WebAppData."""

from .s62_custom_button_callback_fallback import *

# ══════════════════════════════════════════════════════════════
# MINI APP — WebAppData
# ══════════════════════════════════════════════════════════════
@router.message(F.web_app_data)
async def handle_web_app_data(message: Message, c: Container):
    user = UserRepo.get(message.from_user.id)
    if not user:
        return
    lang = user_lang(user)
    data = message.web_app_data.data if message.web_app_data else ""
    logging.info(f"web_app_data from {user.user_id}: {data[:200]}")
    with contextlib.suppress(Exception):
        await message.answer(
            f"{tr(lang, 'received_data')}\n<code>{esc(data[:500])}</code>")



__all__ = [name for name in globals() if not name.startswith("__")]
