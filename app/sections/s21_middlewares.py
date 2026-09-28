"""Arka Downloader section: MIDDLEWARES."""

from .s20_fsm_states import *

# ══════════════════════════════════════════════════════════════
# MIDDLEWARES
# ══════════════════════════════════════════════════════════════
class InjectMiddleware(BaseMiddleware):
    def __init__(self, container: Container):
        self.container = container
        super().__init__()

    async def __call__(self, handler, event, data):
        data["c"] = self.container
        return await handler(event, data)


class UserUpsertMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        u = getattr(event, "from_user", None)
        if u and not getattr(u, "is_bot", False):
            chat = getattr(event, "chat", None)
            if chat is None:
                msg = getattr(event, "message", None)
                if msg is not None:
                    chat = getattr(msg, "chat", None)
            chat_id = chat.id if chat else u.id
            with contextlib.suppress(Exception):
                UserRepo.upsert(u.id, chat_id, u.username, u.first_name)
        return await handler(event, data)


class BlockGuardMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        u = getattr(event, "from_user", None)
        if u and u.id not in OWNER_IDS:
            try:
                user = UserRepo.get(u.id)
                if user and user.is_blocked:
                    with contextlib.suppress(Exception):
                        if isinstance(event, CallbackQuery):
                            await event.answer("🚫", show_alert=True)
                        elif isinstance(event, Message):
                            await event.answer("🚫")
                    return None
            except Exception:
                pass
        return await handler(event, data)


class MaintenanceGuard(BaseMiddleware):
    async def __call__(self, handler, event, data):
        u = getattr(event, "from_user", None)
        if not u:
            return await handler(event, data)
        if u.id in OWNER_IDS:
            return await handler(event, data)
        try:
            user = UserRepo.get(u.id)
            if user and user.is_vip:
                return await handler(event, data)
        except Exception:
            pass
        if db_get("maintenance", "0") == "1":
            text = db_get("maintenance_text", "🔧")
            with contextlib.suppress(Exception):
                if isinstance(event, CallbackQuery):
                    await event.answer(text[:200], show_alert=True)
                elif isinstance(event, Message):
                    await event.answer(text[:4000])
            return None
        return await handler(event, data)


class CallbackRateLimitMiddleware(BaseMiddleware):
    def __init__(self, per_sec: float = 0.6):
        self.per_sec = per_sec
        self._last: dict = {}
        super().__init__()

    async def __call__(self, handler, event, data):
        if not isinstance(event, CallbackQuery):
            return await handler(event, data)
        u = getattr(event, "from_user", None)
        if u is None:
            return await handler(event, data)
        cb_data = event.data or ""
        if cb_data.startswith(("q:", "mq:", "redl:", "histview:", "favview:")):
            if u.id not in OWNER_IDS:
                now = now_ts()
                last = self._last.get(u.id, 0.0)
                if now - last < self.per_sec:
                    with contextlib.suppress(Exception):
                        await event.answer("⏳", show_alert=False)
                    return None
                self._last[u.id] = now
                if len(self._last) > 5000:
                    self._last.clear()
        return await handler(event, data)



__all__ = [name for name in globals() if not name.startswith("__")]
