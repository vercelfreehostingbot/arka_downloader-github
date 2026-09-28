"""Arka Downloader section: SUB-ADMINS."""

from .s60_guide import *

# ══════════════════════════════════════════════════════════════
# SUB-ADMINS
# ══════════════════════════════════════════════════════════════
@router.callback_query(F.data == "admin:admins")
async def cb_admin_admins(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    await render_admins(cb, c, 1)


async def render_admins(cb, c, page=1):
    lang = await _admin_lang(c, cb.from_user.id)
    per = 10
    page = max(1, page)
    total = int(get_conn().execute(
        "SELECT COUNT(*) AS c FROM extra_admins").fetchone()["c"] or 0)
    total_pages = max(1, (total + per - 1) // per)
    rows = get_conn().execute(
        "SELECT * FROM extra_admins ORDER BY added_at DESC LIMIT ? OFFSET ?",
        (per, (page - 1) * per)).fetchall()

    text = tr(lang, "ad_admins_title", count=total)
    text += f"\n📄 {page}/{total_pages}\n\n"

    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=tr(lang, "ad_admins_add"),
                                callback_data="adm:add"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_admins_search"),
                                callback_data="adm:search"))
    if not rows:
        text += tr(lang, "ad_admins_empty")
    else:
        for r in rows:
            uid = int(r["user_id"])
            u = UserRepo.get(uid)
            name = (u.username or u.first_name) if u else str(uid)
            b.row(InlineKeyboardButton(
                text=f"👑 {name[:35]}",
                callback_data=safe_cb(f"adm:view:{uid}")))
            text += f"👑 <code>{uid}</code> — {esc(str(name)[:30])}\n"
    nav = InlineKeyboardBuilder()
    if page > 1:
        nav.button(text="◀️", callback_data=safe_cb(f"adm:pg:{page - 1}"))
    nav.button(text=f"📄 {page}/{total_pages}", callback_data="noop")
    if page < total_pages:
        nav.button(text="▶️", callback_data=safe_cb(f"adm:pg:{page + 1}"))
    nav.adjust(3)
    rows_kb = b.export() + nav.export()
    rows_kb.append([InlineKeyboardButton(text=tr(lang, "ad_admins_back"),
                                           callback_data="admin:home")])
    await safe_edit(cb.message, text,
                    InlineKeyboardMarkup(inline_keyboard=rows_kb))


@router.callback_query(F.data.startswith("adm:pg:"))
async def cb_adm_pg(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    try:
        page = int(cb.data.rsplit(":", 1)[1])
    except ValueError:
        page = 1
    await render_admins(cb, c, page)


@router.callback_query(F.data == "adm:add")
async def cb_adm_add(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    await state.set_state(Flow.admin_new_id)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "ad_admins_back"),
                             callback_data="admin:admins")]])
    await safe_edit(cb.message, tr(lang, "ad_admins_ask"), kb)


@router.message(Flow.admin_new_id, F.text)
async def msg_adm_add(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    lang = await _admin_lang(c, message.from_user.id)
    val = (message.text or "").strip()
    if not val.lstrip("-").isdigit():
        await message.answer(tr(lang, "ad_admins_invalid"))
        return
    uid = int(val)
    if uid == message.from_user.id:
        await message.answer(tr(lang, "ad_admins_self"))
        await state.clear()
        return
    if uid in OWNER_IDS:
        await message.answer(tr(lang, "ad_admins_exists_owner"))
        await state.clear()
        return
    existing = get_conn().execute(
        "SELECT 1 FROM extra_admins WHERE user_id=?", (uid,)).fetchone()
    if existing:
        await message.answer(tr(lang, "ad_admins_exists_admin"))
        await state.clear()
        return
    get_conn().execute(
        "INSERT INTO extra_admins(user_id, added_by, added_at) VALUES (?, ?, ?)",
        (uid, message.from_user.id, now_ts()))
    await state.clear()
    await message.answer(tr(lang, "ad_admins_added"))
    with contextlib.suppress(Exception):
        await c.bot.send_message(uid, "👑")


@router.callback_query(F.data == "adm:search")
async def cb_adm_search(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    await state.set_state(Flow.admin_search)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "ad_admins_back"),
                             callback_data="admin:admins")]])
    await safe_edit(cb.message, tr(lang, "ad_admins_search_ask"), kb)


@router.message(Flow.admin_search, F.text)
async def msg_adm_search(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    lang = await _admin_lang(c, message.from_user.id)
    val = (message.text or "").strip()
    if not val.lstrip("-").isdigit():
        await message.answer(tr(lang, "ad_admins_invalid"))
        return
    uid = int(val)
    row = get_conn().execute(
        "SELECT * FROM extra_admins WHERE user_id=?", (uid,)).fetchone()
    await state.clear()
    if not row:
        await message.answer(tr(lang, "ad_admins_not_found"))
        return
    u = UserRepo.get(uid)
    name = (u.first_name if u and u.first_name else "—")
    username = ("@" + u.username) if (u and u.username) else "—"
    text = f"👑 <code>{uid}</code>\n📛 {esc(name)}\n🔗 {esc(username)}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=tr(lang, "ad_admins_remove_btn"),
                              callback_data=safe_cb(f"adm:rm:{uid}"))],
        [InlineKeyboardButton(text=tr(lang, "ad_admins_back"),
                              callback_data="admin:admins")]])
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("adm:view:"))
async def cb_adm_view(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    lang = await _admin_lang(c, cb.from_user.id)
    try:
        uid = int(cb.data.rsplit(":", 1)[1])
    except ValueError:
        await cb.answer()
        return
    row = get_conn().execute(
        "SELECT * FROM extra_admins WHERE user_id=?", (uid,)).fetchone()
    if not row:
        await cb.answer(tr(lang, "ad_admins_not_found"), show_alert=True)
        return
    await cb.answer()
    u = UserRepo.get(uid)
    name = (u.first_name if u and u.first_name else "—")
    username = ("@" + u.username) if (u and u.username) else "—"
    status = tr(lang, "active")
    text = tr(lang, "ad_admins_profile", uid=uid, name=esc(name),
              username=esc(username),
              date=fmt_time(row["added_at"]), status=status)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=tr(lang, "ad_admins_remove_btn"),
                              callback_data=safe_cb(f"adm:rm:{uid}"))],
        [InlineKeyboardButton(text=tr(lang, "ad_admins_back"),
                              callback_data="admin:admins")]])
    await safe_edit(cb.message, text, kb)


@router.callback_query(F.data.startswith("adm:rm:"))
async def cb_adm_remove(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    try:
        uid = int(cb.data.rsplit(":", 1)[1])
    except ValueError:
        await cb.answer()
        return
    get_conn().execute("DELETE FROM extra_admins WHERE user_id=?", (uid,))
    await cb.answer("🗑", show_alert=True)
    await render_admins(cb, c, 1)



__all__ = [name for name in globals() if not name.startswith("__")]
