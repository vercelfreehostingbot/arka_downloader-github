"""Arka Downloader section: ANNOUNCE — CHANNEL."""

from .s50_announce_users import *

# ══════════════════════════════════════════════════════════════
# ANNOUNCE — CHANNEL
# ══════════════════════════════════════════════════════════════
async def _render_an_channel(cb: CallbackQuery, c: Container):
    lang = await _admin_lang(c, cb.from_user.id)
    ch_id = db_get("announce_channel_id", "") or "—"
    enabled = db_get("announce_channel_enabled", "0") == "1"
    pin = "✅" if db_get("announce_channel_pin", "0") == "1" else "❌"
    silent = "✅" if db_get("announce_channel_silent", "0") == "1" else "❌"
    st = tr(lang, "active") if enabled else tr(lang, "disabled")
    try:
        total = int(db_get("announce_channel_total", "0") or "0")
    except Exception:
        total = 0
    last_ts = db_get("announce_channel_last_ts", "0")
    try:
        last_str = fmt_time(float(last_ts)) if float(last_ts or 0) > 0 else "—"
    except Exception:
        last_str = "—"

    text = tr(lang, "an_channel_title", status=st, channel=esc(ch_id),
              pin=pin, silent=silent, total=total, last=last_str)

    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text=tr(lang, "an_btn_set"),
                              callback_data="anc:set"),
        InlineKeyboardButton(text=tr(lang, "an_btn_enable"),
                              callback_data="anc:toggle"))
    b.row(
        InlineKeyboardButton(text=tr(lang, "an_btn_pin", v=pin),
                              callback_data="anc:pin"),
        InlineKeyboardButton(text=tr(lang, "an_btn_silent", v=silent),
                              callback_data="anc:silent"))
    b.row(
        InlineKeyboardButton(text=tr(lang, "an_btn_text"),
                              callback_data="anc:send_text"),
        InlineKeyboardButton(text=tr(lang, "an_btn_media"),
                              callback_data="anc:send_media"))
    b.row(
        InlineKeyboardButton(text=tr(lang, "an_btn_forward"),
                              callback_data="anc:send_forward"),
        InlineKeyboardButton(text=tr(lang, "an_btn_test"),
                              callback_data="anc:test"))
    b.row(InlineKeyboardButton(text=tr(lang, "an_btn_reset"),
                                callback_data="anc:reset_stats"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_back"),
                                callback_data="admin:announce"))
    await safe_edit(cb.message, text, b.as_markup())


@router.callback_query(F.data == "an:channel_menu")
async def cb_an_channel_menu(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    await _render_an_channel(cb, c)


@router.callback_query(F.data == "anc:set")
async def cb_anc_set(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    await state.set_state(Flow.a_announce_channel_id)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="◀️", callback_data="an:channel_menu")]])
    await safe_edit(cb.message, tr(lang, "an_set_ch_ask"), kb)


