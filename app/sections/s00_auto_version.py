# -*- coding: utf-8 -*-
"""
🎬 دانلودر آرکا — Universal Premium Downloader
Version 5.3.0 — Pro Music Edition
Made with ❤️ by @AMIRALI_IRX
"""

from __future__ import annotations

import asyncio, contextlib, html, logging, os, random, re, shutil
import sqlite3, subprocess, sys, threading, time, uuid, zipfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yt_dlp
try:
    from yt_dlp.networking.impersonate import ImpersonateTarget
except ImportError:
    ImpersonateTarget = None

try:
    import curl_cffi  # noqa: F401
    HAS_CURL_CFFI = True
except Exception:
    HAS_CURL_CFFI = False

try:
    import gallery_dl
    HAS_GALLERY_DL = True
except ImportError:
    gallery_dl = None
    HAS_GALLERY_DL = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from aiogram import Bot, Dispatcher, F, Router, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BotCommand, CallbackQuery, FSInputFile, InlineKeyboardButton,
    InlineKeyboardMarkup, Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
try:
    from aiogram.client.session.middlewares.base import BaseRequestMiddleware
except Exception:
    BaseRequestMiddleware = object
from pydantic_settings import BaseSettings, SettingsConfigDict


# ══════════════════════════════════════════════════════════════
# AUTO VERSION
# ══════════════════════════════════════════════════════════════
def _detect_version() -> str:
    try:
        content = Path(__file__).read_text(encoding="utf-8", errors="ignore")
        m = re.search(r'Version\s+([\d]+\.[\d]+(?:\.[\d]+)?)', content)
        return m.group(1) if m else "0.0.0"
    except Exception:
        return "0.0.0"


FILE_VERSION = _detect_version()



__all__ = [name for name in globals() if not name.startswith("__")]
