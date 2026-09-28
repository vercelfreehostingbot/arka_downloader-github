"""Arka Downloader section: ADMIN — MAIN."""

from .s34_admin_helpers import *

# ══════════════════════════════════════════════════════════════
# ADMIN — MAIN
# ══════════════════════════════════════════════════════════════
@router.callback_query(F.data == "admin:home")
async def cb_admin_home(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    await state.clear()
    lang = await _admin_lang(c, cb.from_user.id)
    await safe_edit(cb.message, tr(lang, "ad_title"), admin_menu(lang))


@router.callback_query(F.data == "admin:stats")
async def cb_admin_stats(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    us = UserRepo.stats()
    js = JobRepo.totals()
    active = JobRepo.count_active()
    try:
        db_size = fmt_bytes(DB_PATH.stat().st_size)
    except Exception:
        db_size = "—"
    text = tr(lang, "ad_rs_title", users=us["total"], vip=us["vip"],
              blocked=us["blocked"], total=js["total"],
              success=js["completed"], failed=js["failed"], active=active,
              tickets=TicketRepo.open_count(), db_size=db_size)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=tr(lang, "refresh"),
                              callback_data="admin:stats")],
        [InlineKeyboardButton(text=tr(lang, "ad_back"),
                              callback_data="admin:home")]])
    await safe_edit(cb.message, text, kb)



__all__ = [name for name in globals() if not name.startswith("__")]
