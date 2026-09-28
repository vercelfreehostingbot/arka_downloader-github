"""Arka Downloader section: ADMIN — ANNOUNCE MAIN."""

from .s48_announce_helpers import *

# ══════════════════════════════════════════════════════════════
# ADMIN — ANNOUNCE MAIN
# ══════════════════════════════════════════════════════════════
@router.callback_query(F.data == "admin:announce")
async def cb_admin_announce(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    await state.clear()
    lang = await _admin_lang(c, cb.from_user.id)
    st = tr(lang, "active") if db_get("announce_enabled", "0") == "1" else tr(lang, "disabled")

    a = db_get("announce_audience", "all")
    a_label = audience_label(lang, a)
    count = _audience_count()

    try:
        ts_total = int(db_get("announce_total_sent", "0") or "0")
        tf_total = int(db_get("announce_total_failed", "0") or "0")
    except Exception:
        ts_total = tf_total = 0

    ch_id = db_get("announce_channel_id", "") or "—"
    try:
        ch_total = int(db_get("announce_channel_total", "0") or "0")
    except Exception:
        ch_total = 0

    text = tr(lang, "an_main_title", status=st, audience=a_label,
              count=count, sent=ts_total, failed=tf_total,
              channel=esc(ch_id), ch_total=ch_total)

    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text=tr(lang, "an_btn_users"),
                              callback_data="an:users_menu"),
        InlineKeyboardButton(text=tr(lang, "an_btn_channel"),
                              callback_data="an:channel_menu"))
    b.row(
        InlineKeyboardButton(text=tr(lang, "an_btn_stats"),
                              callback_data="an:stats"),
        InlineKeyboardButton(text=tr(lang, "an_btn_history"),
                              callback_data="an:history"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_back"),
                                callback_data="admin:home"))
    await safe_edit(cb.message, text, b.as_markup())



__all__ = [name for name in globals() if not name.startswith("__")]
