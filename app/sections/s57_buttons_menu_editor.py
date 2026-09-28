"""Arka Downloader section: BUTTONS — MENU EDITOR."""

from .s56_buttons_hub import *

# ══════════════════════════════════════════════════════════════
# BUTTONS — MENU EDITOR
# ══════════════════════════════════════════════════════════════
@router.callback_query(F.data.startswith("style:menu:"))
async def cb_style_menu(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    scope = cb.data.rsplit(":", 1)[1]
    if scope not in ("user", "admin"):
        return
    await render_menu_editor(cb, c, scope)


async def render_menu_editor(cb: CallbackQuery, c: Container, scope: str):
    lang = await _admin_lang(c, cb.from_user.id)
    rows = MenuButtonRepo.by_scope(scope, visible_only=False)
    try:
        cols = int(db_get(f"menu_cols_{scope}", "2"))
    except ValueError:
        cols = 2
    if cols not in (1, 2, 3, 4):
        cols = 2

    group_label = (tr(lang, "menu_user") if scope == "user"
                   else tr(lang, "menu_admin"))
    text = (
        f"🎛 <b>{tr(lang, 'mn_edit_label')}</b>\n"
        f"📂 {group_label}\n"
        f"🔢 {len(rows)}  |  📊 {cols}\n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )

    b = InlineKeyboardBuilder()
    for r in rows:
        vis = "✅" if r["is_visible"] else "🚫"
        ci = {"default": "⚪", "success": "🟢",
              "danger": "🔴", "primary": "🔵"}.get(r["color"] or "default", "⚪")
        ei = "💎" if r["emoji_id"] else ""
        if r["label"]:
            label = r["label"]
        else:
            key = r["btn_key"]
            lk = (MenuButtonRepo.DEFAULTS_USER if scope == "user"
                  else MenuButtonRepo.DEFAULTS_ADMIN).get(key, ("back", ""))[0]
            label = tr(lang, lk)
        b.row(InlineKeyboardButton(
            text=f"{vis}{ci}{ei} {label[:40]}",
            callback_data=safe_cb(f"mn:edit:{scope}:{r['btn_key']}")))

    col_row = []
    for n in (1, 2, 3, 4):
        mark = " ✅" if cols == n else ""
        col_row.append(InlineKeyboardButton(
            text=f"{n}{mark}",
            callback_data=safe_cb(f"mn:setcols:{scope}:{n}")))
    b.row(*col_row)

    b.row(
        InlineKeyboardButton(text=tr(lang, "mn_show_all"),
                              callback_data=safe_cb(f"mn:allvis:{scope}")),
        InlineKeyboardButton(text=tr(lang, "mn_hide_all"),
                              callback_data=safe_cb(f"mn:allhide:{scope}")))
    b.row(InlineKeyboardButton(text=tr(lang, "mn_reset_all"),
                                callback_data=safe_cb(f"mn:resetall:{scope}")))
    b.row(InlineKeyboardButton(text=tr(lang, "ad_back"),
                                callback_data="admin:buttons"))
    await safe_edit(cb.message, text, b.as_markup())


@router.callback_query(F.data.startswith("mn:setcols:"))
async def cb_mn_setcols(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    parts = cb.data.split(":")
    if len(parts) != 4:
        await cb.answer()
        return
    _, _, scope, n = parts
    if scope not in ("user", "admin") or n not in ("1", "2", "3", "4"):
        await cb.answer()
        return
    db_set(f"menu_cols_{scope}", n)
    await cb.answer("✅")
    await render_menu_editor(cb, c, scope)


@router.callback_query(F.data.startswith("mn:allvis:"))
async def cb_mn_allvis(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    scope = cb.data.rsplit(":", 1)[1]
    get_conn().execute("UPDATE menu_buttons SET is_visible=1 WHERE scope=?",
                        (scope,))
    await cb.answer("✅")
    await render_menu_editor(cb, c, scope)


@router.callback_query(F.data.startswith("mn:allhide:"))
async def cb_mn_allhide(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    scope = cb.data.rsplit(":", 1)[1]
    get_conn().execute("UPDATE menu_buttons SET is_visible=0 WHERE scope=?",
                        (scope,))
    await cb.answer("✅")
    await render_menu_editor(cb, c, scope)


@router.callback_query(F.data.startswith("mn:resetall:"))
async def cb_mn_resetall(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    scope = cb.data.rsplit(":", 1)[1]
    get_conn().execute(
        """UPDATE menu_buttons SET label=NULL, color='default',
           emoji_id=NULL, emoji_fb=NULL, is_visible=1
           WHERE scope=?""", (scope,))
    await cb.answer("✅")
    await render_menu_editor(cb, c, scope)


@router.callback_query(F.data.startswith("mn:edit:"))
async def cb_menu_edit(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    parts = cb.data.split(":")
    if len(parts) != 4:
        return
    _, _, scope, key = parts
    await state.update_data(scope=scope, key=key)
    await render_edit_panel(cb, c, scope, key)


async def render_edit_panel(cb, c, scope, key):
    lang = await _admin_lang(c, cb.from_user.id)
    row = MenuButtonRepo.get(scope, key)
    if not row:
        return
    if row["label"]:
        label = row["label"]
    else:
        lk = (MenuButtonRepo.DEFAULTS_USER if scope == "user"
              else MenuButtonRepo.DEFAULTS_ADMIN).get(key, ("back", ""))[0]
        label = tr(lang, lk)
    group_label = tr(lang, "menu_user") if scope == "user" else tr(lang, "menu_admin")
    cmap = {"default": tr(lang, "mn_color_default_lbl"),
            "success": tr(lang, "mn_color_success_lbl"),
            "danger": tr(lang, "mn_color_danger_lbl"),
            "primary": tr(lang, "mn_color_primary_lbl")}
    color_text = cmap.get(row["color"] or "default", tr(lang, "mn_color_default_lbl"))
    vis_text = tr(lang, "mn_vis_active") if row["is_visible"] else tr(lang, "mn_vis_hidden")
    emoji_text = "—"
    if row["emoji_id"]:
        emoji_text = (f'<tg-emoji emoji-id="{row["emoji_id"]}">'
                      f'{row["emoji_fb"] or "✨"}</tg-emoji>')
    text = (
        f"✏️ <b>{tr(lang, 'mn_edit_label')}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📂 {tr(lang, 'mn_group_label')}: <b>{group_label}</b>\n"
        f"🔑 <code>{esc(key)}</code>\n"
        f"📝 {tr(lang, 'mn_title_label')}: {esc(label[:60])}\n"
        f"🎨 {tr(lang, 'mn_color_label')}: {color_text}\n"
        f"👁 {tr(lang, 'mn_status_label')}: {vis_text}\n"
        f"💎 {tr(lang, 'mn_emoji_label')}: {emoji_text}"
    )
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text=tr(lang, "mv_up"),
                              callback_data=safe_cb(f"mn:mv:{scope}:{key}:up")),
        InlineKeyboardButton(text=tr(lang, "mv_down"),
                              callback_data=safe_cb(f"mn:mv:{scope}:{key}:down")))
    b.row(
        InlineKeyboardButton(text=tr(lang, "mv_left"),
                              callback_data=safe_cb(f"mn:mv:{scope}:{key}:left")),
        InlineKeyboardButton(text=tr(lang, "mv_right"),
                              callback_data=safe_cb(f"mn:mv:{scope}:{key}:right")))
    b.row(
        InlineKeyboardButton(text=tr(lang, "mv_top"),
                              callback_data=safe_cb(f"mn:mv:{scope}:{key}:top")),
        InlineKeyboardButton(text=tr(lang, "mv_bottom"),
                              callback_data=safe_cb(f"mn:mv:{scope}:{key}:bottom")))
    b.row(InlineKeyboardButton(text=tr(lang, "mn_edit_label"),
                                callback_data=safe_cb(f"mn:lbl:{scope}:{key}")))
    b.row(InlineKeyboardButton(text=tr(lang, "mn_set_emoji"),
                                callback_data=safe_cb(f"mn:emoji:{scope}:{key}")),
          InlineKeyboardButton(text=tr(lang, "mn_remove_emoji"),
                                callback_data=safe_cb(f"mn:emoji_del:{scope}:{key}")))
    b.row(
        InlineKeyboardButton(text=tr(lang, "mn_color_success_lbl"),
                              callback_data=safe_cb(f"mn:color:{scope}:{key}:success")),
        InlineKeyboardButton(text=tr(lang, "mn_color_danger_lbl"),
                              callback_data=safe_cb(f"mn:color:{scope}:{key}:danger")))
    b.row(
        InlineKeyboardButton(text=tr(lang, "mn_color_primary_lbl"),
                              callback_data=safe_cb(f"mn:color:{scope}:{key}:primary")),
        InlineKeyboardButton(text=tr(lang, "mn_color_default_lbl"),
                              callback_data=safe_cb(f"mn:color:{scope}:{key}:default")))
    b.row(InlineKeyboardButton(text=tr(lang, "mn_toggle_vis"),
                                callback_data=safe_cb(f"mn:vis:{scope}:{key}")))
    b.row(InlineKeyboardButton(text=tr(lang, "mn_reset"),
                                callback_data=safe_cb(f"mn:reset:{scope}:{key}")))
    b.row(InlineKeyboardButton(text=tr(lang, "back"),
                                callback_data=safe_cb(f"style:menu:{scope}")))
    await safe_edit(cb.message, text, b.as_markup())


@router.callback_query(F.data.startswith("mn:mv:"))
async def cb_mn_move(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    parts = cb.data.split(":")
    if len(parts) != 5:
        await cb.answer()
        return
    _, _, scope, key, direction = parts
    ok = MenuButtonRepo.move(scope, key, direction)
    await cb.answer("✅" if ok else "❌")
    await render_edit_panel(cb, c, scope, key)


@router.callback_query(F.data.startswith("mn:lbl:"))
async def cb_menu_label(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    parts = cb.data.split(":")
    if len(parts) != 4:
        return
    _, _, scope, key = parts
    lang = await _admin_lang(c, cb.from_user.id)
    await state.set_state(Flow.mn_label)
    await state.update_data(scope=scope, key=key)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "back"),
                             callback_data=safe_cb(f"mn:edit:{scope}:{key}"))]])
    await safe_edit(cb.message, tr(lang, "mn_set_label_ask"), kb)


@router.message(Flow.mn_label, F.text)
async def msg_mn_label(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    scope = data.get("scope")
    key = data.get("key")
    if not scope or not key:
        await state.clear()
        return
    val = (message.text or "").strip()
    if val == "-":
        MenuButtonRepo.update(scope, key, label=None)
    else:
        MenuButtonRepo.update(scope, key, label=val)
    await state.clear()
    await message.answer("✅")


@router.callback_query(F.data.startswith("mn:emoji_del:"))
async def cb_menu_emoji_del(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    parts = cb.data.split(":")
    if len(parts) != 4:
        return
    _, _, scope, key = parts
    MenuButtonRepo.update(scope, key, emoji_id=None, emoji_fb=None)
    await cb.answer("🗑", show_alert=True)
    await render_edit_panel(cb, c, scope, key)


@router.callback_query(F.data.startswith("mn:emoji:"))
async def cb_menu_emoji(cb: CallbackQuery, state: FSMContext, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    parts = cb.data.split(":")
    if len(parts) != 4:
        return
    _, _, scope, key = parts
    lang = await _admin_lang(c, cb.from_user.id)
    await state.set_state(Flow.mn_emoji)
    await state.update_data(scope=scope, key=key)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr(lang, "back"),
                             callback_data=safe_cb(f"mn:edit:{scope}:{key}"))]])
    await safe_edit(cb.message, tr(lang, "mn_set_emoji_ask"), kb)


@router.message(Flow.mn_emoji)
async def msg_mn_emoji(message: Message, state: FSMContext, c: Container):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    scope = data.get("scope")
    key = data.get("key")
    if not scope or not key:
        await state.clear()
        return
    prems = extract_premium_emojis(message)
    if not prems:
        await message.answer("⚠️")
        return
    eid, fb = prems[0]
    MenuButtonRepo.update(scope, key, emoji_id=eid, emoji_fb=fb)
    await state.clear()
    await message.answer("✅")


@router.callback_query(F.data.startswith("mn:color:"))
async def cb_menu_color(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    parts = cb.data.split(":")
    if len(parts) != 5:
        return
    _, _, scope, key, color = parts
    MenuButtonRepo.set_color(scope, key, color)
    await cb.answer("✅")
    await render_edit_panel(cb, c, scope, key)


@router.callback_query(F.data.startswith("mn:vis:"))
async def cb_menu_vis(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    parts = cb.data.split(":")
    if len(parts) != 4:
        return
    _, _, scope, key = parts
    MenuButtonRepo.toggle_visible(scope, key)
    await cb.answer("✅")
    await render_edit_panel(cb, c, scope, key)


@router.callback_query(F.data.startswith("mn:reset:"))
async def cb_menu_reset(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    parts = cb.data.split(":")
    if len(parts) != 4:
        return
    _, _, scope, key = parts
    MenuButtonRepo.reset(scope, key)
    await cb.answer("♻️", show_alert=True)
    await render_edit_panel(cb, c, scope, key)



__all__ = [name for name in globals() if not name.startswith("__")]
