"""Arka Downloader section: ANNOUNCE — USERS."""

from .s49_admin_announce_main import *

# ══════════════════════════════════════════════════════════════
# ANNOUNCE — USERS
# ══════════════════════════════════════════════════════════════
async def _render_an_users(cb: CallbackQuery, c: Container):
    lang = await _admin_lang(c, cb.from_user.id)
    st = tr(lang, "active") if db_get("announce_enabled", "0") == "1" else tr(lang, "disabled")
    pin = "✅" if db_get("announce_pin", "0") == "1" else "❌"
    silent = "✅" if db_get("announce_silent", "0") == "1" else "❌"
    preview = "✅" if db_get("announce_preview", "1") == "1" else "❌"
    autodel = "✅" if db_get("announce_auto_delete", "0") == "1" else "❌"
    a = db_get("announce_audience", "all")
    a_label = audience_label(lang, a)
    count = _audience_count()

    text = tr(lang, "an_users_title", status=st, audience=a_label,
              count=count, pin=pin, silent=silent,
              preview=preview, autodel=autodel)

    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(
        text=tr(lang, "an_btn_audience", label=a_label, count=count),
        callback_data="an:audience"))
    b.row(
        InlineKeyboardButton(text=tr(lang, "an_btn_text"),
                              callback_data="an:send_text"),
        InlineKeyboardButton(text=tr(lang, "an_btn_media"),
                              callback_data="an:send_media"))
    b.row(
        InlineKeyboardButton(text=tr(lang, "an_btn_forward"),
                              callback_data="an:send_forward"),
        InlineKeyboardButton(text=tr(lang, "an_btn_test"),
                              callback_data="an:test"))
    b.row(
        InlineKeyboardButton(text=tr(lang, "an_btn_pin", v=pin),
                              callback_data="an:pin"),
        InlineKeyboardButton(text=tr(lang, "an_btn_silent", v=silent),
                              callback_data="an:silent"))
    b.row(
        InlineKeyboardButton(text=tr(lang, "an_btn_preview", v=preview),
                              callback_data="an:preview"),
        InlineKeyboardButton(text=tr(lang, "an_btn_autodel", v=autodel),
                              callback_data="an:auto_delete"))
    b.row(InlineKeyboardButton(text=tr(lang, "an_btn_schedule"),
                                callback_data="an:schedule_menu"))
    b.row(
        InlineKeyboardButton(text=tr(lang, "an_btn_enable"),
                              callback_data="an:toggle"),
        InlineKeyboardButton(text=tr(lang, "an_btn_reset"),
                              callback_data="an:reset_stats"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_back"),
                                callback_data="admin:announce"))
    await safe_edit(cb.message, text, b.as_markup())


