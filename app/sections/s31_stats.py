"""Arka Downloader section: STATS."""

from .s30_favorites import *

# ══════════════════════════════════════════════════════════════
# STATS
# ══════════════════════════════════════════════════════════════
@router.callback_query(F.data == "menu:stats")
async def cb_stats(cb: CallbackQuery, c: Container):
    await cb.answer()
    user = UserRepo.get(cb.from_user.id)
    if not user:
        return
    lang = user_lang(user)
    active = UserRepo.active_jobs(user.user_id)
    tier = tr(lang, "tier_vip") if user.is_vip else tr(lang, "tier_normal")
    text = tr(lang, "stats_title",
              name=esc(user.first_name or "User"), uid=user.user_id,
              total=user.downloads, success=user.success_dl,
              failed=user.failed_dl, active=active, tier=tier)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "back"), callback_data="menu:home")]])
    await safe_edit(cb.message, text, kb)



__all__ = [name for name in globals() if not name.startswith("__")]
