"""
Botning sozlamalari shu yerdan o'qiladi.
Barcha maxfiy qiymatlar (token va h.k.) .env faylidan olinadi —
kodning ichiga hech qanday token yozilmaydi.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# .env faylini loyihaning ildiz papkasidan yuklaymiz
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class ConfigError(RuntimeError):
    """Sozlamalarda xatolik bo'lsa shu xato ko'tariladi."""


@dataclass(frozen=True)
class Settings:
    bot_token: str
    max_download_mb: int
    max_concurrent_jobs: int
    work_dir: Path
    model_filename: Optional[str]


def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise ConfigError(
            "BOT_TOKEN topilmadi. .env faylini yarating va unga "
            "BOT_TOKEN=... qatorini qo'shing (.env.example'ga qarang)."
        )

    max_download_mb = int(os.getenv("MAX_DOWNLOAD_MB", "20"))
    max_concurrent_jobs = int(os.getenv("MAX_CONCURRENT_JOBS", "1"))
    work_dir = Path(os.getenv("WORK_DIR", str(BASE_DIR / "tmp_jobs")))
    model_filename = os.getenv("MODEL_FILENAME", "").strip() or None

    work_dir.mkdir(parents=True, exist_ok=True)

    return Settings(
        bot_token=token,
        max_download_mb=max_download_mb,
        max_concurrent_jobs=max_concurrent_jobs,
        work_dir=work_dir,
        model_filename=model_filename,
    )
