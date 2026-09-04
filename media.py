"""
Video/audio fayllardan ffmpeg yordamida "toza" WAV audio ajratib olish
va natijaviy stemlarni MP3'ga aylantirish uchun yordamchi funksiyalar.

Barcha og'ir ish subprocess orqali ffmpeg'da bajariladi — bu Telegram
botning event loop'ini bloklamaydi (chaqiruvchi tomon asyncio.to_thread
yoki create_subprocess_exec orqali chaqiradi).
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class MediaError(RuntimeError):
    """ffmpeg orqali media bilan ishlashda xatolik yuz berganda ko'tariladi."""


async def _run_ffmpeg(args: list[str], timeout: float = 600.0) -> None:
    """ffmpeg buyrug'ini asinxron tarzda ishga tushiradi va xatolarni tekshiradi."""
    process = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-y",  # mavjud faylni so'ramasdan almashtirish
        "-hide_banner",
        "-loglevel",
        "error",
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        _, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except asyncio.TimeoutError as exc:
        process.kill()
        await process.wait()
        raise MediaError("ffmpeg belgilangan vaqt ichida tugamadi (fayl juda uzun bo'lishi mumkin).") from exc

    if process.returncode != 0:
        err_text = stderr.decode(errors="ignore").strip()
        logger.error("ffmpeg xatosi: %s", err_text)
        raise MediaError(f"ffmpeg fayl bilan ishlay olmadi: {err_text[:300] or 'nomaʼlum xato'}")


async def extract_audio_to_wav(input_path: Path, output_path: Path) -> Path:
    """
    Istalgan audio yoki video fayldan bitta audio trekni ajratib,
    44.1kHz, stereo WAV formatga o'giradi (bu separatsion model uchun
    eng ishonchli kirish formati).
    """
    if not input_path.exists():
        raise MediaError(f"Kirish fayli topilmadi: {input_path}")

    args = [
        "-i", str(input_path),
        "-vn",              # video oqimini olib tashlash (agar mavjud bo'lsa)
        "-ac", "2",          # stereo
        "-ar", "44100",      # 44.1kHz
        "-acodec", "pcm_s16le",
        str(output_path),
    ]
    await _run_ffmpeg(args)

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise MediaError("Audio ajratib olinmadi — fayl formatini tekshiring.")

    return output_path


async def convert_to_mp3(input_path: Path, output_path: Path, bitrate: str = "192k") -> Path:
    """WAV/boshqa formatdagi natijani yengil MP3 ko'rinishiga o'giradi (yuklab berish tezroq bo'lishi uchun)."""
    if not input_path.exists():
        raise MediaError(f"Konvertatsiya uchun fayl topilmadi: {input_path}")

    args = [
        "-i", str(input_path),
        "-codec:a", "libmp3lame",
        "-b:a", bitrate,
        str(output_path),
    ]
    await _run_ffmpeg(args)

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise MediaError("MP3'ga konvertatsiya muvaffaqiyatsiz tugadi.")

    return output_path
