"""Arka Downloader section: HISTORY."""

from .s27_download import *

# ══════════════════════════════════════════════════════════════
# HISTORY
# ══════════════════════════════════════════════════════════════
@router.callback_query(F.data == "menu:history")
async def cb_history(cb: CallbackQuery, state: FSMContext, c: Container):
    await cb.answer()
    await state.clear()
    await show_history(cb, 1)


@router.callback_query(F.data.startswith("histpg:"))
async def cb_history_page(cb: CallbackQuery, c: Container):
    await cb.answer()
    try:
        page = int(cb.data.split(":", 1)[1])
    except ValueError:
        page = 1
    await show_history(cb, page)


async def show_history(cb: CallbackQuery, page: int = 1):
    user = UserRepo.get(cb.from_user.id)
    if not user:
        return
    lang = user_lang(user)
    per = 10
    page = max(1, page)
    total = JobRepo.count_for_user(user.user_id)
    total_pages = max(1, (total + per - 1) // per)
    jobs = JobRepo.history(user.user_id, limit=per, offset=(page - 1) * per)
    if not jobs:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=tr(lang, "back"),
                                 callback_data="menu:home")]])
        await safe_edit(cb.message, tr(lang, "hist_empty"), kb)
        return
    text = tr(lang, "hist_page_title", page=page, total=total_pages)
    buttons = []
    for j in jobs:
        icon = {"completed": "✅", "failed": "❌", "cancelled": "⚪",
                "downloading": "⬇️", "uploading": "⬆️",
                "queued": "⏳", "analyzing": "🔍"}.get(j.status, "⚙️")
        fav_mark = "⭐ " if FavRepo.is_fav(user.user_id, j.job_id) else ""
        title = (j.title or j.job_id)[:26]
        size_str = fmt_bytes(_effective_filesize(j))
        dur = _effective_duration(j)
        dur_str = fmt_duration(dur) if dur else "—"
        buttons.append([InlineKeyboardButton(
            text=f"{fav_mark}{icon} {title}\n💾 {size_str} | ⏱ {dur_str}",
            callback_data=safe_cb(f"histview:{j.job_id}"))])
    nav = InlineKeyboardBuilder()
    if page > 1:
        nav.button(text="◀️", callback_data=safe_cb(f"histpg:{page - 1}"))
    nav.button(text=f"📄 {page} / {total_pages}", callback_data="noop")
    if page < total_pages:
        nav.button(text="▶️", callback_data=safe_cb(f"histpg:{page + 1}"))
    nav.adjust(3)
    kb_rows = buttons + nav.export()
    kb_rows.append([InlineKeyboardButton(
        text=tr(lang, "hist_clear_btn"),
        callback_data="histclearask")])
    kb_rows.append([InlineKeyboardButton(text=tr(lang, "back"),
                                          callback_data="menu:home")])
    await safe_edit(cb.message, text,
                    InlineKeyboardMarkup(inline_keyboard=kb_rows))