@router.callback_query(F.data == "an:users_menu")
async def cb_an_users_menu(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    await _render_an_users(cb, c)


@router.callback_query(F.data == "an:audience")
async def cb_an_audience(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    cur = db_get("announce_audience", "all")
    try:
        total = UserRepo.count_all()
        vip = UserRepo.count_vip()
        active = int(get_conn().execute(
            "SELECT COUNT(*) AS c FROM users WHERE downloads>0").fetchone()["c"] or 0)
        inactive = int(get_conn().execute(
            "SELECT COUNT(*) AS c FROM users WHERE downloads=0").fetchone()["c"] or 0)
    except Exception:
        total = vip = active = inactive = 0

    text = tr(lang, "an_audience_title",
              total=total, vip=vip, active=active, inactive=inactive)

    def mark(k): return "✅ " if cur == k else ""
    b = InlineKeyboardBuilder()
    for k in ("all", "vip", "active", "inactive"):
        b.row(InlineKeyboardButton(
            text=f"{mark(k)}{audience_label(lang, k)}",
            callback_data=f"an:set_aud:{k}"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_back"),
                                callback_data="an:users_menu"))
    await safe_edit(cb.message, text, b.as_markup())


@router.callback_query(F.data.startswith("an:set_aud:"))
async def cb_an_set_aud(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    val = cb.data.rsplit(":", 1)[1]
    if val not in ("all", "vip", "active", "inactive"):
        await cb.answer()
        return
    db_set("announce_audience", val)
    await cb.answer("✅")
    await cb_an_audience(cb, c)


@router.callback_query(F.data == "an:toggle")
async def cb_an_toggle(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    cur = db_get("announce_enabled", "0")
    db_set("announce_enabled", "0" if cur == "1" else "1")
    await cb.answer("✅")
    await _render_an_users(cb, c)


@router.callback_query(F.data == "an:pin")
async def cb_an_pin(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    cur = db_get("announce_pin", "0")
    db_set("announce_pin", "0" if cur == "1" else "1")
    await cb.answer("✅")
    await _render_an_users(cb, c)


@router.callback_query(F.data == "an:silent")
async def cb_an_silent(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    cur = db_get("announce_silent", "0")
    db_set("announce_silent", "0" if cur == "1" else "1")
    await cb.answer("✅")
    await _render_an_users(cb, c)


@router.callback_query(F.data == "an:preview")
async def cb_an_preview(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    cur = db_get("announce_preview", "1")
    db_set("announce_preview", "0" if cur == "1" else "1")
    await cb.answer("✅")
    await _render_an_users(cb, c)


@router.callback_query(F.data == "an:auto_delete")
async def cb_an_autodel(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    cur = db_get("announce_auto_delete", "0")
    db_set("announce_auto_delete", "0" if cur == "1" else "1")
    await cb.answer("✅")
    await _render_an_users(cb, c)


@router.callback_query(F.data == "an:send_text")
async def cb_an_send_text(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    await state.set_state(Flow.a_announce_msg)
    await state.update_data(announce_kind="text", announce_text=None,
                            announce_media=None, announce_forward=None)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "ad_back"),
                             callback_data="an:users_menu")]])
    await safe_edit(cb.message, tr(lang, "an_text_ask"), kb)


@router.message(Flow.a_announce_msg, F.text)
async def msg_an_text(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    lang = await _admin_lang(c, message.from_user.id)
    text = (message.text or "").strip()
    if not text:
        await message.answer("⚠️")
        return
    await state.update_data(announce_text=text)
    await state.set_state(Flow.a_announce_confirm)
    await _show_user_preview(message, c, lang, text=text)


@router.callback_query(F.data == "an:send_media")
async def cb_an_send_media(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    await state.set_state(Flow.a_announce_media)
    await state.update_data(announce_kind="media", announce_text=None,
                            announce_media=None, announce_forward=None)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "ad_back"),
                             callback_data="an:users_menu")]])
    await safe_edit(cb.message, tr(lang, "an_media_ask"), kb)


@router.message(Flow.a_announce_media)
async def msg_an_media(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    lang = await _admin_lang(c, message.from_user.id)
    data = await state.get_data()
    kind = data.get("announce_kind", "media")
    if kind == "forward":
        fwd = {"from_chat_id": message.chat.id,
               "message_id": message.message_id}
        await state.update_data(announce_forward=fwd)
        await state.set_state(Flow.a_announce_confirm)
        await _show_user_preview(message, c, lang,
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
    await state.update_data(announce_media=media)
    await state.set_state(Flow.a_announce_confirm)
    await _show_user_preview(message, c, lang, media=media)


@router.callback_query(F.data == "an:send_forward")
async def cb_an_send_forward(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    await state.set_state(Flow.a_announce_media)
    await state.update_data(announce_kind="forward", announce_text=None,
                            announce_media=None, announce_forward=None)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "ad_back"),
                             callback_data="an:users_menu")]])
    await safe_edit(cb.message, tr(lang, "an_forward_ask"), kb)


async def _show_user_preview(target, c: Container, lang: str,
                              text=None, media=None):
    preview_on = db_get("announce_preview", "1") == "1"
    a = db_get("announce_audience", "all")
    a_label = audience_label(lang, a)
    count = _audience_count()
    body = (tr(lang, "an_preview_title", channel="—") +
            f"\n{tr(lang, 'an_preview_audience', label=a_label, count=count)}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n")
    if text:
        p = text[:800] if preview_on else "🔒"
        body += f"📝 <blockquote>{esc(p)}</blockquote>\n"
    if media:
        body += f"📎 {media.get('type', '?')}\n"
        if media.get("caption") and preview_on:
            body += f"💬 <blockquote>{esc(media['caption'][:400])}</blockquote>\n"
    body += f"━━━━━━━━━━━━━━━━━━━━━\n{tr(lang, 'an_send_confirm')}"
    b = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=tr(lang, "an_send_btn"),
                              callback_data="an:confirm_send")],
        [InlineKeyboardButton(text=tr(lang, "an_cancel_btn"),
                              callback_data="an:abort")]])
    if isinstance(target, Message):
        await target.answer(body, reply_markup=b)
    else:
        await safe_edit(target, body, b)


