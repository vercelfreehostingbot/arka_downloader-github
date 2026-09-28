"""Arka Downloader section: DOCKER MANAGER."""

from .s06_settings import *

# ══════════════════════════════════════════════════════════════
# DOCKER MANAGER
# ══════════════════════════════════════════════════════════════
def ensure_docker_running(api_id: str, api_hash: str):
    print(f"  {C.CYN}⏳ Checking local Telegram server (Docker)...{C.R}")
    VOLUME = "telegram-bot-api-data"
    IMAGE = "aiogram/telegram-bot-api:latest"

    def _sh(*args, timeout=30):
        try:
            return subprocess.run(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, timeout=timeout)
        except Exception:
            return None

    def _api_alive(timeout=3) -> bool:
        import urllib.request, urllib.error
        try:
            urllib.request.urlopen("http://127.0.0.1:8081/", timeout=timeout)
            return True
        except urllib.error.HTTPError as e:
            return e.code in (401, 404)
        except Exception:
            return False

    try:
        res = _sh("docker", "inspect", "-f",
                  "{{.State.Running}}", "telegram-bot-api")
        running = res is not None and "true" in (res.stdout or "").lower()
        if running and _api_alive():
            log_step("Docker", "telegram-bot-api is alive")
            return
        _sh("docker", "rm", "-f", "telegram-bot-api")
        log_step("Docker", "Starting telegram-bot-api (network=host)...")
        _sh("docker", "run", "-d",
            "--name", "telegram-bot-api", "--restart=always",
            "--network", "host",
            "-v", f"{VOLUME}:/var/lib/telegram-bot-api",
            "-e", f"TELEGRAM_API_ID={api_id}",
            "-e", f"TELEGRAM_API_HASH={api_hash}",
            "-e", "TELEGRAM_LOCAL=1", IMAGE, timeout=60)
        for i in range(20):
            time.sleep(1)
            if _api_alive(timeout=2):
                log_step("Docker", f"Telegram API online ({i+1}s)")
                return
        log_warn("Telegram API didn't respond in 20s")
    except Exception as e:
        log_warn(f"Docker auto-start warning: {e}")


def load_settings() -> Settings:
    global CFG, DB_PATH, OWNER_IDS
    # Load project .env before reading process environment. This makes direct
    # execution and systemd execution deterministic even when EnvironmentFile
    # is not available (for example during manual diagnostics).
    if ENV_FILE.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(dotenv_path=ENV_FILE, override=False)
        except Exception:
            pass

    env_token = os.getenv("BOT_TOKEN", "").strip()
    env_owners = os.getenv("OWNER_IDS", "").strip()
    api_id = os.getenv("TELEGRAM_API_ID", "2040").strip()
    api_hash = os.getenv("TELEGRAM_API_HASH",
                          "b18441a1ff607e10a989891a5462e627").strip()

    token = ""
    owner_ids_raw = ""

    if ENV_FILE.exists():
        try:
            from dotenv import dotenv_values
            env_data = dotenv_values(str(ENV_FILE))
            token = (env_data.get("BOT_TOKEN") or "").strip()
            owner_ids_raw = (env_data.get("OWNER_IDS")
                             or env_data.get("ADMIN_ID") or "").strip()
            api_id = (env_data.get("TELEGRAM_API_ID") or "2040").strip()
            api_hash = (env_data.get("TELEGRAM_API_HASH")
                        or "b18441a1ff607e10a989891a5462e627").strip()
        except Exception:
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("BOT_TOKEN="):
                        token = line.split("=", 1)[1].strip().strip('"').strip("'")
                    elif line.startswith(("OWNER_IDS=", "ADMIN_ID=")):
                        owner_ids_raw = line.split("=", 1)[1].strip().strip('"').strip("'")
                    elif line.startswith("TELEGRAM_API_ID="):
                        api_id = line.split("=", 1)[1].strip().strip('"').strip("'")
                    elif line.startswith("TELEGRAM_API_HASH="):
                        api_hash = line.split("=", 1)[1].strip().strip('"').strip("'")

    if env_token:
        token = env_token
    if env_owners:
        owner_ids_raw = env_owners

    if not token or ":" not in token:
        # Never block a daemon/service waiting for interactive credentials.
        if not sys.stdin.isatty():
            raise RuntimeError(
                f"BOT_TOKEN is missing or invalid in {ENV_FILE}. "
                "Set BOT_TOKEN in .env before starting the service."
            )
        print_banner()
        print(f"\n  {C.CYN}{C.B}▸ Setup: Bot Token{C.R}\n")
        token = input(f"  {C.CYN}▸{C.R} {C.B}BOT_TOKEN{C.R}: ").strip()
        if not token or ":" not in token:
            log_err("Invalid token format")
            sys.exit(1)

    ids = []
    for x in owner_ids_raw.replace(",", " ").replace(";", " ").split():
        x = x.strip().lstrip("@")
        if x.isdigit() or (x.startswith("-") and x[1:].isdigit()):
            ids.append(int(x))

    if not ids:
        if not sys.stdin.isatty():
            raise RuntimeError(
                f"OWNER_IDS is missing or invalid in {ENV_FILE}. "
                "Set OWNER_IDS in .env before starting the service."
            )
        raw = input(f"  {C.CYN}▸{C.R} {C.B}OWNER_IDS{C.R}: ").strip()
        for x in raw.replace(",", " ").replace(";", " ").split():
            x = x.strip().lstrip("@")
            if x.isdigit() or (x.startswith("-") and x[1:].isdigit()):
                ids.append(int(x))
        if not ids:
            log_err("Invalid Owner ID")
            sys.exit(1)

    try:
        content = (
            "# Arka Downloader Configuration\n"
            f'BOT_TOKEN="{token}"\n'
            f'OWNER_IDS="{",".join(map(str, ids))}"\n'
            f'TELEGRAM_API_ID="{api_id}"\n'
            f'TELEGRAM_API_HASH="{api_hash}"\n'
            'BOT_NAME="دانلودر آرکا"\n'
            'OWNER_USERNAME="@AMIRALI_IRX"\n'
        )
        ENV_FILE.write_text(content, encoding="utf-8")
        with contextlib.suppress(Exception):
            os.chmod(ENV_FILE, 0o600)
    except Exception:
        pass

    os.environ["BOT_TOKEN"] = token
    os.environ["OWNER_IDS"] = ",".join(map(str, ids))
    ensure_docker_running(api_id, api_hash)
    s = Settings()
    CFG = s
    DB_PATH = s.db_path
    OWNER_IDS = ids
    return s



__all__ = [name for name in globals() if not name.startswith("__")]
