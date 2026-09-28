"""Arka Downloader section: ADMIN — UPDATE."""

from .s46_admin_tools import *

# ══════════════════════════════════════════════════════════════
# ADMIN — UPDATE
# ══════════════════════════════════════════════════════════════
@router.callback_query(F.data == "admin:update")
async def cb_admin_update(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    await state.clear()
    lang = await _admin_lang(c, cb.from_user.id)
    version = db_get("bot_version", FILE_VERSION)
    writable = "✅" if os.access(BASE_DIR, os.W_OK) else "❌"
    text = tr(lang, "ad_up_title", version=esc(version),
              run_file=esc(Path(__file__).name), writable=writable)
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text=tr(lang, "ad_up_apply"),
                              callback_data="up:apply"),
        InlineKeyboardButton(text=tr(lang, "ad_up_fetch"),
                              callback_data="up:fetch"))
    b.row(
        InlineKeyboardButton(text=tr(lang, "ad_up_history"),
                              callback_data="up:history"),
        InlineKeyboardButton(text=tr(lang, "ad_up_rollback"),
                              callback_data="up:rollback"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_back"),
                                callback_data="admin:home"))
    await safe_edit(cb.message, text, b.as_markup())


@router.callback_query(F.data == "up:apply")
async def cb_up_apply(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    await state.set_state(Flow.a_up_zip)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "ad_back"),
                             callback_data="admin:update")]])
    await safe_edit(cb.message, tr(lang, "ad_up_ask_zip"), kb)


@router.message(Flow.a_up_zip, F.document)
async def msg_up_zip(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id) or not c.bot:
        return
    doc = message.document
    lang = await _admin_lang(c, message.from_user.id)
    if not doc or not doc.file_name:
        return
    fname = doc.file_name.lower()
    if not (fname.endswith(".zip") or fname.endswith(".py")):
        await message.answer(tr(lang, "ad_up_invalid_file"))
        return
    try:
        ts = fmt_dt_short(now_ts())
        current_file = Path(__file__).resolve()
        backup_code = BACKUP_DIR / f"pre_update_{ts}_DownVip.py"
        shutil.copy2(current_file, backup_code)
        new_version = "unknown"
        prev = db_get("bot_version", FILE_VERSION)
        if fname.endswith(".py"):
            tmp = UPDATE_DIR / f"update_{ts}.py"
            await download_tg_file(c.bot, doc.file_id, tmp)
            content = tmp.read_text(encoding="utf-8", errors="ignore")
            compile(content, "update.py", "exec")
            shutil.copy2(tmp, current_file)
            with contextlib.suppress(Exception):
                tmp.unlink()
            m = re.search(r'Version\s+([\d]+\.[\d]+(?:\.[\d]+)?)', content)
            new_version = m.group(1) if m else f"unknown_{ts}"
        else:
            dst = UPDATE_DIR / f"update_{ts}.zip"
            await download_tg_file(c.bot, doc.file_id, dst)
            extract_dir = UPDATE_DIR / f"extract_{ts}"
            extract_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(dst, "r") as zf:
                base = extract_dir.resolve()
                for zi in zf.infolist():
                    tgt = (extract_dir / zi.filename).resolve()
                    if tgt != base and base not in tgt.parents:
                        raise ValueError("unsafe path in zip")
                zf.extractall(extract_dir)
            candidates = list(extract_dir.rglob("bot.py"))
            if not candidates:
                await state.clear()
                await message.answer(tr(lang, "ad_up_no_botpy"))
                return
            new_file = candidates[0]
            content = new_file.read_text(encoding="utf-8", errors="ignore")
            compile(content, "bot.py", "exec")
            shutil.copy2(new_file, current_file)
            with contextlib.suppress(Exception):
                shutil.rmtree(extract_dir, ignore_errors=True)
                dst.unlink()
            m = re.search(r'Version\s+([\d]+\.[\d]+(?:\.[\d]+)?)', content)
            new_version = m.group(1) if m else f"unknown_{ts}"
        with contextlib.suppress(Exception):
            get_conn().execute(
                "INSERT INTO update_history(version, prev_version, applied, "
                "backup_path, note, created_at) VALUES (?, ?, 1, ?, ?, ?)",
                (new_version, prev, str(backup_code), fname, now_ts()))
        db_set("bot_version", new_version)
        db_set("prev_version", prev)
        await state.clear()
        await message.answer(
            f"✅ {new_version}\n{tr(lang, 'ad_up_restart_msg')}")
        await asyncio.sleep(3)
        _restart_process(current_file)
    except Exception as e:
        await state.clear()
        await message.answer(f"❌ {esc(str(e))}")