@router.message(Flow.a_announce_channel_id, F.text)
async def msg_anc_set(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    lang = await _admin_lang(c, message.from_user.id)
    val = (message.text or "").strip()
    if not val:
        await message.answer("⚠️")
        return
    try:
        if val.lstrip("-").isdigit():
            target = int(val)
        else:
            target = "@" + val.lstrip("@")
        chat = await c.bot.get_chat(target)
        me = await c.bot.get_me()
        member = await c.bot.get_chat_member(chat.id, me.id)
        if member.status not in ("administrator", "creator"):
            await message.answer(tr(lang, "an_bot_not_admin"))
            return
        db_set("announce_channel_id", str(chat.id))
        db_set("announce_channel_enabled", "1")
        await state.clear()
        await message.answer(
            f"✅ <b>{esc(chat.title or '')}</b>\n<code>{chat.id}</code>")
    except Exception as e:
        await message.answer(f"❌ <code>{esc(str(e)[:200])}</code>")


@router.callback_query(F.data == "anc:toggle")
async def cb_anc_toggle(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    cur = db_get("announce_channel_enabled", "0")
    db_set("announce_channel_enabled", "0" if cur == "1" else "1")
    await cb.answer("✅")
    await _render_an_channel(cb, c)


@router.callback_query(F.data == "anc:pin")
async def cb_anc_pin(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    cur = db_get("announce_channel_pin", "0")
    db_set("announce_channel_pin", "0" if cur == "1" else "1")
    await cb.answer("✅")
    await _render_an_channel(cb, c)


@router.callback_query(F.data == "anc:silent")
async def cb_anc_silent(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    cur = db_get("announce_channel_silent", "0")
    db_set("announce_channel_silent", "0" if cur == "1" else "1")
    await cb.answer("✅")
    await _render_an_channel(cb, c)


@router.callback_query(F.data == "anc:send_text")
async def cb_anc_send_text(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    lang = await _admin_lang(c, cb.from_user.id)
    if not db_get("announce_channel_id", ""):
        await cb.answer(tr(lang, "an_ch_empty"), show_alert=True)
        return
    await cb.answer()
    await state.set_state(Flow.a_anc_text)
    await state.update_data(anc_text=None, anc_media=None, anc_forward=None)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="◀️", callback_data="an:channel_menu")]])
    await safe_edit(cb.message, tr(lang, "an_text_ask"), kb)


@router.message(Flow.a_anc_text, F.text)
async def msg_anc_text(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    lang = await _admin_lang(c, message.from_user.id)
    text = (message.text or "").strip()
    if not text:
        await message.answer("⚠️")
        return
    await state.update_data(anc_text=text, anc_kind="text")
    await state.set_state(Flow.a_anc_confirm)
    await _show_channel_preview(message, c, lang, text=text)


@router.callback_query(F.data == "anc:send_media")
async def cb_anc_send_media(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    lang = await _admin_lang(c, cb.from_user.id)
    if not db_get("announce_channel_id", ""):
        await cb.answer(tr(lang, "an_ch_empty"), show_alert=True)
        return
    await cb.answer()
    await state.set_state(Flow.a_anc_media)
    await state.update_data(anc_kind="media", anc_text=None,
                            anc_media=None, anc_forward=None)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="◀️", callback_data="an:channel_menu")]])
    await safe_edit(cb.message, tr(lang, "an_media_ask"), kb)


@router.message(Flow.a_anc_media)
async def msg_anc_media(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    lang = await _admin_lang(c, message.from_user.id)
    data = await state.get_data()
    kind = data.get("anc_kind", "media")
    if kind == "forward":
        fwd = {"from_chat_id": message.chat.id,
               "message_id": message.message_id}
        await state.update_data(anc_forward=fwd)
        await state.set_state(Flow.a_anc_confirm)
        await _show_channel_preview(message, c, lang,
                                     text=tr(lang, "an_btn_forward"))
        return
    media = None
    if message.photo:
        media = {"type": "photo", "file_id": message.photo[-1].file_id,
                 "caption": message.caption or ""}
    elif message.video:
        media = {"type": "video", "file_id": message.video.file_id,
                 "caption": message.caption or ""}
    elif message.document:
        media = {"type": "document", "file_id": message.document.file_id,
                 "caption": message.caption or ""}
    elif message.audio:
        media = {"type": "audio", "file_id": message.audio.file_id,
                 "caption": message.caption or ""}
    elif message.animation:
        media = {"type": "animation", "file_id": message.animation.file_id,
                 "caption": message.caption or ""}
    else:
        await message.answer("⚠️")
        return
    await state.update_data(anc_media=media)
    await state.set_state(Flow.a_anc_confirm)
    await _show_channel_preview(message, c, lang, media=media)


@router.callback_query(F.data == "anc:send_forward")
async def cb_anc_forward(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    lang = await _admin_lang(c, cb.from_user.id)
    if not db_get("announce_channel_id", ""):
        await cb.answer(tr(lang, "an_ch_empty"), show_alert=True)
        return
    await cb.answer()
    await state.set_state(Flow.a_anc_media)
    await state.update_data(anc_kind="forward", anc_text=None,
                            anc_media=None, anc_forward=None)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="◀️", callback_data="an:channel_menu")]])
    await safe_edit(cb.message, tr(lang, "an_forward_ask"), kb)


async def _show_channel_preview(target, c, lang, text=None, media=None):
    ch = db_get("announce_channel_id", "—")
    pin = "✅" if db_get("announce_channel_pin", "0") == "1" else "❌"
    silent = "✅" if db_get("announce_channel_silent", "0") == "1" else "❌"
    body = (tr(lang, "an_preview_title", channel=esc(ch)) + "\n")
    if text:
        body += f"📝 <blockquote>{esc(text[:600])}</blockquote>\n"
    if media:
        body += f"📎 {media.get('type', '?')}\n"
        if media.get("caption"):
            body += f"💬 <blockquote>{esc(media['caption'][:400])}</blockquote>\n"
    body += (f"━━━━━━━━━━━━━━━━━━━━━\n📌 {pin}  |  🔇 {silent}\n"
             f"{tr(lang, 'an_send_confirm')}")
    b = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=tr(lang, "an_send_btn"),
                              callback_data="anc:confirm")],
        [InlineKeyboardButton(text=tr(lang, "an_cancel_btn"),
                              callback_data="anc:abort")]])
    if isinstance(target, Message):
        await target.answer(body, reply_markup=b)
    else:
        await safe_edit(target, body, b)


