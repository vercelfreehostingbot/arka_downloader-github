"""Arka Downloader section: JOB PIPELINE."""

from .s22_helpers import *

# ══════════════════════════════════════════════════════════════
# JOB PIPELINE
# ══════════════════════════════════════════════════════════════
async def update_progress(c: Container, job_id: str, pct: float,
                          speed: str, eta: str):
    job = JobRepo.get(job_id)
    if not job or not job.msg_id:
        return
    now = now_ts()
    last = c.last_progress.get(job_id, 0)
    if pct < 100 and (now - last < 1.5):
        return
    if pct >= 100:
        c.last_progress.pop(job_id, None)
    else:
        c.last_progress[job_id] = now

    JobRepo.update(job_id, progress=pct, speed=speed, eta=eta)
    user = UserRepo.get(job.user_id)
    lang = user_lang(user)
    text = tr(lang, "dl_downloading",
              title=esc((job.title or "...")[:80]),
              pct=pct, bar=progress_bar(pct),
              speed=speed, eta=eta, id=job_id)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "cancel"),
                             callback_data=safe_cb(f"jcancel:{job_id}"))]])
    with contextlib.suppress(Exception):
        await c.bot.edit_message_text(
            chat_id=job.chat_id, message_id=job.msg_id,
            text=text, reply_markup=kb)


async def upload_result(c: Container, job_id: str, result: DownloadResult):
    job = JobRepo.get(job_id)
    if not job:
        return
    if is_cancelled(job_id):
        JobRepo.update(job_id, status=STATUS_CANCELLED, finished_at=now_ts())
        return
    if job.status == STATUS_COMPLETED:
        return

    path = result.path
    if not path.exists():
        raise DownloadError("File not found")

    max_mb = int(db_get("max_file_size_mb", "2048"))
    size = path.stat().st_size
    user = UserRepo.get(job.user_id)
    lang = user_lang(user)

    if size > max_mb * 1024 * 1024:
        JobRepo.update(job_id, status=STATUS_FAILED, error="too large",
                       finished_at=now_ts())
        UserRepo.bump(job.user_id, "failed_dl")
        with contextlib.suppress(Exception):
            await c.bot.send_message(job.chat_id, tr(lang, "dl_too_large"))
        return

    qn = QUALITY_LABELS.get(lang, QUALITY_LABELS["fa"]).get(
        job.quality, job.quality)
    delay = int(db_get("delete_delay", "60"))

    duration_final = result.duration or job.duration or 0
    if duration_final <= 0:
        duration_final = await asyncio.to_thread(_probe_duration, path) or 0

    caption = tr(lang, "dl_completed",
                 title=esc(result.title[:120]), quality=esc(qn),
                 size=fmt_bytes(result.filesize),
                 duration=fmt_duration(duration_final),
                 id=job_id, delay=delay)

    sent = None
    is_audio = is_audio_quality(job.quality) or \
        path.suffix.lower() in (".mp3", ".m4a", ".opus",
                                ".ogg", ".flac", ".wav", ".aac")

    if is_image_file(path):
        cap_p = tr(lang, "dl_photo_completed",
                   size=fmt_bytes(size), id=job_id, delay=delay)
        sent = await _send_photo_with_compression(
            c.bot, job.chat_id, path, cap_p, job_id, lang)
        if sent:
            JobRepo.update(
                job_id, status=STATUS_COMPLETED, progress=100.0,
                msg_id=sent.message_id, delete_at=now_ts() + delay,
                finished_at=now_ts(), filesize=size, file_path=str(path),
                duration=duration_final or 0)
            UserRepo.bump(job.user_id, "success_dl")
            return

    if is_audio:
        artist_lbl = result.artist or "Arka Downloader"
        with contextlib.suppress(Exception):
            kwargs = {
                "chat_id": job.chat_id,
                "audio": FSInputFile(str(path)),
                "caption": caption[:1024],
                "title": (result.title or "Audio")[:60],
                "performer": str(artist_lbl)[:60],
                "duration": duration_final,
                "request_timeout": 1800,
            }
            if result.thumbnail_path and result.thumbnail_path.exists():
                try:
                    kwargs["thumbnail"] = FSInputFile(
                        str(result.thumbnail_path))
                    sent = await c.bot.send_audio(**kwargs)
                except Exception:
                    kwargs.pop("thumbnail", None)
                    sent = await c.bot.send_audio(**kwargs)
            else:
                sent = await c.bot.send_audio(**kwargs)

    if sent is None and not is_audio and size <= max_mb * 1024 * 1024:
        with contextlib.suppress(Exception):
            sent = await c.bot.send_video(
                chat_id=job.chat_id, video=FSInputFile(str(path)),
                caption=caption[:1024], supports_streaming=True,
                duration=duration_final, request_timeout=1800)

    if sent is None:
        try:
            sent = await c.bot.send_document(
                chat_id=job.chat_id, document=FSInputFile(str(path)),
                caption=caption[:1024], request_timeout=1800)
        except Exception as e:
            err_str = str(e).lower()
            if "timeout" in err_str or "timed out" in err_str:
                await asyncio.sleep(5)
                JobRepo.update(
                    job_id, status=STATUS_COMPLETED, progress=100.0,
                    delete_at=now_ts() + delay, finished_at=now_ts(),
                    filesize=result.filesize,
                    duration=duration_final or 0, file_path=str(path))
                UserRepo.bump(job.user_id, "success_dl")
                return
            JobRepo.update(job_id, status=STATUS_FAILED, error=str(e),
                           finished_at=now_ts())
            UserRepo.bump(job.user_id, "failed_dl")
            with contextlib.suppress(Exception):
                await c.bot.send_message(
                    job.chat_id, tr(lang, "dl_failed", id=job_id))
            return

    JobRepo.update(
        job_id, status=STATUS_COMPLETED, progress=100.0,
        msg_id=sent.message_id, delete_at=now_ts() + delay,
        finished_at=now_ts(), filesize=result.filesize,
        duration=duration_final or 0, file_path=str(path))
    UserRepo.bump(job.user_id, "success_dl")

    with contextlib.suppress(Exception):
        for sub in path.parent.glob("*.srt"):
            await c.bot.send_document(
                chat_id=job.chat_id, document=FSInputFile(str(sub)),
                caption=tr(lang, "subtitle_label"))
            break


