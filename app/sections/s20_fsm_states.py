"""Arka Downloader section: FSM STATES."""

from .s19_keyboard import *

# ══════════════════════════════════════════════════════════════
# FSM STATES
# ══════════════════════════════════════════════════════════════
class Flow(StatesGroup):
    dl_waiting_url = State()
    support_message = State()
    a_users_search = State()
    a_broadcast_content = State()
    a_broadcast_confirm = State()
    a_setting_value = State()
    a_setting_maint = State()
    a_limit_value = State()
    a_channel = State()
    a_ticket_reply = State()
    a_auto_backup_hours = State()
    a_up_zip = State()
    a_miniapp_url = State()
    emoji_add_premium = State()
    emoji_add_normal = State()
    start_emoji = State()
    start_sticker = State()
    mn_label = State()
    mn_emoji = State()
    cbtn_label = State()
    cbtn_callback = State()
    text_value = State()
    guide_text = State()
    admin_new_id = State()
    admin_search = State()

    a_announce_msg = State()
    a_announce_media = State()
    a_announce_confirm = State()
    a_announce_schedule_time = State()
    a_announce_test = State()
    a_announce_channel_id = State()
    a_anc_text = State()
    a_anc_media = State()
    a_anc_confirm = State()
    a_anc_test = State()



__all__ = [name for name in globals() if not name.startswith("__")]