@router.callback_query(F.data == "anc:abort")
async def cb_anc_abort(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer("❌")
    await state.clear()
    await _render_an_channel(cb, c)


@router.callback_query(F.data == "anc:confirm")
async def cb_anc_confirm(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    data = await state.get_data()
    text = data.get("anc_text") or ""
    media = data.get("anc_media") or {}
    forward = data.get("anc_forward") or None
    await state.clear()
    ch = db_get("announce_channel_id", "")
    if not ch:
        await cb.answer("⚠️", show_alert=True)
        return
    await cb.answer("📤...")
    silent = db_get("announce_channel_silent", "0") == "1"
    pin = db_get("announce_channel_pin", "0") == "1"
    try:
        target = int(ch) if ch.lstrip("-").isdigit() else ch
        sent_msg = None
        if forward:
            sent_msg = await c.bot.copy_message(
                chat_id=target, from_chat_id=forward["from_chat_id"],
                message_id=forward["message_id"],
                disable_notification=silent)
        elif media:
            t = media.get("type")
            cap = (media.get("caption") or "")[:1024]
            if t == "photo":
                sent_msg = await c.bot.send_photo(
                    target, media["file_id"], caption=cap,
                    disable_notification=silent)
            elif t == "video":
                sent_msg = await c.bot.send_video(
                    target, media["file_id"], caption=cap,
                    disable_notification=silent)
            elif t == "document":
                sent_msg = await c.bot.send_document(
                    target, media["file_id"], caption=cap,
                    disable_notification=silent)
            elif t == "audio":
                sent_msg = await c.bot.send_audio(
                    target, media["file_id"], caption=cap,
                    disable_notification=silent)
            elif t == "animation":
                sent_msg = await c.bot.send_animation(
                    target, media["file_id"], caption=cap,
                    disable_notification=silent)
        else:
            sent_msg = await send_text_safe(
                c.bot, target, text, disable_notification=silent)

        if pin and sent_msg:
            with contextlib.suppress(Exception):
                await c.bot.pin_chat_message(
                    target, sent_msg.message_id, disable_notification=True)

        db_set("announce_channel_last_ts", str(now_ts()))
        try:
            prev = int(db_get("announce_channel_total", "0") or "0")
            db_set("announce_channel_total", str(prev + 1))
        except Exception:
            pass
        db_log(cb.from_user.id, "announce_channel", f"ch={ch}")
        lang = await _admin_lang(c, cb.from_user.id)
        await safe_edit(cb.message,
            f"{tr(lang, 'an_sent_ok')}\n📢 <code>{esc(ch)}</code>")
    except Exception as e:
        await safe_edit(cb.message,
            f"❌ <code>{esc(str(e)[:300])}</code>")


@router.callback_query(F.data == "anc:reset_stats")
async def cb_anc_reset_stats(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    db_set("announce_channel_total", "0")
    await cb.answer("✅")
    await _render_an_channel(cb, c)


@router.callback_query(F.data == "anc:test")
async def cb_anc_test(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    lang = await _admin_lang(c, cb.from_user.id)
    if not db_get("announce_channel_id", ""):
        await cb.answer(tr(lang, "an_ch_empty"), show_alert=True)
        return
    await cb.answer()
    await state.set_state(Flow.a_anc_test)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="◀️", callback_data="an:channel_menu")]])
    await safe_edit(cb.message, tr(lang, "an_test_ask"), kb)


@router.message(Flow.a_anc_test, F.text)
async def msg_anc_test(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    txt = (message.text or "").strip()
    if not txt:
        await message.answer("⚠️")
        return
    ch = db_get("announce_channel_id", "")
    try:
        target = int(ch) if ch.lstrip("-").isdigit() else ch
        await c.bot.send_message(target, f"🧪 <b>...</b>\n\n{esc(txt)}")
        await message.answer("✅")
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ {esc(str(e)[:200])}")



__all__ = [name for name in globals() if not name.startswith("__")]
