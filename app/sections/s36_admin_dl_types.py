"""Arka Downloader section: ADMIN — DL TYPES."""

from .s35_admin_main import *

# ══════════════════════════════════════════════════════════════
# ADMIN — DL TYPES
# ══════════════════════════════════════════════════════════════
@router.callback_query(F.data == "admin:dl_types")
async def cb_admin_dl_types(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    await cb.answer()
    lang = await _admin_lang(c, cb.from_user.id)
    photo_on = db_get("photo_download_enabled", "1") == "1"
    video_on = db_get("video_download_enabled", "1") == "1"
    music_on = db_get("music_download_enabled", "1") == "1"

    text = tr(lang, "ad_dlt_title",
              photo="✅" if photo_on else "❌",
              video="✅" if video_on else "❌",
              music="✅" if music_on else "❌")

    photo_lbl = tr(lang, "dl_btn_photo").replace("🖼", "").strip()
    video_lbl = tr(lang, "dl_btn_video").replace("🎬", "").strip()
    music_lbl = tr(lang, "dl_btn_music").replace("🎵", "").strip()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"🖼 {'✅' if photo_on else '❌'} {photo_lbl}",
            callback_data="dlt:photo")],
        [InlineKeyboardButton(
            text=f"🎬 {'✅' if video_on else '❌'} {video_lbl}",
            callback_data="dlt:video")],
        [InlineKeyboardButton(
            text=f"🎵 {'✅' if music_on else '❌'} {music_lbl}",
            callback_data="dlt:music")],
        [InlineKeyboardButton(text=tr(lang, "ad_back"),
                              callback_data="admin:home")]])
    await safe_edit(cb.message, text, kb)


@router.callback_query(F.data == "dlt:photo")
async def cb_dlt_photo(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    cur = db_get("photo_download_enabled", "1")
    db_set("photo_download_enabled", "0" if cur == "1" else "1")
    await cb.answer("✅")
    await cb_admin_dl_types(cb, c)


@router.callback_query(F.data == "dlt:video")
async def cb_dlt_video(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    cur = db_get("video_download_enabled", "1")
    db_set("video_download_enabled", "0" if cur == "1" else "1")
    await cb.answer("✅")
    await cb_admin_dl_types(cb, c)


@router.callback_query(F.data == "dlt:music")
async def cb_dlt_music(cb: CallbackQuery, c: Container):
    if not await require_admin(cb):
        return
    cur = db_get("music_download_enabled", "1")
    db_set("music_download_enabled", "0" if cur == "1" else "1")
    await cb.answer("✅")
    await cb_admin_dl_types(cb, c)



__all__ = [name for name in globals() if not name.startswith("__")]
