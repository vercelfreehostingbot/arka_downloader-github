"""Arka Downloader section: START & MAIN."""

from .s24_router_init import *

# ══════════════════════════════════════════════════════════════
# START & MAIN
# ══════════════════════════════════════════════════════════════
async def show_first_lang_picker(target, state: FSMContext = None):
    if state:
        await state.clear()
    text = ("🌐 <b>زبان خود را انتخاب کنید</b>\n"
            "<b>Select your language</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "🇮🇷  فارسی\n"
            "🇬🇧  English")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇮🇷  فارسی",
                              callback_data="firstlang:fa")],
        [InlineKeyboardButton(text="🇬🇧  English",
                              callback_data="firstlang:en")],
    ])
    if isinstance(target, Message):
        await target.answer(text, reply_markup=kb)
    elif isinstance(target, CallbackQuery):
        await safe_edit(target.message, text, kb)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, c: Container):
    await state.clear()
    u = message.from_user
    if not u:
        return
    UserRepo.upsert(u.id, message.chat.id, u.username, u.first_name)
    user = UserRepo.get(u.id)
    if not user:
        return
    if user.is_blocked and u.id not in OWNER_IDS:
        await message.answer(tr(user_lang(user), "blocked"))
        return
    if not await check_membership(u.id):
        await send_join_prompt(message, user_lang(user))
        return

    if not user_has_chosen_lang(u.id):
        await show_first_lang_picker(message, state)
        return

    await send_start_media(message.chat.id, c.bot)
    await send_home(message, user, edit=False)


@router.callback_query(F.data.startswith("firstlang:"))
async def cb_firstlang(cb: CallbackQuery, state: FSMContext, c: Container):
    lang = cb.data.split(":", 1)[1]
    if lang not in ("fa", "en"):
        await cb.answer()
        return
    mark_lang_chosen(cb.from_user.id, lang)
    await cb.answer(tr(lang, "saved"))
    user = UserRepo.get(cb.from_user.id)
    if not user:
        return
    await send_home(cb, user, edit=True)


@router.message(Command("lang"))
async def cmd_lang(message: Message, c: Container):
    u = message.from_user
    if not u:
        return
    user = UserRepo.get(u.id)
    lang = user_lang(user)
    fa_mark = "✅ " if (user and user.lang == "fa") else ""
    en_mark = "✅ " if (user and user.lang == "en") else ""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{fa_mark}🇮🇷 فارسی",
                              callback_data="lang:set:fa")],
        [InlineKeyboardButton(text=f"{en_mark}🇬🇧 English",
                              callback_data="lang:set:en")],
        [InlineKeyboardButton(text=tr(lang, "back"),
                              callback_data="menu:home")],
    ])
    await message.answer(tr(lang, "lang_title"), reply_markup=kb)


# ⚠️ دستور /admin حذف شد
# ⚠️ دستور /cancel حذف شد


@router.callback_query(F.data == "noop")
async def cb_noop(cb: CallbackQuery):
    await cb.answer()


@router.callback_query(F.data == "check_join")
async def cb_check_join(cb: CallbackQuery, c: Container):
    u = cb.from_user
    if await check_membership(u.id):
        user = UserRepo.get(u.id)
        if not user:
            await cb.answer()
            return
        await cb.answer(tr(user_lang(user), "join_ok"))
        await send_home(cb, user, edit=True)
    else:
        user = UserRepo.get(u.id)
        lang = user_lang(user)
        await cb.answer(tr(lang, "join_first"), show_alert=True)


@router.callback_query(F.data == "menu:home")
async def cb_home(cb: CallbackQuery, state: FSMContext, c: Container):
    await cb.answer()
    await state.clear()
    user = UserRepo.get(cb.from_user.id)
    if not user:
        return
    await send_home(cb, user, edit=True)



__all__ = [name for name in globals() if not name.startswith("__")]
