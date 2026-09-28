"""Arka Downloader section: RE-DOWNLOAD."""

from .s28_history import *

# ══════════════════════════════════════════════════════════════
# RE-DOWNLOAD
# ══════════════════════════════════════════════════════════════
@router.callback_query(F.data.startswith("redl:"))
async def cb_redownload(cb: CallbackQuery, c: Container):
    job_id = cb.data.split(":", 1)[1]
    old = JobRepo.get(job_id)
    if not old or old.user_id != cb.from_user.id:
        await cb.answer("⛔", show_alert=True)
        return
    user = UserRepo.get(cb.from_user.id)
    lang = user_lang(user)

    is_photo_mode = False
    if old.file_path:
        with contextlib.suppress(Exception):
            suf = Path(old.file_path).suffix.lower()
            if suf in IMAGE_EXTS:
                is_photo_mode = True
    if old.title in ("Image", "Thumbnail"):
        is_photo_mode = True
    if is_direct_image_url(old.url):
        is_photo_mode = True
    is_music_mode = (not is_photo_mode and is_audio_quality(old.quality))

    if not is_limit_exempt(cb.from_user.id):
        mc = int(db_get("max_concurrent", "2"))
        if UserRepo.active_jobs(cb.from_user.id) >= mc:
            await cb.answer(tr(lang, "dl_concurrent", limit=mc),
                            show_alert=True)
            return
        try:
            if is_photo_mode:
                RateRepo.check_and_consume(cb.from_user.id, "photo",
                    int(db_get("max_photo_hour", "30")),
                    int(db_get("max_photo_day", "200")))
            elif is_music_mode:
                RateRepo.check_and_consume(cb.from_user.id, "music",
                    int(db_get("max_music_hour", "30")),
                    int(db_get("max_music_day", "200")))
            else:
                RateRepo.check_and_consume(cb.from_user.id, "video",
                    int(db_get("max_dl_hour", "10")),
                    int(db_get("max_dl_day", "50")))
        except PermissionError as e:
            await cb.answer(tr(lang, str(e)), show_alert=True)
            return

    target_chat = cb.message.chat.id if cb.message else old.chat_id
    new_job = JobRepo.create(user_id=old.user_id, chat_id=target_chat,
                              url=old.url, status=STATUS_ANALYZING)
    clear_cancelled(new_job.job_id)
    UserRepo.bump(cb.from_user.id, "downloads")
    await cb.answer("✅")

    if is_photo_mode:
        try:
            notice = await c.bot.send_message(
                target_chat, tr(lang, "dl_photo_downloading", id=new_job.job_id))
        except Exception:
            return
        try:
            result = await download_photo_only(old.url, new_job.job_id)
            delay = int(db_get("delete_delay", "60"))
            cap = tr(lang, "dl_photo_completed",
                     size=fmt_bytes(result.filesize),
                     id=new_job.job_id, delay=delay)
            sent = await _send_photo_with_compression(
                c.bot, target_chat, result.path, cap, new_job.job_id, lang)
            if sent is None:
                raise DownloadError("Failed to send image")
            with contextlib.suppress(Exception):
                await notice.delete()
            JobRepo.update(new_job.job_id, status=STATUS_COMPLETED,
                           progress=100.0, title="Image",
                           filesize=result.filesize, duration=0,
                           file_path=str(result.path), msg_id=sent.message_id,
                           delete_at=now_ts() + delay, finished_at=now_ts())
            UserRepo.bump(old.user_id, "success_dl")
        except Exception as e:
            JobRepo.update(new_job.job_id, status=STATUS_FAILED, error=str(e),
                           finished_at=now_ts())
            UserRepo.bump(old.user_id, "failed_dl")
            err_text = tr(lang, "dl_photo_failed",
                          error=esc(str(e))[:200], id=new_job.job_id)
            with contextlib.suppress(Exception):
                await notice.edit_text(err_text)
        return

    if is_music_mode:
        try:
            notice = await c.bot.send_message(
                target_chat,
                tr(lang, "dl_music_analyzing", id=new_job.job_id))
        except Exception:
            return
        try:
            info = await analyze_async(old.url)
            JobRepo.update(new_job.job_id, title=info.title,
                           duration=info.duration, filesize=info.filesize,
                           thumbnail=info.thumbnail, status=STATUS_PENDING)
            with contextlib.suppress(Exception):
                await notice.delete()
            cap = (f"🎵 <b>{esc(info.title[:120])}</b>\n"
                   f"⏱ {fmt_duration(info.duration)}\n"
                   f"💾 {fmt_bytes(info.filesize)}\n")
            if info.uploader:
                cap += f"🎤 {esc(info.uploader[:80])}\n"
            cap += f"\n🎵 <code>{new_job.job_id}</code>"
            sp = False
            if db_get("send_thumbnail", "1") == "1" and info.thumbnail:
                try:
                    await c.bot.send_photo(chat_id=target_chat,
                                            photo=info.thumbnail,
                                            caption=cap[:1024])
                    sp = True
                except Exception:
                    pass
            if not sp:
                with contextlib.suppress(Exception):
                    await c.bot.send_message(target_chat, cap[:4096])
            q_msg = await c.bot.send_message(
                target_chat, tr(lang, "dl_select_quality"),
                reply_markup=quality_kb(new_job.job_id, lang, mode="music"))
            JobRepo.update(new_job.job_id, msg_id=q_msg.message_id)
        except DownloadError as e:
            JobRepo.update(new_job.job_id, status=STATUS_FAILED,
                           error=str(e), finished_at=now_ts())
            UserRepo.bump(old.user_id, "failed_dl")
            with contextlib.suppress(Exception):
                await notice.edit_text(
                    tr(lang, "dl_music_failed",
                       error=esc(str(e))[:200], id=new_job.job_id))
        return

    try:
        msg = await c.bot.send_message(
            target_chat,
            f"{tr(lang, 'dl_analyzing')}\n\n🆔 <code>{new_job.job_id}</code>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text=tr(lang, "cancel"),
                    callback_data=safe_cb(f"jback:{new_job.job_id}"))]]))
    except Exception:
        return
    JobRepo.update(new_job.job_id, msg_id=msg.message_id,
                   status=STATUS_ANALYZING)
    try:
        info = await analyze_async(old.url)
    except DownloadError as e:
        JobRepo.update(new_job.job_id, status=STATUS_FAILED, error=str(e),
                       finished_at=now_ts())
        UserRepo.bump(cb.from_user.id, "failed_dl")
        with contextlib.suppress(Exception):
            await msg.edit_text(tr(lang, "dl_analyze_failed"))
        return
    JobRepo.update(new_job.job_id, title=info.title, duration=info.duration,
                   filesize=info.filesize, thumbnail=info.thumbnail,
                   status=STATUS_PENDING)
    with contextlib.suppress(Exception):
        await msg.delete()
    cap = (f"<b>{esc(info.title[:120])}</b>\n"
           f"⏱ {fmt_duration(info.duration)}\n"
           f"💾 {fmt_bytes(info.filesize)}\n")
    if getattr(info, "max_height", 0) > 0:
        cap += tr(lang, "max_height_label", max=info.max_height) + "\n"
    if info.uploader:
        cap += f"👤 {esc(info.uploader[:80])}\n"
    cap += f"\n🆔 <code>{new_job.job_id}</code>"
    ps = False
    if db_get("send_thumbnail", "1") == "1" and info.thumbnail:
        try:
            await c.bot.send_photo(chat_id=target_chat, photo=info.thumbnail,
                                    caption=cap[:1024])
            ps = True
        except Exception:
            pass
    if not ps:
        with contextlib.suppress(Exception):
            await c.bot.send_message(target_chat, cap[:4096])
    if not allowed_qualities():
        JobRepo.update(new_job.job_id, status=STATUS_FAILED,
                       error="no_quality", finished_at=now_ts())
        with contextlib.suppress(Exception):
            await c.bot.send_message(target_chat, tr(lang, "dl_no_quality"))
        return

    avail = getattr(info, "available_qualities", None) or {"best", "audio"}
    q_msg = await c.bot.send_message(
        target_chat, tr(lang, "dl_select_quality"),
        reply_markup=quality_kb(new_job.job_id, lang, available=avail,
                                 mode="video"))
    JobRepo.update(new_job.job_id, msg_id=q_msg.message_id)



__all__ = [name for name in globals() if not name.startswith("__")]
