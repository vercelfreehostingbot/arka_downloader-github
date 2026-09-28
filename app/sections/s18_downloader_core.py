"""Arka Downloader section: DOWNLOADER — CORE."""

from .s17_container import *

# ══════════════════════════════════════════════════════════════
# DOWNLOADER — CORE
# ══════════════════════════════════════════════════════════════
USER_AGENTS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
)


@dataclass
class VideoInfo:
    title: str
    duration: int
    filesize: int
    uploader: Optional[str]
    site: Optional[str]
    thumbnail: Optional[str]
    available_qualities: set = field(
        default_factory=lambda: {"best", "audio"})
    max_height: int = 0


@dataclass
class DownloadResult:
    path: Path
    title: str
    duration: int
    filesize: int
    artist: Optional[str] = None
    thumbnail_path: Optional[Path] = None


class DownloadError(Exception):
    pass


class DownloadCancelled(DownloadError):
    pass


def _base_ydl_opts() -> dict:
    opts = {
        "quiet": True, "no_warnings": True, "noplaylist": True,
        "socket_timeout": 30, "nocheckcertificate": True,
        "geo_bypass": True, "age_limit": 99,
        "http_headers": {"User-Agent": random.choice(USER_AGENTS)},
    }
    if ImpersonateTarget is not None and HAS_CURL_CFFI:
        with contextlib.suppress(Exception):
            opts["impersonate"] = ImpersonateTarget(client="chrome")
    cookies_path = DATA_DIR / "cookies.txt"
    if cookies_path.exists():
        opts["cookiefile"] = str(cookies_path)
    return opts


def _quality_format(q: str) -> str:
    if is_audio_quality(q):
        return "bestaudio/best"
    if q == "best":
        return "bestvideo+bestaudio/best"
    h = QUALITY_HEIGHTS.get(q)
    if h:
        return f"bestvideo[height<={h}]+bestaudio/best[height<={h}]"
    return "bestvideo+bestaudio/best"


def _extract_available_qualities(info: dict) -> set:
    available = {"best", "audio"}
    heights = set()
    has_video = False
    for f in (info.get("formats") or []):
        vcodec = (f.get("vcodec") or "none").lower()
        h = f.get("height") or 0
        if vcodec and vcodec != "none":
            has_video = True
            if h:
                heights.add(int(h))
    if not has_video:
        return {"best", "audio"}
    for qkey, qh in QUALITY_HEIGHTS.items():
        for h in heights:
            if h >= qh:
                available.add(qkey)
                break
    return available


def analyze_url(url: str) -> VideoInfo:
    opts = _base_ydl_opts()
    opts["skip_download"] = True
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as e:
        raise DownloadError(str(e)) from e
    if not info:
        raise DownloadError("empty info")

    best_size = 0
    max_h = 0
    for f in (info.get("formats") or []):
        sz = f.get("filesize") or f.get("filesize_approx") or 0
        if sz > best_size:
            best_size = sz
        h = f.get("height") or 0
        if h > max_h:
            max_h = int(h)

    avail = _extract_available_qualities(info)

    return VideoInfo(
        title=info.get("title") or "No Title",
        duration=int(info.get("duration") or 0),
        filesize=best_size or int(
            info.get("filesize") or info.get("filesize_approx") or 0),
        uploader=info.get("uploader"),
        site=info.get("extractor_key"),
        thumbnail=info.get("thumbnail"),
        available_qualities=avail,
        max_height=max_h,
    )


async def analyze_async(url: str) -> VideoInfo:
    try:
        return await asyncio.to_thread(analyze_url, url)
    except DownloadError:
        raise
    except Exception as e:
        raise DownloadError(f"analyze failed: {e}") from e


def _fmt_speed(b) -> str:
    try:
        b = float(b or 0)
    except (TypeError, ValueError):
        return "0 B/s"
    for u in ("B/s", "KB/s", "MB/s", "GB/s"):
        if b < 1024:
            return f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} TB/s"


