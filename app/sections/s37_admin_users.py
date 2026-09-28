"""Arka Downloader section: ADMIN — USERS."""

from .s36_admin_dl_types import *

# ══════════════════════════════════════════════════════════════
# ADMIN — USERS
# ══════════════════════════════════════════════════════════════
@router.callback_query(F.data == "admin:users")
async def cb_admin_users(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text=tr(lang, "ad_u_search"),
                             callback_data="users:search"),
        InlineKeyboardButton(text=tr(lang, "ad_u_recent"),
                             callback_data="users:recent:1"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_u_vip"),
                                callback_data="users:vip:1"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_back"),
                                callback_data="admin:home"))
    await safe_edit(cb.message, tr(lang, "ad_u_title"), b.as_markup())


async def _render_users_list(cb, c, mode, page):
    lang = await _admin_lang(c, cb.from_user.id)
    per = 10
    page = max(1, page)
    if mode == "vip":
        total = UserRepo.count_vip()
        users = UserRepo.list_vip(limit=per, offset=(page - 1) * per)
        header = tr(lang, "ad_u_vip_title")
    else:
        total = UserRepo.count_all()
        users = UserRepo.list_recent(limit=per, offset=(page - 1) * per)
        header = tr(lang, "ad_u_recent_title")
    total_pages = max(1, (total + per - 1) // per)
    header += f"  — 📄 {page}/{total_pages}  ({total})"
    b = InlineKeyboardBuilder()
    for u in users:
        icon = "🚫" if u.is_blocked else ("💎" if u.is_vip else "👤")
        name = u.username or u.first_name or str(u.user_id)
        b.row(InlineKeyboardButton(
            text=f"{icon} {name[:35]}",
            callback_data=safe_cb(f"user:view:{u.user_id}")))
    nav = InlineKeyboardBuilder()
    if page > 1:
        nav.button(text="◀️", callback_data=safe_cb(f"users:{mode}:{page-1}"))
    nav.button(text=f"📄 {page}/{total_pages}", callback_data="noop")
    if page < total_pages:
        nav.button(text="▶️", callback_data=safe_cb(f"users:{mode}:{page+1}"))
    nav.adjust(3)
    rows = b.export() + nav.export()
    rows.append([InlineKeyboardButton(text=tr(lang, "ad_back"),
                                        callback_data="admin:users")])
    await safe_edit(cb.message, header,
                    InlineKeyboardMarkup(inline_keyboard=rows))


@router.callback_query(F.data.startswith("users:recent:"))
async def cb_users_recent(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    try:
        page = int(cb.data.rsplit(":", 1)[1])
    except ValueError:
        page = 1
    await _render_users_list(cb, c, "recent", page)


@router.callback_query(F.data.startswith("users:vip:"))
async def cb_users_vip(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    try:
        page = int(cb.data.rsplit(":", 1)[1])
    except ValueError:
        page = 1
    await _render_users_list(cb, c, "vip", page)


@router.callback_query(F.data == "users:search")
async def cb_users_search(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    await state.set_state(Flow.a_users_search)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "ad_back"),
                             callback_data="admin:users")]])
    await safe_edit(cb.message, tr(lang, "ad_u_search_ask"), kb)


@router.message(Flow.a_users_search, F.text)
async def msg_users_search(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    lang = await _admin_lang(c, message.from_user.id)
    q = (message.text or "").strip()
    clean = q.lstrip("@")
    rows = get_conn().execute(
        """SELECT * FROM users WHERE
           CAST(user_id AS TEXT)=? OR username LIKE ? OR first_name LIKE ?
           LIMIT 20""", (q, f"%{clean}%", f"%{q}%")).fetchall()
    await state.clear()
    if not rows:
        await message.answer(tr(lang, "ad_u_not_found"))
        return
    b = InlineKeyboardBuilder()
    for r in rows:
        u = User.from_row(r)
        name = u.username or u.first_name or str(u.user_id)
        b.row(InlineKeyboardButton(
            text=f"{name[:35]}",
            callback_data=safe_cb(f"user:view:{u.user_id}")))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_back"),
                                callback_data="admin:users"))
    header = tr(lang, "ad_u_search_title") + f"  ({len(rows)})"
    await message.answer(header, reply_markup=b.as_markup())


@router.callback_query(F.data.startswith("user:view:"))
async def cb_user_view(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    try:
        uid = int(cb.data.rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await cb.answer()
        return
    u = UserRepo.get(uid)
    if not u:
        await cb.answer("❌", show_alert=True)
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    status = (tr(lang, "status_blocked") if u.is_blocked
              else tr(lang, "status_active"))
    tier = tr(lang, "tier_vip") if u.is_vip else tr(lang, "tier_normal")
    text = tr(lang, "ad_u_profile", uid=u.user_id,
              name=esc(u.first_name or "-"),
              username=esc("@" + u.username) if u.username else "-",
              total=u.downloads, success=u.success_dl, failed=u.failed_dl,
              status=status, tier=tier)
    block_btn = (tr(lang, "ad_u_unblock") if u.is_blocked
                 else tr(lang, "ad_u_block"))
    block_cb = f"user:unblock:{uid}" if u.is_blocked else f"user:block:{uid}"
    vip_btn = (tr(lang, "ad_u_vip_off") if u.is_vip
               else tr(lang, "ad_u_vip_on"))
    vip_cb = f"user:unvip:{uid}" if u.is_vip else f"user:setvip:{uid}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=block_btn,
                              callback_data=safe_cb(block_cb)),
         InlineKeyboardButton(text=vip_btn,
                              callback_data=safe_cb(vip_cb))],
        [InlineKeyboardButton(text=tr(lang, "ad_back"),
                              callback_data="admin:users")]])
    await safe_edit(cb.message, text, kb)


@router.callback_query(F.data.startswith("user:block:"))
async def cb_user_block(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    uid = int(cb.data.rsplit(":", 1)[1])
    UserRepo.set_blocked(uid, True)
    db_log(cb.from_user.id, "user_block", str(uid))
    await cb.answer("🚫", show_alert=True)
    await cb_user_view(cb, c)


@router.callback_query(F.data.startswith("user:unblock:"))
async def cb_user_unblock(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    uid = int(cb.data.rsplit(":", 1)[1])
    UserRepo.set_blocked(uid, False)
    db_log(cb.from_user.id, "user_unblock", str(uid))
    await cb.answer("✅", show_alert=True)
    await cb_user_view(cb, c)


@router.callback_query(F.data.startswith("user:setvip:"))
async def cb_user_setvip(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    uid = int(cb.data.rsplit(":", 1)[1])
    UserRepo.set_vip(uid, True)
    db_log(cb.from_user.id, "user_vip", str(uid))
    await cb.answer("💎", show_alert=True)
    await cb_user_view(cb, c)


@router.callback_query(F.data.startswith("user:unvip:"))
async def cb_user_unvip(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    uid = int(cb.data.rsplit(":", 1)[1])
    UserRepo.set_vip(uid, False)
    db_log(cb.from_user.id, "user_unvip", str(uid))
    await cb.answer("💔", show_alert=True)
    await cb_user_view(cb, c)



__all__ = [name for name in globals() if not name.startswith("__")]
