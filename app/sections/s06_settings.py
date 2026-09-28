"""Arka Downloader section: SETTINGS."""

from .s05_emoji import *

# ══════════════════════════════════════════════════════════════
# SETTINGS
# ══════════════════════════════════════════════════════════════
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE), env_file_encoding="utf-8",
        case_sensitive=False, extra="ignore",
    )
    bot_token: str = ""
    owner_ids: str = ""
    bot_name: str = "دانلودر آرکا"
    owner_username: str = "@AMIRALI_IRX"

    @property
    def db_path(self) -> Path:
        return DATA_DIR / "bot.db"

    @property
    def cookies_file(self) -> Path:
        return DATA_DIR / "cookies.txt"


CFG: Optional[Settings] = None
DB_PATH: Path = DATA_DIR / "bot.db"
OWNER_IDS: list = []



__all__ = [name for name in globals() if not name.startswith("__")]