async def process_job(c: Container, job_id: str):
    job = JobRepo.get(job_id)
    if not job or job.status in (STATUS_CANCELLED, STATUS_COMPLETED):
        return
    cur = get_conn().execute(
        "UPDATE jobs SET status=?, started_at=? WHERE job_id=? AND status=?",
        (STATUS_DOWNLOADING, now_ts(), job_id, STATUS_QUEUED))
    if cur.rowcount == 0:
        return
    clear_cancelled(job_id)
    max_retries = int(db_get("max_retries", "2"))
    quality = job.quality or "best"
    attempts = 0
    while attempts <= max_retries:
        if is_cancelled(job_id):
            JobRepo.update(job_id, status=STATUS_CANCELLED, finished_at=now_ts())
            return
        attempts += 1
        JobRepo.update(job_id, status=STATUS_DOWNLOADING, started_at=now_ts())

        async def progress_cb(p, s, e):
            await update_progress(c, job_id, p, s, e)

        try:
            loop = asyncio.get_running_loop()
            result = await asyncio.to_thread(
                download_sync, job_id, job.url, quality, loop,
                progress_cb, is_cancelled)
            if is_cancelled(job_id):
                JobRepo.update(job_id, status=STATUS_CANCELLED)
                return
            JobRepo.update(job_id, status=STATUS_UPLOADING,
                           progress=100.0, file_path=str(result.path))
            for up_try in range(max_retries + 1):
                try:
                    await upload_result(c, job_id, result)
                    break
                except DownloadCancelled:
                    JobRepo.update(job_id, status=STATUS_CANCELLED,
                                   finished_at=now_ts())
                    return
                except Exception as ue:
                    logging.error(
                        f"upload_result error (try {up_try + 1}): {ue}")
                    final = JobRepo.get(job_id)
                    if final and final.status in (
                            STATUS_COMPLETED, STATUS_FAILED, STATUS_CANCELLED):
                        break
                    if up_try < max_retries:
                        await asyncio.sleep(2)
            final = JobRepo.get(job_id)
            if final and final.status in (STATUS_COMPLETED, STATUS_FAILED,
                                          STATUS_CANCELLED):
                return
            JobRepo.update(job_id, status=STATUS_FAILED, error="upload_failed",
                           finished_at=now_ts())
            UserRepo.bump(job.user_id, "failed_dl")
            user = UserRepo.get(job.user_id)
            lang = user_lang(user)
            with contextlib.suppress(Exception):
                await c.bot.send_message(
                    job.chat_id, tr(lang, "dl_failed", id=job_id))
            return
        except DownloadCancelled:
            JobRepo.update(job_id, status=STATUS_CANCELLED, finished_at=now_ts())
            return
        except Exception as e:
            logging.warning(f"Job {job_id} attempt {attempts} failed: {e}")
            if attempts > max_retries:
                final = JobRepo.get(job_id)
                if final and final.status == STATUS_COMPLETED:
                    return
                JobRepo.update(job_id, status=STATUS_FAILED, error=str(e),
                               finished_at=now_ts())
                UserRepo.bump(job.user_id, "failed_dl")
                user = UserRepo.get(job.user_id)
                lang = user_lang(user)
                with contextlib.suppress(Exception):
                    await c.bot.send_message(
                        job.chat_id, tr(lang, "dl_failed", id=job_id))
                return
            await asyncio.sleep(2)


async def worker(c: Container, worker_id: int):
    while not c.shutdown_event.is_set():
        try:
            job_id = await asyncio.wait_for(c.job_queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            continue
        try:
            await process_job(c, job_id)
        except Exception as e:
            logging.error(f"Worker {worker_id} crashed: {e}")
        finally:
            with contextlib.suppress(Exception):
                c.job_queue.task_done()



__all__ = [name for name in globals() if not name.startswith("__")]