@router.callback_query(F.data == "an:abort")
async def cb_an_abort(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer("❌")
    await state.clear()
    await _render_an_users(cb, c)


@router.callback_query(F.data == "an:confirm_send")
async def cb_an_confirm_send(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    data = await state.get_data()
    text = data.get("announce_text") or ""
    media = data.get("announce_media") or {}
    forward = data.get("announce_forward") or None
    uids = _audience_uids()
    if not uids:
        await cb.answer("⚠️", show_alert=True)
        return
    await cb.answer()
    await state.clear()
    try:
        sched_ts = float(db_get("announce_schedule_ts", "0") or 0)
    except ValueError:
        sched_ts = 0.0
    if sched_ts > now_ts():
        import json
        db_set("announce_scheduled_payload", json.dumps({
            "text": text, "media": media, "forward": forward,
            "chat_id": cb.message.chat.id, "admin_id": cb.from_user.id},
            ensure_ascii=False))
        with contextlib.suppress(Exception):
            await cb.message.answer(
                f"⏰ {esc(db_get('announce_schedule', ''))}")
        return
    asyncio.create_task(_do_user_broadcast(c, cb, uids, text, media, forward))


async def _do_user_broadcast(c, cb, uids, text, media, forward):
    silent = db_get("announce_silent", "0") == "1"
    autodel = db_get("announce_auto_delete", "0") == "1"
    del_after = int(db_get("announce_delete_after", "3600") or "3600")
    delay = float(db_get("broadcast_delay", "0.05") or 0.05)
    total = len(uids)
    sent = failed = 0
    last_update = 0.0
    lang = "fa"
    with contextlib.suppress(Exception):
        user = UserRepo.get(cb.from_user.id)
        if user:
            lang = user_lang(user)
    try:
        progress = await c.bot.send_message(
            cb.message.chat.id,
            f"{tr(lang, 'bc_progress')}\n"
            f"{tr(lang, 'wc_users', total=total)}")
    except Exception:
        progress = None

    for idx, uid in enumerate(uids, 1):
        try:
            sent_msg = None
            if forward:
                with contextlib.suppress(Exception):
                    sent_msg = await c.bot.copy_message(
                        chat_id=uid, from_chat_id=forward["from_chat_id"],
                        message_id=forward["message_id"],
                        disable_notification=silent)
            elif media:
                t = media.get("type")
                cap = (media.get("caption") or "")[:1024]
                if t == "photo":
                    sent_msg = await c.bot.send_photo(
                        uid, media["file_id"], caption=cap,
                        disable_notification=silent)
                elif t == "video":
                    sent_msg = await c.bot.send_video(
                        uid, media["file_id"], caption=cap,
                        disable_notification=silent)
                elif t == "document":
                    sent_msg = await c.bot.send_document(
                        uid, media["file_id"], caption=cap,
                        disable_notification=silent)
                elif t == "audio":
                    sent_msg = await c.bot.send_audio(
                        uid, media["file_id"], caption=cap,
                        disable_notification=silent)
                elif t == "animation":
                    sent_msg = await c.bot.send_animation(
                        uid, media["file_id"], caption=cap,
                        disable_notification=silent)
            else:
                sent_msg = await send_text_safe(
                    c.bot, uid, text, disable_notification=silent)
            if sent_msg:
                sent += 1
                if autodel:
                    _spawn_auto_delete(c, c.bot, uid,
                                       sent_msg.message_id, del_after)
            else:
                failed += 1
        except TelegramForbiddenError:
            failed += 1
            with contextlib.suppress(Exception):
                UserRepo.set_blocked(uid, True)
        except Exception:
            failed += 1

        now = now_ts()
        if progress and now - last_update > 2.5:
            last_update = now
            with contextlib.suppress(Exception):
                await c.bot.edit_message_text(
                    chat_id=cb.message.chat.id,
                    message_id=progress.message_id,
                    text=(f"{tr(lang, 'bc_progress')}\n"
                          f"{tr(lang, 'wc_users', total=total)}\n"
                          f"{tr(lang, 'wc_sent', sent=sent)}\n"
                          f"{tr(lang, 'wc_failed', failed=failed)}\n"
                          f"{tr(lang, 'wc_progress', idx=idx, total=total)}"))
        if delay > 0:
            await asyncio.sleep(delay)

    db_log(cb.from_user.id, "announce_sent",
           f"sent={sent} failed={failed} audience={db_get('announce_audience', 'all')}")
    db_set("announce_last_ts", str(now_ts()))
    try:
        ps = int(db_get("announce_total_sent", "0") or "0")
        pf = int(db_get("announce_total_failed", "0") or "0")
        db_set("announce_total_sent", str(ps + sent))
        db_set("announce_total_failed", str(pf + failed))
    except Exception:
        pass

    if progress:
        with contextlib.suppress(Exception):
            await c.bot.edit_message_text(
                chat_id=cb.message.chat.id, message_id=progress.message_id,
                text=(f"{tr(lang, 'wc_complete')}\n"
                      f"{tr(lang, 'wc_users', total=total)}\n"
                      f"✔️ {sent}\n✖️ {failed}"),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="◀️", callback_data="admin:announce")]]))


