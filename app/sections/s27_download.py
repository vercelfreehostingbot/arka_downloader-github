"""Arka Downloader section: DOWNLOAD."""

from .s26_language import *

# ══════════════════════════════════════════════════════════════
# DOWNLOAD
# ══════════════════════════════════════════════════════════════
@router.callback_query(F.data == "menu:download")
async def cb_download(cb: CallbackQuery, state: FSMContext, c: Container):
    await cb.answer()
    await state.clear()
    user = UserRepo.get(cb.from_user.id)
    if not user:
        return
    lang = user_lang(user)
    if not await check_membership(user.user_id):
        await send_join_prompt(cb.message, lang)
        return

    photo_enabled = db_get("photo_download_enabled", "1") == "1"
    video_enabled = db_get("video_download_enabled", "1") == "1"
    music_enabled = db_get("music_download_enabled", "1") == "1"

    available = []
    if photo_enabled: available.append("photo")
    if video_enabled: available.append("video")
    if music_enabled: available.append("music")

    if not available:
        await safe_edit(cb.message, "⚠️",
            InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text=tr(lang, "back"),
                                     callback_data="menu:home")]]))
        return
    if len(available) == 1:
        return await _enter_download_mode(cb, state, c, available[0])

    rows = []
    if photo_enabled:
        rows.append([InlineKeyboardButton(
            text=tr(lang, "dl_btn_photo"), callback_data="dl:photo")])
    if video_enabled:
        rows.append([InlineKeyboardButton(
            text=tr(lang, "dl_btn_video"), callback_data="dl:video")])
    if music_enabled:
        rows.append([InlineKeyboardButton(
            text=tr(lang, "dl_btn_music"), callback_data="dl:music")])
    rows.append([InlineKeyboardButton(
        text=tr(lang, "back"), callback_data="menu:home")])

    await safe_edit(cb.message, tr(lang, "dl_choose_type"),
                    InlineKeyboardMarkup(inline_keyboard=rows))


@router.callback_query(F.data == "dl:photo")
async def cb_dl_photo(cb: CallbackQuery, state: FSMContext, c: Container):
    await cb.answer()
    await _enter_download_mode(cb, state, c, "photo")


@router.callback_query(F.data == "dl:video")
async def cb_dl_video(cb: CallbackQuery, state: FSMContext, c: Container):
    await cb.answer()
    await _enter_download_mode(cb, state, c, "video")


@router.callback_query(F.data == "dl:music")
async def cb_dl_music(cb: CallbackQuery, state: FSMContext, c: Container):
    await cb.answer()
    await _enter_download_mode(cb, state, c, "music")


async def _enter_download_mode(cb: CallbackQuery, state: FSMContext,
                                c: Container, mode: str):
    user = UserRepo.get(cb.from_user.id)
    if not user:
        return
    lang = user_lang(user)
    if not await check_membership(user.user_id):
        await send_join_prompt(cb.message, lang)
        return
    await state.set_state(Flow.dl_waiting_url)
    await state.update_data(dl_mode=mode)

    if mode == "photo":
        text = tr(lang, "dl_photo_center")
    elif mode == "music":
        text = tr(lang, "dl_music_center")
    else:
        text = tr(lang, "dl_video_center")

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "dl_back_to_types"),
                             callback_data="menu:download")]])
    await safe_edit(cb.message, text, kb)


