"""Arka Downloader section: ADMIN — QUALITY."""

from .s43_admin_channel import *

# ══════════════════════════════════════════════════════════════
# ADMIN — QUALITY
# ══════════════════════════════════════════════════════════════
@router.callback_query(F.data == "admin:quality")
async def cb_admin_quality(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    allowed = allowed_qualities()
    labels = QUALITY_LABELS.get(lang, QUALITY_LABELS["fa"])
    b = InlineKeyboardBuilder()
    for q in ALL_QUALITIES:
        icon = "✅" if q in allowed else "❌"
        b.row(InlineKeyboardButton(
            text=f"{icon} {labels[q]}",
            callback_data=safe_cb(f"admq:toggle:{q}")))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_back"),
                                callback_data="admin:home"))
    en = ", ".join(labels[q] for q in ALL_QUALITIES if q in allowed) or "-"
    di = ", ".join(labels[q] for q in ALL_QUALITIES if q not in allowed) or "-"
    text = tr(lang, "ad_q_title", enabled=esc(en), disabled=esc(di))
    await safe_edit(cb.message, text, b.as_markup())


@router.callback_query(F.data.startswith("admq:toggle:"))
async def cb_quality_toggle(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    q = cb.data.rsplit(":", 1)[1]
    if q not in ALL_QUALITIES:
        await cb.answer()
        return
    allowed = allowed_qualities()
    if q in allowed:
        allowed.discard(q)
    else:
        allowed.add(q)
    db_set("allowed_quality", ",".join(sorted(allowed)))
    await cb.answer("✅")
    await cb_admin_quality(cb, c)



__all__ = [name for name in globals() if not name.startswith("__")]
