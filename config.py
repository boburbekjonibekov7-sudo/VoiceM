"""Environment-backed settings for the vocal bot."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class ConfigError(RuntimeError):
    """Raised when a required setting is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    bot_token: str
    webhook_secret: Optional[str]
    max_download_mb: int
    max_concurrent_jobs: int
    work_dir: Path
    model_filename: Optional[str]


def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise ConfigError(
            "BOT_TOKEN topilmadi. Vercel Environment Variables yoki .env fayliga "
            "BOT_TOKEN=... qatorini qo'shing."
        )

    try:
        max_download_mb = int(os.getenv("MAX_DOWNLOAD_MB", "20"))
        max_concurrent_jobs = int(os.getenv("MAX_CONCURRENT_JOBS", "1"))
    except ValueError as exc:
        raise ConfigError("MAX_DOWNLOAD_MB va MAX_CONCURRENT_JOBS son bo'lishi kerak.") from exc
    if max_download_mb <= 0 or max_concurrent_jobs <= 0:
        raise ConfigError("MAX_DOWNLOAD_MB va MAX_CONCURRENT_JOBS noldan katta bo'lishi kerak.")

    work_dir = Path(os.getenv("WORK_DIR", "/tmp/vocal_bot"))
    work_dir.mkdir(parents=True, exist_ok=True)
    model_filename = os.getenv("MODEL_FILENAME", "").strip() or None
    webhook_secret = os.getenv("WEBHOOK_SECRET", "").strip() or None

    return Settings(
        bot_token=token,
        webhook_secret=webhook_secret,
        max_download_mb=max_download_mb,
        max_concurrent_jobs=max_concurrent_jobs,
        work_dir=work_dir,
        model_filename=model_filename,
    )
