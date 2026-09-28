"""Arka Downloader section: FAVORITES."""

from .s29_re_download import *

# ══════════════════════════════════════════════════════════════
# FAVORITES
# ══════════════════════════════════════════════════════════════
@router.callback_query(F.data == "menu:favs")
async def cb_favs(cb: CallbackQuery, c: Container):
    await cb.answer()
    await show_favs(cb, 1)


@router.callback_query(F.data.startswith("favpg:"))
async def cb_favs_page(cb: CallbackQuery, c: Container):
    await cb.answer()
    try:
        page = int(cb.data.split(":", 1)[1])
    except ValueError:
        page = 1
    await show_favs(cb, page)


async def show_favs(cb: CallbackQuery, page: int = 1):
    user = UserRepo.get(cb.from_user.id)
    if not user:
        return
    lang = user_lang(user)
    per = 10
    page = max(1, page)
    total = FavRepo.count(user.user_id)
    total_pages = max(1, (total + per - 1) // per)
    jobs = FavRepo.list(user.user_id, limit=per, offset=(page - 1) * per)
    if not jobs:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=tr(lang, "back"),
                                 callback_data="menu:home")]])
        await safe_edit(cb.message, tr(lang, "fav_empty_new"), kb)
        return
    text = tr(lang, "fav_page_title", count=total) + \
           f"  — 📄 {page}/{total_pages}\n\n"
    buttons = []
    for j in jobs:
        icon = {"completed": "✅", "failed": "❌", "cancelled": "⚪",
                "downloading": "⬇️", "uploading": "⬆️",
                "queued": "⏳", "analyzing": "🔍"}.get(j.status, "⚙️")
        title = (j.title or j.job_id)[:22]
        size_str = fmt_bytes(_effective_filesize(j))
        dur = _effective_duration(j)
        dur_str = fmt_duration(dur) if dur else "—"
        text += f"⭐ {icon} <b>{title}</b>  💾 {size_str}  ⏱ {dur_str}\n"
        buttons.append([InlineKeyboardButton(
            text=f"⭐ {icon} {title[:18]}\n💾 {size_str} | ⏱ {dur_str}",
            callback_data=safe_cb(f"favview:{j.job_id}"))])
    nav = InlineKeyboardBuilder()
    if page > 1:
        nav.button(text="◀️", callback_data=safe_cb(f"favpg:{page - 1}"))
    nav.button(text=f"📄 {page} / {total_pages}", callback_data="noop")
    if page < total_pages:
        nav.button(text="▶️", callback_data=safe_cb(f"favpg:{page + 1}"))
    nav.adjust(3)
    kb_rows = buttons + nav.export()
    kb_rows.append([InlineKeyboardButton(text=tr(lang, "back"),
                                          callback_data="menu:home")])
    await safe_edit(cb.message, text,
                    InlineKeyboardMarkup(inline_keyboard=kb_rows))


@router.callback_query(F.data.startswith("favview:"))
async def cb_fav_view(cb: CallbackQuery, c: Container):
    with contextlib.suppress(Exception):
        await cb.answer()
    user = UserRepo.get(cb.from_user.id)
    if not user:
        return
    lang = user_lang(user)
    jid = cb.data.split(":", 1)[1]
    j = JobRepo.get(jid)
    if not j or not FavRepo.is_fav(user.user_id, jid):
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
    text = tr(lang, "hist_item_detail",
              title=esc((j.title or "-")[:80]), id=j.job_id,
              quality=esc(qn), status=f"{icon} {esc(j.status)}",
              size=fmt_bytes(size), duration=fmt_duration(duration),
              date=fmt_time(j.started_at or j.created_at or now_ts()))
    buttons = []
    if j.file_path and Path(j.file_path).exists():
        buttons.append([InlineKeyboardButton(
            text=tr(lang, "resend"),
            callback_data=safe_cb(f"sendfile:{jid}"))])
    buttons.append([InlineKeyboardButton(
        text=tr(lang, "fav_remove_btn"),
        callback_data=safe_cb(f"favrm:{jid}"))])
    buttons.append([InlineKeyboardButton(
        text=tr(lang, "btn_redo"),
        callback_data=safe_cb(f"redl:{jid}"))])
    buttons.append([InlineKeyboardButton(
        text=tr(lang, "back_to_favs"),
        callback_data="menu:favs")])
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


@router.callback_query(F.data.startswith("favrm:"))
async def cb_fav_remove(cb: CallbackQuery, c: Container):
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
    await show_favs(cb, 1)



__all__ = [name for name in globals() if not name.startswith("__")]
