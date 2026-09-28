"""Arka Downloader section: MODELS."""

from .s10_quality import *

# ══════════════════════════════════════════════════════════════
# MODELS
# ══════════════════════════════════════════════════════════════
@dataclass
class User:
    user_id: int
    chat_id: int
    username: Optional[str]
    first_name: Optional[str]
    downloads: int
    success_dl: int
    failed_dl: int
    is_blocked: bool
    is_vip: bool
    lang: str

    @classmethod
    def from_row(cls, r) -> "User":
        keys = set(r.keys())
        def g(k, d=None):
            return r[k] if k in keys else d
        return cls(
            user_id=int(g("user_id", 0) or 0),
            chat_id=int(g("chat_id", 0) or 0),
            username=g("username"), first_name=g("first_name"),
            downloads=int(g("downloads", 0) or 0),
            success_dl=int(g("success_dl", 0) or 0),
            failed_dl=int(g("failed_dl", 0) or 0),
            is_blocked=bool(g("is_blocked", 0)),
            is_vip=bool(g("is_vip", 0)),
            lang=str(g("lang", "fa") or "fa"),
        )


@dataclass
class Job:
    job_id: str
    user_id: int
    chat_id: int
    url: str
    title: Optional[str]
    quality: str
    duration: int
    filesize: int
    status: str
    progress: float
    file_path: Optional[str]
    thumbnail: Optional[str]
    msg_id: Optional[int]
    notice_msg_id: Optional[int]
    delete_at: Optional[float]
    created_at: Optional[float] = None
    started_at: Optional[float] = None
    finished_at: Optional[float] = None

    @classmethod
    def from_row(cls, r) -> "Job":
        keys = set(r.keys())
        def g(k, d=None):
            return r[k] if k in keys else d
        return cls(
            job_id=str(g("job_id", "") or ""),
            user_id=int(g("user_id", 0) or 0),
            chat_id=int(g("chat_id", 0) or 0),
            url=str(g("url", "") or ""),
            title=g("title"),
            quality=str(g("quality", "best") or "best"),
            duration=int(g("duration", 0) or 0),
            filesize=int(g("filesize", 0) or 0),
            status=str(g("status", "queued") or "queued"),
            progress=float(g("progress", 0) or 0),
            file_path=g("file_path"), thumbnail=g("thumbnail"),
            msg_id=g("msg_id"), notice_msg_id=g("notice_msg_id"),
            delete_at=g("delete_at"),
            created_at=g("created_at"),
            started_at=g("started_at"), finished_at=g("finished_at"),
        )


STATUS_QUEUED = "queued"
STATUS_ANALYZING = "analyzing"
STATUS_DOWNLOADING = "downloading"
STATUS_UPLOADING = "uploading"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_CANCELLED = "cancelled"
STATUS_PENDING = "pending"
ACTIVE_STATUSES = (STATUS_QUEUED, STATUS_ANALYZING,
                   STATUS_DOWNLOADING, STATUS_UPLOADING)



__all__ = [name for name in globals() if not name.startswith("__")]
