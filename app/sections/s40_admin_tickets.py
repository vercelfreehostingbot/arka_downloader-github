"""Arka Downloader section: ADMIN — TICKETS."""

from .s39_admin_broadcast import *

# ══════════════════════════════════════════════════════════════
# ADMIN — TICKETS
# ══════════════════════════════════════════════════════════════
@router.callback_query(F.data == "admin:tickets")
async def cb_admin_tickets(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    await render_tickets(cb, c, "open", 1)


@router.callback_query(F.data.startswith("tk:filter:"))
async def cb_tickets_filter(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    parts = cb.data.split(":")
    if len(parts) == 4:
        status = parts[2]
        try:
            page = int(parts[3])
        except ValueError:
            page = 1
    else:
        status, page = "open", 1
    await render_tickets(cb, c, status, page)


async def render_tickets(cb, c, status="open", page=1):
    lang = await _admin_lang(c, cb.from_user.id)
    per = 10
    page = max(1, page)
    total = TicketRepo.count_by_status(status)
    total_pages = max(1, (total + per - 1) // per)
    rows = TicketRepo.by_status(status, limit=per, offset=(page - 1) * per)
    label = {"open": tr(lang, "ad_tk_open"),
             "closed": tr(lang, "ad_tk_closed"),
             "all": tr(lang, "ad_tk_all")}.get(status, "?")
    b = InlineKeyboardBuilder()
    if not rows:
        b.row(InlineKeyboardButton(text=tr(lang, "empty"), callback_data="noop"))
    else:
        for tk in rows:
            icon = {"open": "🟢", "closed": "🔴", "answered": "🟡"}.get(
                tk["status"], "⚪")
            preview = esc((tk["message"] or "")[:26])
            b.row(InlineKeyboardButton(
                text=f"{icon} #{tk['ticket_id']} | {tk['user_id']} | {preview}",
                callback_data=safe_cb(f"ticket:view:{tk['ticket_id']}")))
    b.row(
        InlineKeyboardButton(text=tr(lang, "ad_tk_open"),
                              callback_data="tk:filter:open:1"),
        InlineKeyboardButton(text=tr(lang, "ad_tk_closed"),
                              callback_data="tk:filter:closed:1"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_tk_all"),
                                callback_data="tk:filter:all:1"))
    nav = InlineKeyboardBuilder()
    if page > 1:
        nav.button(text="◀️", callback_data=safe_cb(f"tk:filter:{status}:{page-1}"))
    nav.button(text=f"📄 {page}/{total_pages}", callback_data="noop")
    if page < total_pages:
        nav.button(text="▶️", callback_data=safe_cb(f"tk:filter:{status}:{page+1}"))
    nav.adjust(3)
    rows_kb = b.export() + nav.export()
    rows_kb.append([InlineKeyboardButton(text=tr(lang, "ad_back"),
                                           callback_data="admin:home")])
    text = tr(lang, "ad_tk_title", status=label, count=total)
    await safe_edit(cb.message, text,
                    InlineKeyboardMarkup(inline_keyboard=rows_kb))


@router.callback_query(F.data.startswith("ticket:view:"))
async def cb_ticket_view(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    try:
        tid = int(cb.data.rsplit(":", 1)[1])
    except ValueError:
        return
    tk = TicketRepo.get(tid)
    if not tk:
        await safe_edit(cb.message, tr(lang, "empty"))
        return
    text = tr(lang, "ad_tk_detail", id=tk["ticket_id"], uid=tk["user_id"],
              status=esc(tk["status"]), msg=esc(tk["message"]),
              date=fmt_time(tk["created_at"]))
    if tk["answer"]:
        text += f"\n\n💬 {esc(tk['answer'])}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=tr(lang, "ad_tk_reply"),
                              callback_data=safe_cb(f"ticket:reply:{tid}")),
         InlineKeyboardButton(text=tr(lang, "ad_tk_close"),
                              callback_data=safe_cb(f"ticket:close:{tid}"))],
        [InlineKeyboardButton(text=tr(lang, "ad_back"),
                              callback_data="admin:tickets")]])
    await safe_edit(cb.message, text, kb)


@router.callback_query(F.data.startswith("ticket:reply:"))
async def cb_ticket_reply(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    tid = int(cb.data.rsplit(":", 1)[1])
    lang = await _admin_lang(c, cb.from_user.id)
    await state.set_state(Flow.a_ticket_reply)
    await state.update_data(ticket_id=tid)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "ad_back"),
                             callback_data="admin:tickets")]])
    await safe_edit(cb.message, tr(lang, "ad_tk_ask_reply"), kb)


@router.message(Flow.a_ticket_reply, F.text)
async def msg_ticket_reply(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    tid = data.get("ticket_id")
    lang = await _admin_lang(c, message.from_user.id)
    if not tid:
        await state.clear()
        return
    tk = TicketRepo.get(tid)
    if not tk:
        await state.clear()
        return
    answer = (message.text or "").strip()
    if not answer:
        await message.answer(tr(lang, "empty"))
        return
    TicketRepo.answer(tid, answer)
    await state.clear()
    with contextlib.suppress(Exception):
        await c.bot.send_message(
            tk["user_id"],
            tr(lang, "ad_tk_reply_prefix", id=tid) + esc(answer))
    await message.answer(tr(lang, "ad_tk_reply_sent"))


@router.callback_query(F.data.startswith("ticket:close:"))
async def cb_ticket_close(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer("🔒", show_alert=True)
    tid = int(cb.data.rsplit(":", 1)[1])
    TicketRepo.close(tid)
    await render_tickets(cb, c, "open", 1)



__all__ = [name for name in globals() if not name.startswith("__")]
