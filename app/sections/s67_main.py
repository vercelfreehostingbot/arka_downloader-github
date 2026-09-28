"""Arka Downloader section: MAIN."""

from .s66_background_loops import *
from app.enterprise import runtime as ENTERPRISE_RUNTIME

# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════
async def main():
    print_banner()
    log_step("Loading", "settings...")
    cfg = load_settings()
    log_step("Database", "initializing...")
    run_migrations()
    log_step("Database", f"{cfg.db_path.name} ready")
    ffmpeg_ok = shutil.which("ffmpeg") is not None
    log_step("FFmpeg", "detected" if ffmpeg_ok else "missing", ok=ffmpeg_ok)
    log_step("Pillow", "detected" if HAS_PIL else "missing", ok=HAS_PIL)
    log_step("gallery-dl", "detected" if HAS_GALLERY_DL else "missing",
             ok=HAS_GALLERY_DL)
    cookies_path = DATA_DIR / "cookies.txt"
    log_step("Cookies", "found" if cookies_path.exists() else "not found",
             ok=cookies_path.exists())
    owner_ids = []
    for x in str(cfg.owner_ids or "").replace(",", " ").replace(";", " ").split():
        x = x.strip().lstrip("@")
        if x.isdigit() or (x.startswith("-") and x[1:].isdigit()):
            owner_ids.append(int(x))
    log_step("Owners", str(len(owner_ids)))
    MenuButtonRepo.seed_defaults()
    cleanup_menu_buttons()

    global CONTAINER
    CONTAINER = Container()
    await ENTERPRISE_RUNTIME.start()

    log_step("Bot", "connecting...")
    try:
        local_server = TelegramAPIServer.from_base(LOCAL_TG_API, is_local=True)
        session = AiohttpSession(api=local_server, timeout=1800, limit=100)
        with contextlib.suppress(Exception):
            session.middleware(PremiumEmojiRequestMiddleware())
        CONTAINER.bot = Bot(
            token=cfg.bot_token, session=session,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        me = await asyncio.wait_for(CONTAINER.bot.get_me(), timeout=30.0)
        log_step("Bot", f"@{me.username}")
        log_step("API", LOCAL_TG_API)
    except asyncio.TimeoutError:
        log_err("Bot connection timed out after 30s")
        sys.exit(1)
    except Exception as e:
        log_err(f"Bot connection failed: {e}")
        sys.exit(1)

    # ✅ فقط start و lang در منوی ربات نمایش داده میشن
    with contextlib.suppress(Exception):
        await CONTAINER.bot.set_my_commands([
            BotCommand(command="start", description="🏠 Start / شروع"),
            BotCommand(command="lang",  description="🌐 Language / زبان"),
        ])
        log_step("Commands", "registered (start, lang)")

    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(InjectMiddleware(CONTAINER))
    dp.callback_query.middleware(InjectMiddleware(CONTAINER))
    dp.message.middleware(UserUpsertMiddleware())
    dp.callback_query.middleware(UserUpsertMiddleware())
    dp.message.middleware(BlockGuardMiddleware())
    dp.callback_query.middleware(BlockGuardMiddleware())
    dp.message.middleware(MaintenanceGuard())
    dp.callback_query.middleware(MaintenanceGuard())
    dp.callback_query.middleware(CallbackRateLimitMiddleware(per_sec=0.6))
    dp.include_router(router)

    log_step("Jobs", "recovering...")
    await recover_stuck_jobs(CONTAINER)

    try:
        n_workers = max(1, int(os.getenv("BOT_WORKERS", "3")))
    except (ValueError, TypeError):
        n_workers = 3
    for i in range(n_workers):
        CONTAINER.worker_tasks.append(
            asyncio.create_task(worker(CONTAINER, i)))
    log_step("Workers", str(n_workers))

    CONTAINER.bg_tasks.append(
        asyncio.create_task(auto_delete_loop(CONTAINER)))
    CONTAINER.bg_tasks.append(
        asyncio.create_task(auto_backup_loop(CONTAINER)))
    CONTAINER.bg_tasks.append(
        asyncio.create_task(announce_schedule_loop(CONTAINER)))

    sys.stdout.write("\n")
    sys.stdout.write(
        f"  {C.GRN}{C.B}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.R}\n")
    sys.stdout.write(f"  {C.GRN}{C.B}✓ ONLINE{C.R}\n")
    sys.stdout.write(
        f"  {C.GRN}{C.B}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.R}\n\n")
    sys.stdout.flush()

    try:
        await CONTAINER.bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(CONTAINER.bot,
                                allowed_updates=["message", "callback_query"])
    except KeyboardInterrupt:
        sys.stdout.write(f"\n  {C.YEL}⚠ Stopped{C.R}\n")
    finally:
        CONTAINER.shutdown_event.set()
        for t in CONTAINER.worker_tasks + CONTAINER.bg_tasks:
            t.cancel()
        await asyncio.gather(
            *(CONTAINER.worker_tasks + CONTAINER.bg_tasks),
            return_exceptions=True)
        with contextlib.suppress(Exception):
            await CONTAINER.bot.session.close()
        await ENTERPRISE_RUNTIME.stop()
        close_conn()
        log_ok("Bot stopped cleanly")


def _run():
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        sys.stdout.write(f"\n  {C.YEL}⚠ Stopped{C.R}\n")
    except Exception as e:
        log_err(f"Fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    _run()
__all__ = [name for name in globals() if not name.startswith("__")]