def _fmt_eta(s) -> str:
    if s is None:
        return "--"
    try:
        m, x = divmod(int(s), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{x:02d}" if h else f"{m:02d}:{x:02d}"
    except (TypeError, ValueError):
        return "--"


def download_sync(job_id: str, url: str, quality: str,
                  loop: asyncio.AbstractEventLoop,
                  progress_cb, cancelled_cb) -> DownloadResult:
    jd = DOWNLOAD_DIR / job_id
    if jd.exists():
        shutil.rmtree(jd, ignore_errors=True)
    jd.mkdir(parents=True, exist_ok=True)

    def _schedule(p, sp, et):
        try:
            fut = asyncio.run_coroutine_threadsafe(progress_cb(p, sp, et), loop)
            fut.add_done_callback(lambda f: f.exception() and None)
        except Exception:
            pass

    def _hook(d):
        if cancelled_cb(job_id):
            raise DownloadCancelled("cancelled")
        st = d.get("status")
        if st == "downloading":
            tot = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            dn = d.get("downloaded_bytes") or 0
            if tot and tot > 0:
                p = dn / tot * 100
            else:
                fi = d.get("fragment_index") or 0
                fc = d.get("fragment_count") or 0
                p = (fi / fc * 100) if (fc and fc > 0) else 0.0
            _schedule(p, _fmt_speed(d.get("speed") or 0),
                      _fmt_eta(d.get("eta")))
        elif st == "finished":
            _schedule(100.0, "…", "00:00")

    opts = _base_ydl_opts()
    opts.update({
        "outtmpl": str(jd / "%(title).80s-%(id)s.%(ext)s"),
        "retries": 3, "fragment_retries": 3,
        "continuedl": True, "progress_hooks": [_hook],
    })

    if is_audio_quality(quality):
        if not shutil.which("ffmpeg"):
            raise DownloadError("FFmpeg not installed")
        opts["format"] = "bestaudio/best"
        if quality == "audio_best":
            opts["prefer_ffmpeg"] = True
        else:
            bitrate = {"audio_320": "320", "audio_128": "128"}.get(quality, "192")
            opts.update({
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": bitrate,
                }],
                "prefer_ffmpeg": True,
            })
    else:
        opts.update({
            "format": _quality_format(quality),
            "merge_output_format": "mp4",
        })
        if db_get("download_subtitles", "0") == "1":
            opts.update({
                "writesubtitles": True, "writeautomaticsub": True,
                "subtitleslangs": ["fa", "en"],
                "subtitlesformat": "srt/best",
            })

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except yt_dlp.utils.DownloadError as e:
        raise DownloadError(str(e)) from e
    if not info:
        raise DownloadError("empty info")

    final = None
    if is_audio_quality(quality):
        audios = [p for p in jd.rglob("*") if p.is_file()
                  and p.suffix.lower() in (".mp3", ".m4a", ".opus",
                                            ".ogg", ".webm", ".aac",
                                            ".flac", ".wav")]
        if audios:
            final = max(audios, key=lambda p: p.stat().st_size)
    if final is None:
        files = [p for p in jd.rglob("*") if p.is_file() and
                 p.suffix.lower() not in (".srt", ".vtt", ".ass", ".json")]
        if not files:
            raise DownloadError("No output file")
        files.sort(key=lambda p: p.stat().st_size, reverse=True)
        final = files[0]

    dur = int(info.get("duration") or 0)
    if dur <= 0:
        dur = _probe_duration(final)

    return DownloadResult(path=final,
                          title=info.get("title") or "No Title",
                          duration=dur,
                          filesize=final.stat().st_size)


def _gallery_dl_sync(url: str, jd: Path, want_video: bool) -> Optional[Path]:
    if not HAS_GALLERY_DL:
        return None
    try:
        import gallery_dl.job  # noqa: F401
        gallery_dl.config.load()
        gcfg = gallery_dl.config
        gcfg.set(("extractor",), "base-directory", str(jd))
        gcfg.set(("extractor",), "directory", ["."])
        gcfg.set(("extractor",), "filename", "{filename}.{extension}")
        cookies_path = DATA_DIR / "cookies.txt"
        if cookies_path.exists():
            gcfg.set(("extractor",), "cookies", str(cookies_path))
        gcfg.set(("extractor", "generic"), "enabled", True)
        gcfg.set(("output",), "mode", "null")
        gallery_dl.job.DownloadJob(url).run()
    except Exception as e:
        logging.info(f"[gallery-dl] failed: {e}")
        return None
    all_files = [f for f in jd.rglob("*") if f.is_file()]
    files = [f for f in all_files
             if f.suffix.lower() in (VIDEO_EXTS if want_video else IMAGE_EXTS)]
    if not files:
        return None
    files.sort(key=lambda p: p.stat().st_size, reverse=True)
    return files[0]


async def download_photo_only(url: str, job_id: str) -> DownloadResult:
    import aiohttp
    jd = DOWNLOAD_DIR / job_id
    if jd.exists():
        shutil.rmtree(jd, ignore_errors=True)
    jd.mkdir(parents=True, exist_ok=True)
    try:
        max_mb = int(db_get("max_photo_size_mb", "2048"))
    except (TypeError, ValueError):
        max_mb = 2048
    max_bytes = max_mb * 1024 * 1024
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "image/avif,image/webp,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }
    timeout = aiohttp.ClientTimeout(total=600, connect=30)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as sess:
            async with sess.get(url, headers=headers, allow_redirects=True) as r:
                if r.status == 200:
                    ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip().lower()
                    if ctype.startswith("image/"):
                        ext = _IMG_CTYPE_EXT.get(ctype, ".jpg")
                        path = jd / f"image_{job_id}{ext}"
                        written = 0
                        with open(path, "wb") as f:
                            async for chunk in r.content.iter_chunked(65536):
                                written += len(chunk)
                                if written > max_bytes:
                                    raise DownloadError("Image too large")
                                f.write(chunk)
                        if path.stat().st_size > 0:
                            return DownloadResult(path=path, title="Image",
                                                  duration=0,
                                                  filesize=path.stat().st_size)
    except DownloadError:
        raise
    except Exception as e:
        logging.info(f"[photo] direct failed: {e}")

    path = await asyncio.to_thread(_gallery_dl_sync, url, jd, False)
    if path and path.exists() and path.stat().st_size > 0:
        return DownloadResult(path=path, title=path.stem,
                              duration=0, filesize=path.stat().st_size)

    try:
        opts = _base_ydl_opts()
        opts["skip_download"] = True
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        thumb_url = info.get("thumbnail") if info else None
        if thumb_url:
            async with aiohttp.ClientSession(timeout=timeout) as sess:
                async with sess.get(thumb_url, headers=headers) as r:
                    if r.status == 200:
                        path = jd / f"thumb_{job_id}.jpg"
                        with open(path, "wb") as f:
                            async for chunk in r.content.iter_chunked(65536):
                                f.write(chunk)
                        if path.stat().st_size > 0:
                            return DownloadResult(path=path, title="Thumbnail",
                                                  duration=0,
                                                  filesize=path.stat().st_size)
    except Exception as e:
        logging.info(f"[photo] yt-dlp thumb failed: {e}")

    raise DownloadError("No image found / عکسی پیدا نشد")


