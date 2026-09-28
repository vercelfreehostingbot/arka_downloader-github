"""Arka Downloader section: BACKGROUND LOOPS."""

from .s65_fallback import *

# ══════════════════════════════════════════════════════════════
# BACKGROUND LOOPS
# ══════════════════════════════════════════════════════════════
async def auto_delete_loop(c: Container):
    while not c.shutdown_event.is_set():
        try:
            await asyncio.wait_for(c.shutdown_event.wait(), timeout=30)
            return
        except asyncio.TimeoutError:
            pass
        try:
            now = now_ts()
            for j in JobRepo.due_for_delete(now):
                if j.file_path:
                    with contextlib.suppress(Exception):
                        p = Path(j.file_path)
                        parent = p.parent
                        if p.exists():
                            p.unlink()
                        cleanup_empty_dir(parent)
                with contextlib.suppress(Exception):
                    jd = DOWNLOAD_DIR / j.job_id
                    if jd.exists():
                        shutil.rmtree(jd, ignore_errors=True)
                if c.bot and j.msg_id:
                    with contextlib.suppress(Exception):
                        await c.bot.delete_message(j.chat_id, j.msg_id)
                if c.bot:
                    user = UserRepo.get(j.user_id)
                    lang = user_lang(user)
                    with contextlib.suppress(Exception):
                        kb = InlineKeyboardMarkup(inline_keyboard=[[
                            InlineKeyboardButton(
                                text=tr(lang, "btn_redo"),
                                callback_data=safe_cb(f"redl:{j.job_id}"))]])
                        await c.bot.send_message(
                            j.chat_id,
                            f"{tr(lang, 'file_removed')}\n"
                            f"🆔 <code>{j.job_id}</code>",
                            reply_markup=kb)
                JobRepo.update(j.job_id, notice_msg_id=1, file_path=None)
        except Exception as e:
            logging.error(f"auto_delete error: {e}")


async def announce_schedule_loop(c: Container):
    import json
    from types import SimpleNamespace
    while not c.shutdown_event.is_set():
        try:
            await asyncio.wait_for(c.shutdown_event.wait(), timeout=20)
            return
        except asyncio.TimeoutError:
            pass
        try:
            ts = float(db_get("announce_schedule_ts", "0") or 0)
            if ts <= 0 or now_ts() < ts:
                continue
            raw = db_get("announce_scheduled_payload", "")
            db_set("announce_schedule", "")
            db_set("announce_schedule_ts", "0")
            db_set("announce_scheduled_payload", "")
            if not raw:
                continue
            pl = json.loads(raw)
            uids = _audience_uids()
            if not uids:
                continue
            fake = SimpleNamespace(
                message=SimpleNamespace(
                    chat=SimpleNamespace(id=pl.get("chat_id"))),
                from_user=SimpleNamespace(id=pl.get("admin_id", 0)))
            await _do_user_broadcast(
                c, fake, uids, pl.get("text") or "",
                pl.get("media") or {}, pl.get("forward") or None)
        except Exception as e:
            logging.error(f"announce_schedule error: {e}")


async def auto_backup_loop(c: Container):
    last_check = 0
    while not c.shutdown_event.is_set():
        try:
            await asyncio.wait_for(c.shutdown_event.wait(), timeout=60)
            return
        except asyncio.TimeoutError:
            pass
        try:
            now = now_ts()
            if now - last_check < 60:
                continue
            last_check = now
            if db_get("auto_backup_enabled", "0") != "1":
                continue
            try:
                ih = float(db_get("auto_backup_hours", "24"))
            except ValueError:
                ih = 24.0
            try:
                lt = float(db_get("auto_backup_last", "0") or "0")
            except ValueError:
                lt = 0.0
            if now - lt < ih * 3600:
                continue
            name = f"auto_backup_{fmt_dt_short(now)}.db"
            dst = BACKUP_DIR / name
            checkpoint_db()
            shutil.copy2(DB_PATH, dst)
            size = dst.stat().st_size
            get_conn().execute(
                "INSERT INTO backups(path, size, created_at) VALUES (?, ?, ?)",
                (str(dst), size, now))
            db_set("auto_backup_last", str(now))
        except Exception as e:
            logging.error(f"auto_backup error: {e}")


async def recover_stuck_jobs(c: Container):
    try:
        for j in JobRepo.stuck_queued(now_ts() + 1):
            clear_cancelled(j.job_id)
            JobRepo.update(j.job_id, status=STATUS_QUEUED, error=None)
            await c.job_queue.put(j.job_id)
        for j in JobRepo.active(10000):
            if j.status in (STATUS_DOWNLOADING, STATUS_UPLOADING):
                clear_cancelled(j.job_id)
                JobRepo.update(j.job_id, status=STATUS_QUEUED,
                               error="interrupted_restart")
                await c.job_queue.put(j.job_id)
            elif j.status == STATUS_ANALYZING:
                JobRepo.update(j.job_id, status=STATUS_CANCELLED,
                               error="interrupted_restart",
                               finished_at=now_ts())
    except Exception as e:
        logging.error(f"recover error: {e}")



__all__ = [name for name in globals() if not name.startswith("__")]
