"""Arka Downloader section: EMOJI MAP."""

from .s53_admin_style import *

# ══════════════════════════════════════════════════════════════
# EMOJI MAP
# ══════════════════════════════════════════════════════════════
@router.callback_query(F.data == "style:emoji_map")
async def cb_style_emoji_map(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    await render_emoji_map(cb, c)


async def render_emoji_map(cb: CallbackQuery, c: Container):
    lang = await _admin_lang(c, cb.from_user.id)
    count = emoji_map_count()
    enabled = db_get("premium_emoji_enabled", "1") == "1"
    status = tr(lang, "active") if enabled else tr(lang, "disabled")
    text = tr(lang, "em_title", count=count, status=status)
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=tr(lang, "em_add"),
                                callback_data="em:add"))
    b.row(InlineKeyboardButton(text=tr(lang, "em_list"),
                                callback_data="em:list"))
    b.row(InlineKeyboardButton(text=tr(lang, "em_clear"),
                                callback_data="em:clear"))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_back"),
                                callback_data="admin:style"))
    await safe_edit(cb.message, text, b.as_markup())


@router.callback_query(F.data == "em:add")
async def cb_em_add(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    await state.set_state(Flow.emoji_add_premium)
    await state.update_data(premium_list=[])
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "cancel"),
                             callback_data="style:emoji_map")]])
    await safe_edit(cb.message, tr(lang, "em_step1"), kb)


@router.message(Flow.emoji_add_premium)
async def msg_em_premium(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    lang = await _admin_lang(c, message.from_user.id)
    prems = extract_premium_emojis(message)
    if not prems:
        await message.answer(tr(lang, "em_need_premium"))
        return
    await state.update_data(premium_list=prems)
    await state.set_state(Flow.emoji_add_normal)
    preview = "\n".join(
        f"{i+1}. <tg-emoji emoji-id=\"{eid}\">{fb}</tg-emoji>"
        for i, (eid, fb) in enumerate(prems[:20]))
    await message.answer(
        f"✅ {len(prems)}\n\n{preview}\n\n"
        f"{tr(lang, 'normal_emojis_prompt')}")


@router.message(Flow.emoji_add_normal, F.text)
async def msg_em_normal(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    prems = data.get("premium_list") or []
    if not prems:
        await state.clear()
        return
    norms = extract_normal_emojis(message.text or "")
    if not norms:
        await message.answer("⚠️")
        return
    count = min(len(prems), len(norms))
    for i in range(count):
        eid, fb = prems[i]
        get_conn().execute(
            """INSERT INTO emoji_map(normal_emoji, premium_id,
               fallback_emoji, created_at) VALUES (?, ?, ?, ?)
               ON CONFLICT(normal_emoji) DO UPDATE SET
                 premium_id=excluded.premium_id,
                 fallback_emoji=excluded.fallback_emoji,
                 created_at=excluded.created_at""",
            (norms[i], eid, fb, now_ts()))
    invalidate_emoji_cache()
    await state.clear()
    await message.answer(f"✅ {count}")


@router.callback_query(F.data == "em:list")
async def cb_em_list(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    rows = get_conn().execute(
        "SELECT * FROM emoji_map ORDER BY created_at DESC LIMIT 30").fetchall()
    text = "📋\n\n"
    for r in rows:
        text += (f"{r['normal_emoji']} → "
                 f"<tg-emoji emoji-id=\"{r['premium_id']}\">"
                 f"{r['fallback_emoji']}</tg-emoji>\n")
    if not rows:
        text += "📭"
    b = InlineKeyboardBuilder()
    for r in rows[:15]:
        b.row(InlineKeyboardButton(
            text=f"🗑 {r['normal_emoji']}",
            callback_data=safe_cb(f"em:del:{r['normal_emoji']}")))
    b.row(InlineKeyboardButton(text="◀️", callback_data="style:emoji_map"))
    await safe_edit(cb.message, text, b.as_markup())


@router.callback_query(F.data.startswith("em:del:"))
async def cb_em_del(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    normal = cb.data[len("em:del:"):]
    get_conn().execute("DELETE FROM emoji_map WHERE normal_emoji=?", (normal,))
    invalidate_emoji_cache()
    await cb.answer("🗑", show_alert=True)
    await cb_em_list(cb, c)


@router.callback_query(F.data == "em:clear")
async def cb_em_clear(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    count = emoji_map_count()
    if count == 0:
        await cb.answer("📭", show_alert=True)
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅", callback_data="em:clear:yes")],
        [InlineKeyboardButton(text="❌", callback_data="style:emoji_map")]])
    await safe_edit(cb.message, f"⚠️ {count}", kb)
    await cb.answer()


@router.callback_query(F.data == "em:clear:yes")
async def cb_em_clear_yes(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    count = emoji_map_count()
    get_conn().execute("DELETE FROM emoji_map")
    invalidate_emoji_cache()
    await cb.answer(f"🧹 {count}", show_alert=True)
    await cb_style_emoji_map(cb, c)



__all__ = [name for name in globals() if not name.startswith("__")]
