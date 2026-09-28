"""Arka Downloader section: TEXTS."""

from .s58_custom_buttons import *

# ══════════════════════════════════════════════════════════════
# TEXTS
# ══════════════════════════════════════════════════════════════
@router.callback_query(F.data == "admin:texts")
async def cb_admin_texts(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    await state.clear()
    lang = await _admin_lang(c, cb.from_user.id)
    b = InlineKeyboardBuilder()
    for key in TEXT_KEYS:
        current = db_get(f"custom_text_{key}", "")
        marker = "✅" if current else "⚪"
        label = text_label(lang, key)
        b.row(InlineKeyboardButton(
            text=f"{marker} {label}",
            callback_data=safe_cb(f"txt:edit:{key}")))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_back"),
                                callback_data="admin:home"))
    await safe_edit(cb.message, tr(lang, "texts_title"), b.as_markup())


@router.callback_query(F.data.startswith("txt:edit:"))
async def cb_txt_edit(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    key = cb.data[len("txt:edit:"):]
    if not key:
        await cb.answer()
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    custom = db_get(f"custom_text_{key}", "")
    current = custom if custom else tr(lang, key)
    label = text_label(lang, key)
    status = tr(lang, "texts_custom_status") if custom else tr(lang, "texts_default_status")

    await state.set_state(Flow.text_value)
    await state.update_data(text_key=key)

    info = (f"📝 <b>{esc(label)}</b>  <i>({status})</i>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"<code>{esc(current[:600])}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"{tr(lang, 'texts_ask_new')}")

    b = InlineKeyboardBuilder()
    if custom:
        b.row(InlineKeyboardButton(
            text=tr(lang, "texts_reset_btn"),
            callback_data=safe_cb(f"txt:reset:{key}")))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_back"),
                                callback_data="admin:texts"))
    await safe_edit(cb.message, info, b.as_markup())


@router.callback_query(F.data.startswith("txt:reset:"))
async def cb_txt_reset(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    key = cb.data[len("txt:reset:"):]
    lang = await _admin_lang(c, cb.from_user.id)
    get_conn().execute("DELETE FROM settings WHERE key=?",
                       (f"custom_text_{key}",))
    await cb.answer(tr(lang, "texts_reset_ok"), show_alert=True)
    await state.clear()
    await cb_admin_texts(cb, state, c)


@router.message(Flow.text_value, F.text)
async def msg_txt_edit(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    key = data.get("text_key")
    if not key:
        await state.clear()
        return
    val = (message.text or "").strip()
    if not val:
        await message.answer("⚠️")
        return
    if val == "-":
        get_conn().execute("DELETE FROM settings WHERE key=?",
                           (f"custom_text_{key}",))
        await state.clear()
        await message.answer("♻️")
        return
    db_set(f"custom_text_{key}", val)
    await state.clear()
    await message.answer("✅")



__all__ = [name for name in globals() if not name.startswith("__")]