@router.message(Flow.dl_waiting_url, F.text)
async def handle_url(message: Message, state: FSMContext, c: Container):
    u = message.from_user
    if not u:
        return
    user = UserRepo.get(u.id)
    if not user:
        return
    lang = user_lang(user)
    if not await check_membership(u.id):
        await send_join_prompt(message, lang)
        return
    data = await state.get_data()
    mode = data.get("dl_mode", "video")
    url = (message.text or "").strip()
    if not is_valid_url(url):
        await message.answer(tr(lang, "dl_invalid"))
        return

    cd_left = cooldown_remaining(u.id)
    if cd_left:
        await message.answer(tr(lang, "dl_cooldown", sec=cd_left))
        return

    max_concurrent = int(db_get("max_concurrent", "2"))
    if UserRepo.active_jobs(u.id) >= max_concurrent and not is_limit_exempt(u.id):
        await message.answer(tr(lang, "dl_concurrent", limit=max_concurrent))
        await state.clear()
        return

    if not is_limit_exempt(u.id):
        try:
            if mode == "photo":
                hl = int(db_get("max_photo_hour", "30"))
                dl = int(db_get("max_photo_day", "200"))
            elif mode == "music":
                hl = int(db_get("max_music_hour", "30"))
                dl = int(db_get("max_music_day", "200"))
            else:
                hl = int(db_get("max_dl_hour", "10"))
                dl = int(db_get("max_dl_day", "50"))
            RateRepo.check_and_consume(u.id, mode, hl, dl)
        except PermissionError as e:
            await message.answer(tr(lang, str(e)))
            await state.clear()
            return

    job = JobRepo.create(user_id=u.id, chat_id=message.chat.id, url=url,
                         status=STATUS_ANALYZING)
    UserRepo.bump(u.id, "downloads")
    await state.clear()

    if mode == "photo":
        notice = await message.answer(
            tr(lang, "dl_photo_downloading", id=job.job_id))
        try:
            result = await download_photo_only(url, job.job_id)
            delay = int(db_get("delete_delay", "60"))
            cap = tr(lang, "dl_photo_completed",
                     size=fmt_bytes(result.filesize),
                     id=job.job_id, delay=delay)
            sent = await _send_photo_with_compression(
                c.bot, message.chat.id, result.path, cap, job.job_id, lang)
            if sent is None:
                raise DownloadError("Failed to send image")
            with contextlib.suppress(Exception):
                await notice.delete()
            JobRepo.update(job.job_id, status=STATUS_COMPLETED, progress=100.0,
                           title="Image", filesize=result.filesize, duration=0,
                           file_path=str(result.path), msg_id=sent.message_id,
                           delete_at=now_ts() + delay, finished_at=now_ts())
            UserRepo.bump(u.id, "success_dl")
        except Exception as e:
            logging.warning(f"[photo] failed: {e}")
            JobRepo.update(job.job_id, status=STATUS_FAILED, error=str(e),
                           finished_at=now_ts())
            UserRepo.bump(u.id, "failed_dl")
            err_text = tr(lang, "dl_photo_failed",
                          error=esc(str(e))[:200], id=job.job_id)
            edited = False
            with contextlib.suppress(Exception):
                await notice.edit_text(err_text)
                edited = True
            if not edited:
                with contextlib.suppress(Exception):
                    await message.answer(err_text)
        if db_get("keep_state_after_download", "1") == "1":
            await state.set_state(Flow.dl_waiting_url)
            await state.update_data(dl_mode="photo")
        return

    if mode == "music":
        analyzing = await message.answer(
            f"{tr(lang, 'dl_music_analyzing', id=job.job_id)}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text=tr(lang, "cancel"),
                    callback_data=safe_cb(f"jback:{job.job_id}"))]]))
        JobRepo.update(job.job_id, msg_id=analyzing.message_id)

        info = None
        analyze_err = ""
        try:
            info = await analyze_async(url)
        except DownloadError as e:
            analyze_err = str(e)
        except Exception as e:
            analyze_err = str(e)
            logging.exception("music analyze crashed")

        if info is None:
            try:
                result = await download_music_only(url, job.job_id, "audio")
                with contextlib.suppress(Exception):
                    await analyzing.delete()
                delay = int(db_get("delete_delay", "60"))
                artist = result.artist or tr(lang, "artist_unknown")
                cap = tr(lang, "dl_music_completed",
                         title=esc(result.title[:80]),
                         artist=esc(artist[:60]),
                         size=fmt_bytes(result.filesize),
                         duration=fmt_duration(result.duration),
                         id=job.job_id, delay=delay)
                sent = await _send_music_file(c.bot, message.chat.id, result, cap)
                if sent is None:
                    raise DownloadError("Failed to send audio")
                JobRepo.update(job.job_id, status=STATUS_COMPLETED,
                               progress=100.0, title=result.title,
                               filesize=result.filesize, quality="audio",
                               duration=result.duration,
                               file_path=str(result.path),
                               msg_id=sent.message_id,
                               delete_at=now_ts() + delay,
                               finished_at=now_ts())
                UserRepo.bump(u.id, "success_dl")
            except Exception as e:
                JobRepo.update(job.job_id, status=STATUS_FAILED,
                               error=analyze_err or str(e),
                               finished_at=now_ts())
                UserRepo.bump(u.id, "failed_dl")
                with contextlib.suppress(Exception):
                    await analyzing.edit_text(
                        tr(lang, "dl_music_failed",
                           error=esc(analyze_err or str(e))[:200],
                           id=job.job_id),
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                            InlineKeyboardButton(text=tr(lang, "back"),
                                                 callback_data="menu:home")]]))
            if db_get("keep_state_after_download", "1") == "1":
                await state.set_state(Flow.dl_waiting_url)
                await state.update_data(dl_mode="music")
            return

        current = JobRepo.get(job.job_id)
        if (is_cancelled(job.job_id) or not current
                or current.status == STATUS_CANCELLED):
            return
        JobRepo.update(job.job_id, title=info.title, duration=info.duration,
                       filesize=info.filesize, thumbnail=info.thumbnail,
                       status=STATUS_PENDING)
        with contextlib.suppress(Exception):
            await analyzing.delete()

        cap = (f"🎵 <b>{esc(info.title[:120])}</b>\n"
               f"⏱ {fmt_duration(info.duration)}\n"
               f"💾 {fmt_bytes(info.filesize)}\n")
        if info.uploader:
            cap += f"🎤 {esc(info.uploader[:80])}\n"
        cap += f"\n🎵 <code>{job.job_id}</code>"

        sent_p = False
        if db_get("send_thumbnail", "1") == "1" and info.thumbnail:
            try:
                await message.answer_photo(
                    photo=info.thumbnail, caption=cap[:1024])
                sent_p = True
            except Exception:
                pass
        if not sent_p:
            with contextlib.suppress(Exception):
                await message.answer(cap[:4096])

        q_msg = await message.answer(
            tr(lang, "dl_select_quality"),
            reply_markup=quality_kb(job.job_id, lang, mode="music"))
        JobRepo.update(job.job_id, msg_id=q_msg.message_id)
        return

    # VIDEO
    analyzing = await message.answer(
        f"{tr(lang, 'dl_analyzing')}\n\n🆔 <code>{job.job_id}</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=tr(lang, "cancel"),
                                 callback_data=safe_cb(f"jback:{job.job_id}"))]]))
    JobRepo.update(job.job_id, msg_id=analyzing.message_id)
    info = None
    analyze_err = ""
    try:
        info = await analyze_async(url)
    except DownloadError as e:
        analyze_err = str(e)
    except Exception as e:
        analyze_err = str(e)
        logging.exception("analyze crashed")

    if info is None:
        try:
            result = await download_video_only(url, job.job_id)
            with contextlib.suppress(Exception):
                await analyzing.delete()
            delay = int(db_get("delete_delay", "60"))
            dur = result.duration or 0
            if dur <= 0:
                dur = await asyncio.to_thread(
                    _probe_duration, result.path) or 0
            size = result.filesize
            try:
                mx = int(db_get("max_file_size_mb", "2048"))
            except (TypeError, ValueError):
                mx = 2048
            if size > mx * 1024 * 1024:
                raise DownloadError("File too large")
            cap = tr(lang, "dl_completed",
                     title=esc(result.title[:80]), quality="best",
                     size=fmt_bytes(size), duration=fmt_duration(dur),
                     id=job.job_id, delay=delay)
            sent = None
            with contextlib.suppress(Exception):
                sent = await c.bot.send_video(
                    chat_id=message.chat.id,
                    video=FSInputFile(str(result.path)),
                    caption=cap[:1024], supports_streaming=True,
                    duration=dur, request_timeout=1800)
            if sent is None:
                sent = await c.bot.send_document(
                    chat_id=message.chat.id,
                    document=FSInputFile(str(result.path)),
                    caption=cap[:1024], request_timeout=1800)
            JobRepo.update(job.job_id, status=STATUS_COMPLETED, progress=100.0,
                           title=result.title, filesize=size, duration=dur,
                           file_path=str(result.path), msg_id=sent.message_id,
                           delete_at=now_ts() + delay, finished_at=now_ts())
            UserRepo.bump(u.id, "success_dl")
            if db_get("keep_state_after_download", "1") == "1":
                await state.set_state(Flow.dl_waiting_url)
                await state.update_data(dl_mode="video")
            return
        except Exception as e:
            JobRepo.update(job.job_id, status=STATUS_FAILED,
                           error=analyze_err or str(e),
                           finished_at=now_ts())
            UserRepo.bump(u.id, "failed_dl")
            with contextlib.suppress(Exception):
                await analyzing.edit_text(
                    tr(lang, "dl_analyze_failed"),
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton(text=tr(lang, "back"),
                                             callback_data="menu:home")]]))
            return

    current = JobRepo.get(job.job_id)
    if (is_cancelled(job.job_id) or not current
            or current.status == STATUS_CANCELLED):
        return
    JobRepo.update(job.job_id, title=info.title, duration=info.duration,
                   filesize=info.filesize, thumbnail=info.thumbnail,
                   status=STATUS_PENDING)
    with contextlib.suppress(Exception):
        await analyzing.delete()

    cap = (f"<b>{esc(info.title[:120])}</b>\n"
           f"⏱ {fmt_duration(info.duration)}\n"
           f"💾 {fmt_bytes(info.filesize)}\n")
    if getattr(info, "max_height", 0) > 0:
        cap += tr(lang, "max_height_label", max=info.max_height) + "\n"
    if info.uploader:
        cap += f"👤 {esc(info.uploader[:80])}\n"
    cap += f"\n🆔 <code>{job.job_id}</code>"
    preview_sent = False
    if db_get("send_thumbnail", "1") == "1" and info.thumbnail:
        try:
            await message.answer_photo(photo=info.thumbnail, caption=cap[:1024])
            preview_sent = True
        except Exception:
            pass
    if not preview_sent:
        with contextlib.suppress(Exception):
            await message.answer(cap[:4096])
    if not allowed_qualities():
        await message.answer(tr(lang, "dl_no_quality"))
        JobRepo.update(job.job_id, status=STATUS_FAILED,
                       error="no_quality", finished_at=now_ts())
        return

    avail = getattr(info, "available_qualities", None) or {"best", "audio"}
    max_h = getattr(info, "max_height", 0)
    quality_hint = ""
    if max_h > 0:
        quality_hint = tr(lang, "qualities_available_hint", max=max_h)

    q_msg = await message.answer(
        tr(lang, "dl_select_quality") + quality_hint,
        reply_markup=quality_kb(job.job_id, lang, available=avail,
                                 mode="video"))
    JobRepo.update(job.job_id, msg_id=q_msg.message_id)