@router.callback_query(F.data == "an:schedule_menu")
async def cb_an_schedule_menu(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    cur = db_get("announce_schedule", "") or "—"
    text = f"⏰ <b>{tr(lang, 'an_btn_schedule')}</b>\n\n🕐 {esc(cur)}"
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="✏️", callback_data="an:set_schedule"))
    b.row(InlineKeyboardButton(text="🗑", callback_data="an:clear_schedule"))
    b.row(InlineKeyboardButton(text="◀️", callback_data="an:users_menu"))
    await safe_edit(cb.message, text, b.as_markup())


@router.callback_query(F.data == "an:set_schedule")
async def cb_an_set_schedule(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    await state.set_state(Flow.a_announce_schedule_time)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="◀️", callback_data="an:schedule_menu")]])
    await safe_edit(cb.message, tr(lang, "an_schedule_ask"), kb)


@router.message(Flow.a_announce_schedule_time, F.text)
async def msg_an_sched_time(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    lang = await _admin_lang(c, message.from_user.id)
    val = (message.text or "").strip()
    try:
        ts = time.mktime(time.strptime(val, "%Y-%m-%d %H:%M"))
        if ts < now_ts():
            await message.answer(tr(lang, "schedule_future_required"))
            return
    except Exception:
        await message.answer(tr(lang, "schedule_format"))
        return
    db_set("announce_schedule", val)
    db_set("announce_schedule_ts", str(ts))
    await state.clear()
    await message.answer(f"✅ {esc(val)}")


@router.callback_query(F.data == "an:clear_schedule")
async def cb_an_clear_sched(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    db_set("announce_schedule", "")
    db_set("announce_schedule_ts", "0")
    db_set("announce_scheduled_payload", "")
    await cb.answer("✅")
    await _render_an_users(cb, c)


@router.callback_query(F.data == "an:test")
async def cb_an_test(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    await state.set_state(Flow.a_announce_test)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="◀️", callback_data="an:users_menu")]])
    await safe_edit(cb.message, tr(lang, "an_test_ask"), kb)


@router.message(Flow.a_announce_test, F.text)
async def msg_an_test(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    txt = (message.text or "").strip()
    with contextlib.suppress(Exception):
        await c.bot.send_message(message.chat.id, f"🧪 {esc(txt)}")
    await state.clear()


@router.callback_query(F.data == "an:reset_stats")
async def cb_an_reset_stats(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    db_set("announce_total_sent", "0")
    db_set("announce_total_failed", "0")
    await cb.answer("✅")
    await _render_an_users(cb, c)


@router.callback_query(F.data == "an:stats")
async def cb_an_stats(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    try:
        ts = int(db_get("announce_total_sent", "0") or "0")
        tf = int(db_get("announce_total_failed", "0") or "0")
        ct = int(db_get("announce_channel_total", "0") or "0")
    except Exception:
        ts = tf = ct = 0
    try:
        total = UserRepo.count_all()
        vip = UserRepo.count_vip()
        active = int(get_conn().execute(
            "SELECT COUNT(*) AS c FROM users WHERE downloads>0").fetchone()["c"] or 0)
        inactive = int(get_conn().execute(
            "SELECT COUNT(*) AS c FROM users WHERE downloads=0").fetchone()["c"] or 0)
    except Exception:
        total = vip = active = inactive = 0
    text = tr(lang, "an_stats_title", sent=ts, failed=tf, ch_sent=ct,
              total=total, vip=vip, active=active, inactive=inactive)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="◀️", callback_data="admin:announce")]])
    await safe_edit(cb.message, text, kb)


@router.callback_query(F.data == "an:history")
async def cb_an_history(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    rows = get_conn().execute(
        "SELECT * FROM logs WHERE action IN "
        "('announce_sent', 'announce_channel') "
        "ORDER BY created_at DESC LIMIT 25").fetchall()
    text = "📜\n\n"
    if not rows:
        text += "📭"
    else:
        for r in rows:
            text += f"• {fmt_time(r['created_at'])}\n<code>{esc(str(r['details'] or '')[:80])}</code>\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="◀️", callback_data="admin:announce")]])
    await safe_edit(cb.message, text, kb)



__all__ = [name for name in globals() if not name.startswith("__")]