async def download_video_only(url: str, job_id: str) -> DownloadResult:
    jd = DOWNLOAD_DIR / job_id
    if jd.exists():
        shutil.rmtree(jd, ignore_errors=True)
    jd.mkdir(parents=True, exist_ok=True)
    try:
        loop = asyncio.get_running_loop()
        async def _noop_progress(p, s, e):
            return None

        result = await asyncio.to_thread(
            download_sync, job_id, url, "best", loop,
            _noop_progress, is_cancelled)
        if result.path.exists() and is_video_file(result.path):
            return result
    except Exception as e:
        logging.info(f"[video] yt-dlp failed: {e}")
    path = await asyncio.to_thread(_gallery_dl_sync, url, jd, True)
    if path and path.exists() and path.stat().st_size > 0:
        return DownloadResult(path=path, title=path.stem,
                              duration=0, filesize=path.stat().st_size)
    raise DownloadError("No video found / ویدئویی پیدا نشد")


async def download_music_only(url: str, job_id: str,
                              quality: str = "audio") -> DownloadResult:
    """دانلود آهنگ به صورت MP3 با متادیتا و کاور."""
    jd = DOWNLOAD_DIR / job_id
    if jd.exists():
        shutil.rmtree(jd, ignore_errors=True)
    jd.mkdir(parents=True, exist_ok=True)

    if not shutil.which("ffmpeg"):
        raise DownloadError("FFmpeg required for music download")

    def _sync() -> dict:
        opts = _base_ydl_opts()
        base_opts = {
            "outtmpl": str(jd / "%(title).80s.%(ext)s"),
            "format": "bestaudio/best",
            "prefer_ffmpeg": True,
            "writethumbnail": True,
        }
        if quality == "audio_best":
            opts.update(base_opts)
        else:
            bitrate = {"audio_320": "320", "audio_128": "128"}.get(quality, "192")
            base_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": bitrate,
            }]
            opts.update(base_opts)
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=True)

    try:
        info = await asyncio.to_thread(_sync)
    except yt_dlp.utils.DownloadError as e:
        raise DownloadError(str(e)) from e
    except DownloadError:
        raise
    except Exception as e:
        raise DownloadError(f"music failed: {e}") from e

    if not info:
        raise DownloadError("empty info")

    mp3s = [p for p in jd.glob("*.mp3") if p.is_file()]
    if not mp3s:
        audios = [p for p in jd.rglob("*") if p.is_file() and
                  p.suffix.lower() in (".mp3", ".m4a", ".opus",
                                       ".ogg", ".webm", ".aac",
                                       ".flac", ".wav")]
        if not audios:
            raise DownloadError("No audio output")
        mp3s = audios
    mp3 = max(mp3s, key=lambda p: p.stat().st_size)

    thumb_path: Optional[Path] = None
    for ext in (".webp", ".jpg", ".jpeg", ".png"):
        thumbs = [t for t in jd.glob(f"*{ext}") if t.is_file()]
        if thumbs:
            thumb_path = max(thumbs, key=lambda p: p.stat().st_size)
            break

    if thumb_path and thumb_path.suffix.lower() == ".webp" and HAS_PIL:
        try:
            with Image.open(thumb_path) as im:
                jpg_path = thumb_path.with_suffix(".jpg")
                im.convert("RGB").save(jpg_path, "JPEG", quality=88)
                thumb_path = jpg_path
        except Exception:
            pass

    title = str(info.get("title") or mp3.stem)
    artist = (info.get("artist") or info.get("uploader") or
              info.get("creator") or info.get("channel") or
              info.get("album_artist") or "Unknown")
    artist = str(artist).strip() or "Unknown"

    duration = int(info.get("duration") or 0)
    if duration <= 0:
        duration = _probe_duration(mp3)

    return DownloadResult(
        path=mp3,
        title=title,
        duration=duration,
        filesize=mp3.stat().st_size,
        artist=artist,
        thumbnail_path=thumb_path,
    )



__all__ = [name for name in globals() if not name.startswith("__")]
