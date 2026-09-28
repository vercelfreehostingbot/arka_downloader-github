"""Arka Downloader section: ADMIN — LOGS."""

from .s44_admin_quality import *

# ══════════════════════════════════════════════════════════════
# ADMIN — LOGS
# ══════════════════════════════════════════════════════════════
@router.callback_query(F.data == "admin:logs")
async def cb_admin_logs(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    rows = get_conn().execute(
        "SELECT * FROM logs ORDER BY created_at DESC LIMIT 20").fetchall()
    text = tr(lang, "ad_logs_title") + "\n\n"
    if not rows:
        text += tr(lang, "ad_logs_empty")
    else:
        for r in rows:
            text += (f"<code>{r['admin_id']}</code> | {esc(r['action'])} | "
                     f"{esc(str(r['details'] or '')[:50])} | "
                     f"{fmt_time(r['created_at'])}\n")
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "ad_back"),
                             callback_data="admin:home")]])
    await safe_edit(cb.message, text, kb)



__all__ = [name for name in globals() if not name.startswith("__")]
