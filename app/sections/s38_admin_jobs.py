"""Arka Downloader section: ADMIN — JOBS."""

from .s37_admin_users import *

# ══════════════════════════════════════════════════════════════
# ADMIN — JOBS
# ══════════════════════════════════════════════════════════════
@router.callback_query(F.data == "admin:jobs")
async def cb_admin_jobs(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    await render_jobs(cb, c, "active", 1)


@router.callback_query(F.data.startswith("jobs:filter:"))
async def cb_jobs_filter(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    parts = cb.data.split(":")
    if len(parts) == 4:
        status = parts[2]
        try:
            page = int(parts[3])
        except ValueError:
            page = 1
    else:
        status, page = "active", 1
    await render_jobs(cb, c, status, page)


async def render_jobs(cb, c, status, page=1):
    lang = await _admin_lang(c, cb.from_user.id)
    per = 10
    page = max(1, page)
    total = JobRepo.count_for_filter(status)
    total_pages = max(1, (total + per - 1) // per)
    jobs = JobRepo.list_paginated(status, limit=per, offset=(page - 1) * per)
    labels = {"active": tr(lang, "ad_j_active"),
              "completed": tr(lang, "ad_j_completed"),
              "failed": tr(lang, "ad_j_failed"),
              "recent": tr(lang, "ad_j_recent")}
    label = labels.get(status, tr(lang, "ad_j_active"))
    b = InlineKeyboardBuilder()
    if not jobs:
        b.row(InlineKeyboardButton(text=tr(lang, "ad_j_empty"),
                                    callback_data="noop"))
    else:
        for j in jobs:
            icon = {"completed": "✅", "failed": "❌", "cancelled": "⚪",
                    "downloading": "⬇️", "uploading": "⬆️",
                    "queued": "⏳", "analyzing": "🔍"}.get(j.status, "⚙️")
            title = (j.title or j.job_id)[:26]
            size = _effective_filesize(j)
            dur = _effective_duration(j)
            b.row(InlineKeyboardButton(
                text=f"{icon} {title}\n💾 {fmt_bytes(size)} | ⏱ {fmt_duration(dur)}",
                callback_data=safe_cb(f"admin:job:{j.job_id}")))
    b.row(
        InlineKeyboardButton(text=tr(lang, "ad_j_active"),
                              callback_data="jobs:filter:active:1"),
        InlineKeyboardButton(text=tr(lang, "ad_j_completed"),
                              callback_data="jobs:filter:completed:1"))
    b.row(
        InlineKeyboardButton(text=tr(lang, "ad_j_failed"),
                              callback_data="jobs:filter:failed:1"),
        InlineKeyboardButton(text=tr(lang, "ad_j_recent"),
                              callback_data="jobs:filter:recent:1"))
    nav = InlineKeyboardBuilder()
    if page > 1:
        nav.button(text="◀️", callback_data=safe_cb(f"jobs:filter:{status}:{page-1}"))
    nav.button(text=f"📄 {page}/{total_pages}", callback_data="noop")
    if page < total_pages:
        nav.button(text="▶️", callback_data=safe_cb(f"jobs:filter:{status}:{page+1}"))
    nav.adjust(3)
    rows = b.export() + nav.export()
    rows.append([InlineKeyboardButton(text=tr(lang, "ad_back"),
                                        callback_data="admin:home")])
    text = tr(lang, "ad_j_title", status=label, count=total)
    await safe_edit(cb.message, text,
                    InlineKeyboardMarkup(inline_keyboard=rows))


@router.callback_query(F.data.startswith("admin:job:retry:"))
async def cb_job_retry(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    jid = cb.data.rsplit(":", 1)[1]
    if not JobRepo.get(jid):
        await cb.answer()
        return
    clear_cancelled(jid)
    JobRepo.update(jid, status=STATUS_QUEUED, error=None)
    await c.job_queue.put(jid)
    await cb.answer("✅", show_alert=True)


@router.callback_query(F.data.startswith("admin:job:cancel:"))
async def cb_job_cancel_admin(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    jid = cb.data.rsplit(":", 1)[1]
    mark_cancelled(jid)
    JobRepo.update(jid, status=STATUS_CANCELLED, finished_at=now_ts())
    await cb.answer("🚫", show_alert=True)


@router.callback_query(F.data.startswith("admin:job:delete:"))
async def cb_job_delete_file(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    jid = cb.data.rsplit(":", 1)[1]
    j = JobRepo.get(jid)
    if j and j.file_path:
        with contextlib.suppress(Exception):
            p = Path(j.file_path)
            parent = p.parent
            if p.exists():
                p.unlink()
            cleanup_empty_dir(parent)
        JobRepo.update(jid, file_path=None)
    await cb.answer("🗑", show_alert=True)


@router.callback_query(F.data.startswith("admin:job:"))
async def cb_job_detail(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    tail = cb.data[len("admin:job:"):]
    if tail.startswith(("retry:", "cancel:", "delete:")):
        return
    j = JobRepo.get(tail)
    if not j:
        await cb.answer("❌", show_alert=True)
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    qn = QUALITY_LABELS.get(lang, QUALITY_LABELS["fa"]).get(
        j.quality, j.quality)
    text = tr(lang, "ad_j_detail", id=j.job_id, uid=j.user_id,
              title=esc(j.title or "-"), quality=esc(qn),
              status=esc(j.status), size=fmt_bytes(_effective_filesize(j)),
              duration=fmt_duration(_effective_duration(j)),
              url=esc(j.url[:200]))
    b = InlineKeyboardBuilder()
    if j.status in (STATUS_QUEUED, STATUS_ANALYZING, STATUS_PENDING,
                    STATUS_DOWNLOADING):
        b.row(InlineKeyboardButton(
            text=tr(lang, "ad_j_cancel"),
            callback_data=safe_cb(f"admin:job:cancel:{j.job_id}")))
    else:
        b.row(InlineKeyboardButton(
            text=tr(lang, "ad_j_retry"),
            callback_data=safe_cb(f"admin:job:retry:{j.job_id}")))
        if j.file_path and Path(j.file_path).exists():
            b.row(InlineKeyboardButton(
                text=tr(lang, "ad_j_delete_file"),
                callback_data=safe_cb(f"admin:job:delete:{j.job_id}")))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_back"),
                                callback_data="admin:jobs"))
    await safe_edit(cb.message, text, b.as_markup())



__all__ = [name for name in globals() if not name.startswith("__")]
