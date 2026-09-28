"""Arka Downloader section: HELPERS."""

from .s21_middlewares import *

# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════
async def safe_edit(target, text: str, markup=None):
    try:
        await target.edit_text(text, reply_markup=markup)
        return True
    except TelegramBadRequest as e:
        s = str(e).lower()
        if "not modified" in s:
            return True
        if "no text" in s or "caption" in s:
            with contextlib.suppress(Exception):
                await target.edit_caption(caption=text[:1024], reply_markup=markup)
                return True
        with contextlib.suppress(Exception):
            await target.answer(text, reply_markup=markup)
            return True
    except Exception:
        return False
    return False


async def send_text_safe(bot, chat_id, text, **kw):
    try:
        return await bot.send_message(chat_id, text, **kw)
    except TelegramBadRequest as e:
        low = str(e).lower()
        if "parse" in low or "entities" in low:
            return await bot.send_message(chat_id, text, parse_mode=None, **kw)
        raise


async def check_membership(uid: int) -> bool:
    if db_get("force_join", "0") != "1":
        return True
    if uid in OWNER_IDS:
        return True
    channel = db_get("channel_username", "").strip()
    if not channel:
        return True
    bot = CONTAINER.bot if CONTAINER else None
    if not bot:
        return True
    try:
        m = await bot.get_chat_member(channel, uid)
        return m.status not in ("left", "kicked")
    except Exception:
        return True


async def send_join_prompt(target, lang: str):
    channel = db_get("channel_username", "").strip()
    text = tr(lang, "please_join") + f"\n\n📢 <code>{esc(channel)}</code>"
    kb = join_kb(channel, lang)
    if isinstance(target, Message):
        await target.answer(text, reply_markup=kb)
    else:
        await safe_edit(target, text, kb)


async def send_home(target, user: User, edit: bool = True):
    lang = user_lang(user)
    text = tr_custom(lang, "welcome", name=esc(user.first_name or "User"))
    kb = main_menu(user)
    if isinstance(target, CallbackQuery):
        if edit:
            await safe_edit(target.message, text, kb)
        else:
            with contextlib.suppress(Exception):
                await target.message.answer(text, reply_markup=kb)
    elif isinstance(target, Message):
        await target.answer(text, reply_markup=kb)


async def send_start_media(chat_id: int, bot: Bot):
    if db_get("start_sticker_enabled", "1") == "1":
        sid = db_get("start_sticker_file_id", "").strip()
        if sid:
            try:
                await bot.send_sticker(chat_id=chat_id, sticker=sid)
                return
            except Exception:
                pass
    val = db_get("start_emoji_id", "").strip()
    if not val:
        return
    fb = db_get("start_emoji_fb", "✨") or "✨"
    with contextlib.suppress(Exception):
        if val.isdigit():
            await bot.send_message(
                chat_id=chat_id,
                text=f'<tg-emoji emoji-id="{val}">{fb}</tg-emoji>')
        else:
            await bot.send_message(chat_id=chat_id, text=val)


def _purge_job_files(rows):
    for r in rows:
        with contextlib.suppress(Exception):
            fp = r["file_path"]
            if fp:
                fpp = Path(fp)
                if fpp.exists():
                    fpp.unlink()
            jd = DOWNLOAD_DIR / str(r["job_id"])
            if jd.exists():
                shutil.rmtree(jd, ignore_errors=True)


def _effective_filesize(j: Job) -> int:
    if j.filesize and j.filesize > 0:
        return j.filesize
    if j.file_path:
        with contextlib.suppress(Exception):
            p = Path(j.file_path)
            if p.exists() and p.is_file():
                return p.stat().st_size
    return 0


def _effective_duration(j: Job) -> int:
    return j.duration if (j.duration and j.duration > 0) else 0


async def _send_photo_with_compression(
    bot: Bot, chat_id: int, image_path: Path,
    caption: str, job_id: str, lang: str,
) -> Optional[Message]:
    try:
        size = image_path.stat().st_size
    except Exception:
        return None
    if size <= PHOTO_TG_LIMIT:
        with contextlib.suppress(Exception):
            return await bot.send_photo(
                chat_id=chat_id, photo=FSInputFile(str(image_path)),
                caption=caption[:1024], request_timeout=1800)
    if db_get("compress_large_photos", "1") == "1" and HAS_PIL:
        with contextlib.suppress(Exception):
            compressed = await asyncio.to_thread(
                compress_image_for_tg, image_path, PHOTO_TG_LIMIT)
            if compressed and compressed.exists() and \
                    compressed.stat().st_size <= PHOTO_TG_LIMIT:
                with contextlib.suppress(Exception):
                    return await bot.send_photo(
                        chat_id=chat_id, photo=FSInputFile(str(compressed)),
                        caption=caption[:1024], request_timeout=1800)
    with contextlib.suppress(Exception):
        return await bot.send_document(
            chat_id=chat_id, document=FSInputFile(str(image_path)),
            caption=caption[:1024], request_timeout=1800)
    return None


async def _send_music_file(bot: Bot, chat_id: int, result: DownloadResult,
                            caption: str) -> Optional[Message]:
    as_audio = db_get("music_send_as_audio", "1") == "1"
    title = (result.title or "Audio")[:64]
    artist = (result.artist or "Unknown")[:64]
    duration = max(0, int(result.duration or 0))

    base_kwargs: dict = {
        "chat_id": chat_id,
        "caption": caption[:1024],
        "request_timeout": 1800,
    }

    if as_audio:
        kwargs = dict(base_kwargs)
        kwargs.update({
            "audio": FSInputFile(str(result.path)),
            "title": title,
            "performer": artist,
        })
        if duration > 0:
            kwargs["duration"] = duration
        if result.thumbnail_path and result.thumbnail_path.exists():
            try:
                kwargs["thumbnail"] = FSInputFile(str(result.thumbnail_path))
                return await bot.send_audio(**kwargs)
            except Exception:
                kwargs.pop("thumbnail", None)
        try:
            return await bot.send_audio(**kwargs)
        except Exception:
            pass

    try:
        return await bot.send_document(
            chat_id=chat_id,
            document=FSInputFile(str(result.path)),
            caption=caption[:1024],
            request_timeout=1800)
    except Exception:
        return None



__all__ = [name for name in globals() if not name.startswith("__")]