@router.callback_query(F.data == "up:fetch")
async def cb_up_fetch(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    try:
        name = f"source_{fmt_dt_short(now_ts())}.zip"
        dst = UPDATE_DIR / name
        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in BASE_DIR.glob("*.py"):
                zf.write(f, f.name)
        await c.bot.send_document(chat_id=cb.from_user.id,
                                    document=FSInputFile(str(dst)),
                                    caption=name)
    except Exception as e:
        with contextlib.suppress(Exception):
            await cb.message.answer(f"❌ {esc(str(e))}")


@router.callback_query(F.data == "up:history")
async def cb_up_history(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    rows = get_conn().execute(
        "SELECT * FROM update_history ORDER BY created_at DESC LIMIT 15"
    ).fetchall()
    text = tr(lang, "ad_up_history_title") + "\n\n"
    if not rows:
        text += tr(lang, "ad_up_history_empty")
    else:
        for r in rows:
            text += f"<code>{esc(r['version'])}</code> {fmt_time(r['created_at'])}\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "ad_back"),
                             callback_data="admin:update")]])
    await safe_edit(cb.message, text, kb)


@router.callback_query(F.data == "up:rollback")
async def cb_up_rollback(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    backups = sorted(BACKUP_DIR.glob("pre_update_*_DownVip.py"),
                     key=lambda p: p.stat().st_mtime, reverse=True)
    if not backups:
        await cb.answer("⚠️", show_alert=True)
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅", callback_data="up:rollback_yes")],
        [InlineKeyboardButton(text="❌", callback_data="admin:update")]])
    await safe_edit(
        cb.message,
        f"{tr(lang, 'rollback_title')}\n"
        f"<code>{esc(backups[0].name)}</code>\n\n"
        f"{tr(lang, 'rollback_confirm_text')}",
        kb)


@router.callback_query(F.data == "up:rollback_yes")
async def cb_up_rollback_yes(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    backups = sorted(BACKUP_DIR.glob("pre_update_*_DownVip.py"),
                     key=lambda p: p.stat().st_mtime, reverse=True)
    if not backups:
        await cb.answer("⚠️", show_alert=True)
        return
    await cb.answer("♻️")
    try:
        src = backups[0]
        content = src.read_text(encoding="utf-8", errors="ignore")
        compile(content, src.name, "exec")
        current_file = Path(__file__).resolve()
        shutil.copy2(current_file, BACKUP_DIR /
                     f"pre_rollback_{fmt_dt_short(now_ts())}_DownVip.py")
        shutil.copy2(src, current_file)
        m = re.search(r'Version\s+([\d]+\.[\d]+(?:\.[\d]+)?)', content)
        ver = m.group(1) if m else "unknown"
        prev = db_get("bot_version", FILE_VERSION)
        with contextlib.suppress(Exception):
            get_conn().execute(
                "INSERT INTO update_history(version, prev_version, applied, "
                "backup_path, note, created_at) VALUES (?, ?, 0, ?, ?, ?)",
                (ver, prev, str(src), "rollback", now_ts()))
        db_set("bot_version", ver)
        db_set("prev_version", prev)
        lang = await _admin_lang(c, cb.from_user.id)
        await cb.message.answer(
            f"↩️ {esc(ver)}\n{tr(lang, 'rollback_restarting')}")
        await asyncio.sleep(3)
        _restart_process(current_file)
    except Exception as e:
        with contextlib.suppress(Exception):
            await cb.message.answer(f"❌ {esc(str(e))}")



__all__ = [name for name in globals() if not name.startswith("__")]
