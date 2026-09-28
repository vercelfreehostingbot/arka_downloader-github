"""Arka Downloader section: CONTAINER."""

from .s16_cancellation import *

# ══════════════════════════════════════════════════════════════
# CONTAINER
# ══════════════════════════════════════════════════════════════
@dataclass
class Container:
    bot: Optional[Bot] = None
    job_queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    shutdown_event: asyncio.Event = field(default_factory=asyncio.Event)
    worker_tasks: list = field(default_factory=list)
    bg_tasks: list = field(default_factory=list)
    last_progress: dict = field(default_factory=dict)


CONTAINER: Optional[Container] = None



__all__ = [name for name in globals() if not name.startswith("__")]
