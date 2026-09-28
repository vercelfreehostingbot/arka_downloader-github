"""Arka Downloader section: CUSTOM BUTTONS."""

from .s57_buttons_menu_editor import *

# ══════════════════════════════════════════════════════════════
# CUSTOM BUTTONS
# ══════════════════════════════════════════════════════════════
async def _render_custom_buttons(cb: CallbackQuery, c: Container):
    lang = await _admin_lang(c, cb.from_user.id)
    rows = get_conn().execute(
        "SELECT * FROM custom_buttons WHERE is_active=1 ORDER BY row_order, id"
    ).fetchall()
    text = tr(lang, "cbtn_title") + "\n\n"
    if not rows:
        text += tr(lang, "cbtn_empty")
    else:
        for i, r in enumerate(rows, 1):
            text += f"{i}. {esc(r['label'])} → <code>{esc(r['callback'])}</code>\n"
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=tr(lang, "cbtn_add"),
                                callback_data="cbtn:add"))
    for r in rows[:10]:
        b.row(InlineKeyboardButton(
            text=f"🗑 {r['label'][:25]}",
            callback_data=safe_cb(f"cbtn:del:{r['id']}")))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_back"),
                                callback_data="admin:buttons"))
    await safe_edit(cb.message, text, b.as_markup())


@router.callback_query(F.data == "admin:custom_buttons")
async def cb_admin_custom_buttons(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    await state.clear()
    await _render_custom_buttons(cb, c)


@router.callback_query(F.data == "cbtn:add")
async def cb_cbtn_add(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    await state.set_state(Flow.cbtn_label)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "ad_back"),
                             callback_data="admin:custom_buttons")]])
    await safe_edit(cb.message, tr(lang, "cbtn_ask_label"), kb)


@router.message(Flow.cbtn_label, F.text)
async def msg_cbtn_label(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    lang = await _admin_lang(c, message.from_user.id)
    val = (message.text or "").strip()
    if not val:
        await message.answer("⚠️")
        return
    await state.update_data(cbtn_label=val)
    await state.set_state(Flow.cbtn_callback)
    await message.answer(tr(lang, "callback_data_prompt"))


@router.message(Flow.cbtn_callback, F.text)
async def msg_cbtn_cb(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    label = data.get("cbtn_label")
    cb_data = (message.text or "").strip()
    if not label or not cb_data:
        await state.clear()
        return
    get_conn().execute(
        """INSERT INTO custom_buttons(label, callback, is_active, created_at)
           VALUES (?, ?, 1, ?)""", (label, cb_data, now_ts()))
    await state.clear()
    await message.answer("✅")


@router.callback_query(F.data.startswith("cbtn:del:"))
async def cb_cbtn_del(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    try:
        bid = int(cb.data.rsplit(":", 1)[1])
    except ValueError:
        await cb.answer()
        return
    get_conn().execute("DELETE FROM custom_buttons WHERE id=?", (bid,))
    await cb.answer("🗑", show_alert=True)
    await _render_custom_buttons(cb, c)



__all__ = [name for name in globals() if not name.startswith("__")]
