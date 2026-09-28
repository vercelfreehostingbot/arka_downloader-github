"""Arka Downloader section: ROUTER INIT."""

from .s23_job_pipeline import *

# ══════════════════════════════════════════════════════════════
# ROUTER INIT
# ══════════════════════════════════════════════════════════════
_ANSWERED_CB: dict = {}
_orig_cb_answer = CallbackQuery.answer


async def _cb_answer_once(self, *args, **kwargs):
    qid = getattr(self, "id", None)
    if qid is not None:
        if qid in _ANSWERED_CB:
            return True
        _ANSWERED_CB[qid] = None
        if len(_ANSWERED_CB) > 5000:
            for k in list(_ANSWERED_CB)[:2500]:
                _ANSWERED_CB.pop(k, None)
    return await _orig_cb_answer(self, *args, **kwargs)


with contextlib.suppress(Exception):
    CallbackQuery.answer = _cb_answer_once

router = Router(name="main")



__all__ = [name for name in globals() if not name.startswith("__")]
