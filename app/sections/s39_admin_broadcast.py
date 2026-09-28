"""Arka Downloader section: ADMIN — BROADCAST."""

from .s38_admin_jobs import *

# ══════════════════════════════════════════════════════════════
# ADMIN — BROADCAST
# ══════════════════════════════════════════════════════════════
@router.callback_query(F.data == "admin:broadcast")
async def cb_admin_broadcast(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    await state.clear()
    lang = await _admin_lang(c, cb.from_user.id)
    await state.set_state(Flow.a_broadcast_content)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "ad_back"),
                             callback_data="admin:home")]])
    await safe_edit(cb.message, tr(lang, "ad_bc_title"), kb)


@router.message(Flow.a_broadcast_content)
async def msg_broadcast_content(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    lang = await _admin_lang(c, message.from_user.id)
    content_data = {}
    if message.text:
        content_data = {"type": "text", "text": message.text}
    elif message.photo:
        content_data = {"type": "photo",
                        "file_id": message.photo[-1].file_id,
                        "caption": message.caption or ""}
    elif message.video:
        content_data = {"type": "video", "file_id": message.video.file_id,
                        "caption": message.caption or ""}
    elif message.document:
        content_data = {"type": "document",
                        "file_id": message.document.file_id,
                        "caption": message.caption or ""}
    else:
        await message.answer(tr(lang, "ad_bc_no_content"))
        return
    await state.update_data(bc_content=content_data)
    await state.set_state(Flow.a_broadcast_confirm)
    preview = (content_data.get("caption") or content_data.get("text") or "")[:200]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=tr(lang, "yes"), callback_data="bc:confirm")],
        [InlineKeyboardButton(text=tr(lang, "no"), callback_data="bc:cancel")]])
    await message.answer(tr(lang, "ad_bc_preview", preview=esc(preview)),
                          reply_markup=kb)


@router.callback_query(F.data == "bc:cancel")
async def cb_bc_cancel(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    await state.clear()
    lang = await _admin_lang(c, cb.from_user.id)
    await safe_edit(cb.message, tr(lang, "ad_title"), admin_menu(lang))


@router.callback_query(F.data == "bc:confirm")
async def cb_bc_confirm(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    data = await state.get_data()
    content_data = data.get("bc_content", {})
    await state.clear()
    if not content_data:
        await safe_edit(cb.message, tr(lang, "ad_bc_no_content"),
                        admin_menu(lang))
        return
    rows = get_conn().execute(
        "SELECT user_id FROM users WHERE is_blocked=0").fetchall()
    uids = [r["user_id"] for r in rows]
    await safe_edit(cb.message, tr(lang, "ad_bc_sending", count=len(uids)))
    delay = float(db_get("broadcast_delay", "0.05"))
    sent = failed = 0
    t = content_data.get("type")
    for uid in uids:
        try:
            if t == "text":
                await send_text_safe(c.bot, uid, content_data["text"])
            elif t == "photo":
                await c.bot.send_photo(uid, content_data["file_id"],
                                        caption=content_data.get("caption", "")[:1024])
            elif t == "video":
                await c.bot.send_video(uid, content_data["file_id"],
                                        caption=content_data.get("caption", "")[:1024])
            elif t == "document":
                await c.bot.send_document(uid, content_data["file_id"],
                                           caption=content_data.get("caption", "")[:1024])
            sent += 1
        except TelegramForbiddenError:
            failed += 1
            UserRepo.set_blocked(uid, True)
        except Exception:
            failed += 1
        if delay > 0:
            await asyncio.sleep(delay)
    db_log(cb.from_user.id, "broadcast", f"sent={sent} failed={failed}")
    with contextlib.suppress(Exception):
        await c.bot.edit_message_text(
            chat_id=cb.message.chat.id, message_id=cb.message.message_id,
            text=tr(lang, "ad_bc_done", sent=sent, failed=failed),
            reply_markup=admin_menu(lang))



__all__ = [name for name in globals() if not name.startswith("__")]