@router.callback_query(F.data.startswith("histview:"))
async def cb_history_view(cb: CallbackQuery, c: Container):
    with contextlib.suppress(Exception):
        await cb.answer()
    user = UserRepo.get(cb.from_user.id)
    if not user:
        return
    lang = user_lang(user)
    jid = cb.data.split(":", 1)[1]
    j = JobRepo.get(jid)
    if not j or j.user_id != user.user_id:
        with contextlib.suppress(Exception):
            await cb.answer("⛔", show_alert=True)
        return
    qn = QUALITY_LABELS.get(lang, QUALITY_LABELS["fa"]).get(
        j.quality, j.quality)
    icon = {"completed": "✅", "failed": "❌", "cancelled": "⚪",
            "downloading": "⬇️", "uploading": "⬆️",
            "queued": "⏳", "analyzing": "🔍"}.get(j.status, "⚙️")
    size = _effective_filesize(j)
    duration = _effective_duration(j)
    file_exists = bool(j.file_path and Path(j.file_path).exists())
    text = tr(lang, "hist_item_detail",
              title=esc((j.title or "-")[:80]), id=j.job_id,
              quality=esc(qn), status=f"{icon} {esc(j.status)}",
              size=fmt_bytes(size), duration=fmt_duration(duration),
              date=fmt_time(j.started_at or j.created_at or now_ts()))
    buttons = []
    if file_exists:
        buttons.append([InlineKeyboardButton(
            text=tr(lang, "resend"),
            callback_data=safe_cb(f"sendfile:{jid}"))])
    is_fav = FavRepo.is_fav(user.user_id, jid)
    fav_btn_text = (tr(lang, "fav_remove_btn") if is_fav
                    else tr(lang, "fav_add_btn"))
    fav_cb = f"histunfav:{jid}" if is_fav else f"histfav:{jid}"
    buttons.append([InlineKeyboardButton(
        text=fav_btn_text, callback_data=safe_cb(fav_cb))])
    buttons.append([InlineKeyboardButton(
        text=tr(lang, "btn_redo"),
        callback_data=safe_cb(f"redl:{jid}"))])
    buttons.append([InlineKeyboardButton(
        text=tr(lang, "hist_delete_btn"),
        callback_data=safe_cb(f"histdel:{jid}"))])
    buttons.append([InlineKeyboardButton(
        text=tr(lang, "back_to_history"),
        callback_data="menu:history")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    try:
        await cb.message.edit_text(text, reply_markup=kb)
        return
    except TelegramBadRequest as e:
        s = str(e).lower()
        if "not modified" in s:
            return
        if "no text" in s or "caption" in s:
            with contextlib.suppress(Exception):
                await cb.message.edit_caption(caption=text[:1024], reply_markup=kb)
                return
    except Exception:
        pass
    with contextlib.suppress(Exception):
        await cb.message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("sendfile:"))
async def cb_sendfile(cb: CallbackQuery, c: Container):
    jid = cb.data.split(":", 1)[1]
    j = JobRepo.get(jid)
    if not j or j.user_id != cb.from_user.id:
        await cb.answer("⛔", show_alert=True)
        return
    user = UserRepo.get(cb.from_user.id)
    lang = user_lang(user)
    if not j.file_path or not Path(j.file_path).exists():
        await cb.answer("⚠️", show_alert=True)
        return
    await cb.answer("📤...")
    path = Path(j.file_path)
    size = path.stat().st_size
    duration_final = _effective_duration(j)
    if duration_final <= 0:
        duration_final = await asyncio.to_thread(_probe_duration, path) or 0
    qn = QUALITY_LABELS.get(lang, QUALITY_LABELS["fa"]).get(
        j.quality, j.quality)
    delay = int(db_get("delete_delay", "60"))
    caption = tr(lang, "dl_completed",
                 title=esc((j.title or "Video")[:120]), quality=esc(qn),
                 size=fmt_bytes(size), duration=fmt_duration(duration_final),
                 id=j.job_id, delay=delay)
    is_audio = is_audio_quality(j.quality) or \
        path.suffix.lower() in (".mp3", ".m4a", ".opus",
                                ".ogg", ".flac", ".wav", ".aac")
    if is_image_file(path):
        cap_p = tr(lang, "dl_photo_completed", size=fmt_bytes(size),
                   id=j.job_id, delay=delay)
        with contextlib.suppress(Exception):
            await _send_photo_with_compression(
                c.bot, cb.message.chat.id, path, cap_p, j.job_id, lang)
        return
    try:
        if is_audio:
            await c.bot.send_audio(
                chat_id=cb.message.chat.id, audio=FSInputFile(str(path)),
                caption=caption[:1024], title=(j.title or "Audio")[:60],
                duration=duration_final, request_timeout=1800)
        else:
            await c.bot.send_video(
                chat_id=cb.message.chat.id, video=FSInputFile(str(path)),
                caption=caption[:1024], supports_streaming=True,
                duration=duration_final, request_timeout=1800)
    except Exception as e:
        with contextlib.suppress(Exception):
            await cb.message.answer(f"❌ {esc(str(e))}")


@router.callback_query(F.data.startswith("histfav:"))
async def cb_hist_add_fav(cb: CallbackQuery, c: Container):
    user = UserRepo.get(cb.from_user.id)
    if not user:
        await cb.answer()
        return
    lang = user_lang(user)
    jid = cb.data.split(":", 1)[1]
    j = JobRepo.get(jid)
    if not j or j.user_id != user.user_id:
        await cb.answer("⛔", show_alert=True)
        return
    if FavRepo.is_fav(user.user_id, jid):
        await cb.answer(tr(lang, "fav_already"), show_alert=True)
        return
    FavRepo.add(user.user_id, jid)
    await cb.answer(tr(lang, "fav_add_ok"), show_alert=True)
    await cb_history_view(cb, c)


@router.callback_query(F.data.startswith("histunfav:"))
async def cb_hist_del_fav(cb: CallbackQuery, c: Container):
    user = UserRepo.get(cb.from_user.id)
    if not user:
        await cb.answer()
        return
    lang = user_lang(user)
    jid = cb.data.split(":", 1)[1]
    if not FavRepo.is_fav(user.user_id, jid):
        await cb.answer(tr(lang, "fav_not_in"), show_alert=True)
        return
    FavRepo.remove(user.user_id, jid)
    await cb.answer(tr(lang, "fav_remove_ok"), show_alert=True)
    await cb_history_view(cb, c)


@router.callback_query(F.data.startswith("histdel:"))
async def cb_hist_delete(cb: CallbackQuery, c: Container):
    user = UserRepo.get(cb.from_user.id)
    if not user:
        await cb.answer()
        return
    lang = user_lang(user)
    jid = cb.data.split(":", 1)[1]
    j = JobRepo.get(jid)
    if not j or j.user_id != user.user_id:
        await cb.answer("⛔", show_alert=True)
        return
    FavRepo.remove(user.user_id, jid)
    _purge_job_files(get_conn().execute(
        "SELECT job_id, file_path FROM jobs WHERE job_id=? AND user_id=? "
        "AND status NOT IN ('queued','analyzing','downloading','uploading')",
        (jid, user.user_id)).fetchall())
    get_conn().execute("DELETE FROM jobs WHERE job_id=? AND user_id=?",
                       (jid, user.user_id))
    await cb.answer(tr(lang, "hist_delete_ok"), show_alert=True)
    await show_history(cb, 1)


@router.callback_query(F.data == "histclearask")
async def cb_hist_clear_ask(cb: CallbackQuery, c: Container):
    await cb.answer()
    user = UserRepo.get(cb.from_user.id)
    if not user:
        return
    lang = user_lang(user)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=tr(lang, "yes"),
                              callback_data="histclearyes")],
        [InlineKeyboardButton(text=tr(lang, "no"),
                              callback_data="menu:history")]])
    await safe_edit(cb.message, tr(lang, "hist_clear_confirm"), kb)


@router.callback_query(F.data == "histclearyes")
async def cb_hist_clear_yes(cb: CallbackQuery, c: Container):
    user = UserRepo.get(cb.from_user.id)
    if not user:
        await cb.answer()
        return
    lang = user_lang(user)
    r = get_conn().execute("SELECT COUNT(*) AS c FROM jobs WHERE user_id=?",
                            (user.user_id,)).fetchone()
    count = int(r["c"] or 0)
    _purge_job_files(get_conn().execute(
        "SELECT job_id, file_path FROM jobs WHERE user_id=? "
        "AND status NOT IN ('queued','analyzing','downloading','uploading')",
        (user.user_id,)).fetchall())
    get_conn().execute("DELETE FROM jobs WHERE user_id=?", (user.user_id,))
    get_conn().execute("DELETE FROM favorites WHERE user_id=?",
                       (user.user_id,))
    await cb.answer(tr(lang, "hist_cleared", count=count), show_alert=True)
    await show_history(cb, 1)



__all__ = [name for name in globals() if not name.startswith("__")]