@router.callback_query(F.data.startswith("q:"))
async def cb_quality(cb: CallbackQuery, c: Container):
    parts = cb.data.split(":")
    if len(parts) != 3:
        await cb.answer()
        return
    _, job_id, quality = parts
    if quality not in VIDEO_QUALITIES:
        await cb.answer()
        return
    job = JobRepo.get(job_id)
    if not job or job.user_id != cb.from_user.id:
        await cb.answer("⛔", show_alert=True)
        return
    if job.status in (STATUS_CANCELLED, STATUS_COMPLETED):
        await cb.answer("⚠️", show_alert=True)
        return
    if quality not in allowed_qualities():
        await cb.answer("Not enabled", show_alert=True)
        return
    await cb.answer()
    clear_cancelled(job_id)
    JobRepo.update(job_id, quality=quality, status=STATUS_QUEUED, error=None)
    user = UserRepo.get(cb.from_user.id)
    lang = user_lang(user)
    qn = QUALITY_LABELS.get(lang, QUALITY_LABELS["fa"]).get(quality, quality)
    await safe_edit(cb.message, tr(lang, "dl_queued", quality=esc(qn), id=job_id))
    await c.job_queue.put(job_id)


@router.callback_query(F.data.startswith("mq:"))
async def cb_music_quality(cb: CallbackQuery, c: Container):
    parts = cb.data.split(":")
    if len(parts) != 3:
        await cb.answer()
        return
    _, job_id, quality = parts
    if not is_audio_quality(quality):
        await cb.answer()
        return
    job = JobRepo.get(job_id)
    if not job or job.user_id != cb.from_user.id:
        await cb.answer("⛔", show_alert=True)
        return
    if job.status in (STATUS_CANCELLED, STATUS_COMPLETED):
        await cb.answer("⚠️", show_alert=True)
        return
    if quality not in allowed_qualities():
        await cb.answer("Not enabled", show_alert=True)
        return
    await cb.answer()
    clear_cancelled(job_id)
    JobRepo.update(job_id, quality=quality, status=STATUS_QUEUED, error=None)
    user = UserRepo.get(cb.from_user.id)
    lang = user_lang(user)
    qn = QUALITY_LABELS.get(lang, QUALITY_LABELS["fa"]).get(quality, quality)
    await safe_edit(cb.message,
                    tr(lang, "dl_queued", quality=esc(qn), id=job_id))
    await c.job_queue.put(job_id)


