"""Arka Downloader section: SUPPORT."""

from .s31_stats import *

# ══════════════════════════════════════════════════════════════
# SUPPORT
# ══════════════════════════════════════════════════════════════
@router.callback_query(F.data == "menu:support")
async def cb_support(cb: CallbackQuery, state: FSMContext, c: Container):
    await cb.answer()
    await state.clear()
    user = UserRepo.get(cb.from_user.id)
    if not user:
        return
    lang = user_lang(user)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=tr(lang, "support_new"),
                              callback_data="support:new")],
        [InlineKeyboardButton(text=tr(lang, "support_my"),
                              callback_data="support:my")],
        [InlineKeyboardButton(text=tr(lang, "back"),
                              callback_data="menu:home")]])
    await safe_edit(cb.message, tr(lang, "support_menu_title"), kb)


@router.callback_query(F.data == "support:new")
async def cb_support_new(cb: CallbackQuery, state: FSMContext, c: Container):
    await cb.answer()
    user = UserRepo.get(cb.from_user.id)
    if not user:
        return
    lang = user_lang(user)
    await state.set_state(Flow.support_message)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "back"),
                             callback_data="menu:support")]])
    await safe_edit(cb.message, tr(lang, "support_title"), kb)


@router.callback_query(F.data == "support:my")
async def cb_support_my(cb: CallbackQuery, c: Container):
    await cb.answer()
    user = UserRepo.get(cb.from_user.id)
    if not user:
        return
    lang = user_lang(user)
    rows = TicketRepo.by_user(user.user_id, limit=10)
    if not rows:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=tr(lang, "back"),
                                 callback_data="menu:support")]])
        await safe_edit(cb.message, tr(lang, "my_tickets_empty"), kb)
        return
    text = tr(lang, "my_tickets_title") + "\n\n"
    buttons = []
    for tk in rows:
        icon = {"open": "🟢", "answered": "🟡", "closed": "🔴"}.get(
            tk["status"], "⚪")
        preview = esc((tk["message"] or "")[:30])
        text += f"{icon} <b>#{tk['ticket_id']}</b> — {preview}\n"
        buttons.append([InlineKeyboardButton(
            text=f"{icon} #{tk['ticket_id']}",
            callback_data=safe_cb(f"mytk:{tk['ticket_id']}"))])
    buttons.append([InlineKeyboardButton(text=tr(lang, "back"),
                                          callback_data="menu:support")])
    await safe_edit(cb.message, text,
                    InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data.startswith("mytk:"))
async def cb_my_ticket_view(cb: CallbackQuery, c: Container):
    user = UserRepo.get(cb.from_user.id)
    if not user:
        await cb.answer()
        return
    lang = user_lang(user)
    try:
        tid = int(cb.data.rsplit(":", 1)[1])
    except ValueError:
        await cb.answer()
        return
    tk = TicketRepo.get(tid)
    if not tk or int(tk["user_id"]) != user.user_id:
        await cb.answer("⛔", show_alert=True)
        return
    await cb.answer()
    status_map = {"open": tr(lang, "ticket_status_open"),
                  "answered": tr(lang, "ticket_status_answered"),
                  "closed": tr(lang, "ticket_status_closed")}
    status = status_map.get(tk["status"], tk["status"])
    text = tr(lang, "ticket_detail_user", id=tk["ticket_id"], status=status,
              date=fmt_time(tk["created_at"]), msg=esc(tk["message"] or ""))
    if tk["answer"]:
        text += (f"\n\n{tr(lang, 'ticket_reply_label')}\n"
                 f"{esc(tk['answer'])}")
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "back"),
                             callback_data="support:my")]])
    await safe_edit(cb.message, text, kb)


@router.message(Flow.support_message, F.text)
async def msg_support(message: Message, state: FSMContext, c: Container):
    user = UserRepo.get(message.from_user.id)
    if not user:
        await state.clear()
        return
    lang = user_lang(user)
    text = (message.text or "").strip()
    if not text:
        await message.answer(tr(lang, "empty"))
        return
    await state.clear()
    tid = TicketRepo.create(user.user_id, text)
    await message.answer(tr(lang, "support_sent", id=tid))
    with contextlib.suppress(Exception):
        owner = UserRepo.get(OWNER_IDS[0]) if OWNER_IDS else None
        owner_lang = user_lang(owner) if owner else "fa"
        text_owner = tr(owner_lang, "ticket_admin_notify", id=tid,
                        uid=user.user_id, name=esc(user.first_name or "User"),
                        msg=esc(text[:3000]))
        await c.bot.send_message(
            OWNER_IDS[0], text_owner,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text=tr(owner_lang, "ticket_view_btn"),
                    callback_data=safe_cb(f"ticket:view:{tid}"))]]))



__all__ = [name for name in globals() if not name.startswith("__")]
