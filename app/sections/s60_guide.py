"""Arka Downloader section: GUIDE."""

from .s59_texts import *

# ══════════════════════════════════════════════════════════════
# GUIDE
# ══════════════════════════════════════════════════════════════
@router.callback_query(F.data == "admin:guide")
async def cb_admin_guide(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(
        text="🇮🇷 فارسی / Persian",
        callback_data="guide:fa"))
    b.row(InlineKeyboardButton(
        text="🇬🇧 English / انگلیسی",
        callback_data="guide:en"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_back"),
                                callback_data="admin:home"))
    title = ("📖 <b>راهنما / Guide</b>\n\n"
             "زبان مورد نظر را انتخاب کنید:\n"
             "Choose your preferred language:")
    await safe_edit(cb.message, title, b.as_markup())


@router.callback_query(F.data.in_({"guide:fa", "guide:en"}))
async def cb_guide_edit(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    lang_code = cb.data.split(":")[1]
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    await state.set_state(Flow.guide_text)
    await state.update_data(guide_lang=lang_code)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "back"),
                             callback_data="admin:guide")]])
    await safe_edit(cb.message, tr(lang, "guide_ask", lang=lang_code), kb)


@router.message(Flow.guide_text, F.text)
async def msg_guide_text(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    lang_code = data.get("guide_lang")
    val = (message.text or "").strip()
    if not lang_code or not val:
        await state.clear()
        return
    db_set(f"guide_{lang_code}", val)
    await state.clear()
    await message.answer("✅")



__all__ = [name for name in globals() if not name.startswith("__")]