@router.callback_query(F.data.startswith("jcancel:"))
async def cb_job_cancel(cb: CallbackQuery, c: Container):
    job_id = cb.data.split(":", 1)[1]
    job = JobRepo.get(job_id)
    if not job or job.user_id != cb.from_user.id:
        await cb.answer("⛔", show_alert=True)
        return
    await cb.answer()
    mark_cancelled(job_id)
    JobRepo.update(job_id, status=STATUS_CANCELLED, finished_at=now_ts())
    user = UserRepo.get(cb.from_user.id)
    lang = user_lang(user)
    await safe_edit(cb.message, tr(lang, "dl_cancelled"))


@router.callback_query(F.data.startswith("jback:"))
async def cb_job_back(cb: CallbackQuery, state: FSMContext, c: Container):
    await cb.answer()
    await state.clear()
    job_id = cb.data.split(":", 1)[1]
    job = JobRepo.get(job_id)
    if job and job.user_id == cb.from_user.id and job.status in (
            STATUS_QUEUED, STATUS_ANALYZING, STATUS_PENDING):
        mark_cancelled(job_id)
        JobRepo.update(job_id, status=STATUS_CANCELLED, finished_at=now_ts())
    user = UserRepo.get(cb.from_user.id)
    if not user:
        return
    await send_home(cb, user, edit=True)



__all__ = [name for name in globals() if not name.startswith("__")]
