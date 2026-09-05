"""
Telegram bot: audio yoki video fayl yuborilsa, undan ovozni (vocals)
va musiqani (instrumental / "minus") alohida-alohida ajratib beradi.

Ishga tushirish:
    python bot.py

Talablar: .env faylida BOT_TOKEN ko'rsatilgan bo'lishi kerak
(qarang: .env.example va README.md).
"""
from __future__ import annotations

import asyncio
import logging
import shutil
import uuid
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandStart
from aiogram.types import FSInputFile, Message

from config import ConfigError, load_settings
from media import MediaError, convert_to_mp3, extract_audio_to_wav
from separation import SeparationError, VocalSeparator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("vocal_bot")

WELCOME_TEXT = (
    "Salom! 👋\n\n"
    "Menga <b>audio</b>, <b>audio fayl</b>, <b>video</b> yoki <b>video fayl</b> "
    "yuboring — men undan:\n"
    "🎤 <b>Ovoz (vocals)</b>\n"
    "🎹 <b>Musiqa / minus (instrumental)</b>\n\n"
    "qismlarini alohida-alohida ajratib, qaytarib beraman.\n\n"
    "⚠️ Eslatma: fayl hajmi katta bo'lsa (odatda ~20MB dan katta), "
    "Telegram bot API cheklovi tufayli yuklab bo'lmasligi mumkin."
)

UNSUPPORTED_TEXT = (
    "Bu turdagi faylni qabul qila olmayman 🙈\n"
    "Iltimos, audio, ovozli xabar, audio fayl yoki video yuboring."
)


def build_application(settings):
    """Create the bot and register handlers for polling or webhook execution."""
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    separator = VocalSeparator(
        model_file_dir=settings.work_dir / "_models",
        model_filename=settings.model_filename,
    )
    job_semaphore = asyncio.Semaphore(settings.max_concurrent_jobs)

    @dp.message(CommandStart())
    async def handle_start(message: Message) -> None:
        await message.answer(WELCOME_TEXT)

    @dp.message(Command("help"))
    async def handle_help(message: Message) -> None:
        await message.answer(WELCOME_TEXT)

    @dp.message(F.audio | F.voice | F.video | F.video_note)
    async def handle_media(message: Message) -> None:
        await process_media_message(message, bot, separator, settings, job_semaphore)

    @dp.message(F.document)
    async def handle_document(message: Message) -> None:
        mime = (message.document.mime_type or "")
        if mime.startswith("audio/") or mime.startswith("video/"):
            await process_media_message(message, bot, separator, settings, job_semaphore)
        else:
            await message.answer(UNSUPPORTED_TEXT)

    @dp.message()
    async def handle_other(message: Message) -> None:
        await message.answer(UNSUPPORTED_TEXT)

    return bot, dp


async def main() -> None:
    try:
        settings = load_settings()
    except ConfigError as exc:
        logger.error(str(exc))
        raise SystemExit(1) from exc

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    separator = VocalSeparator(
        model_file_dir=settings.work_dir / "_models",
        model_filename=settings.model_filename,
    )
    job_semaphore = asyncio.Semaphore(settings.max_concurrent_jobs)

    @dp.message(CommandStart())
    async def handle_start(message: Message) -> None:
        await message.answer(WELCOME_TEXT)

    @dp.message(Command("help"))
    async def handle_help(message: Message) -> None:
        await message.answer(WELCOME_TEXT)

    @dp.message(F.audio | F.voice | F.video | F.video_note)
    async def handle_media(message: Message) -> None:
        await process_media_message(message, bot, separator, settings, job_semaphore)

    @dp.message(F.document)
    async def handle_document(message: Message) -> None:
        mime = (message.document.mime_type or "")
        if mime.startswith("audio/") or mime.startswith("video/"):
            await process_media_message(message, bot, separator, settings, job_semaphore)
        else:
            await message.answer(UNSUPPORTED_TEXT)

    @dp.message()
    async def handle_other(message: Message) -> None:
        await message.answer(UNSUPPORTED_TEXT)

    logger.info("Bot ishga tushdi.")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


async def process_media_message(
    message: Message,
    bot: Bot,
    separator: VocalSeparator,
    settings,
    job_semaphore: asyncio.Semaphore,
) -> None:
    """Kelgan audio/video xabarni to'liq qayta ishlab, natijalarni foydalanuvchiga qaytaradi."""
    media = message.audio or message.voice or message.video or message.video_note or message.document
    if media is None:
        await message.answer(UNSUPPORTED_TEXT)
        return

    file_size = getattr(media, "file_size", None) or 0
    max_bytes = settings.max_download_mb * 1024 * 1024
    if file_size and file_size > max_bytes:
        await message.answer(
            f"Bu fayl juda katta ({file_size / 1024 / 1024:.1f} MB). "
            f"Iltimos, {settings.max_download_mb} MB dan kichikroq fayl yuboring."
        )
        return

    status_msg = await message.answer("📥 Fayl qabul qilindi, navbatga qo'yildi...")

    job_id = uuid.uuid4().hex[:12]
    job_dir = settings.work_dir / job_id

    async with job_semaphore:
        try:
            await status_msg.edit_text("⬇️ Fayl yuklab olinmoqda...")
            job_dir.mkdir(parents=True, exist_ok=True)

            source_path = job_dir / "source_input"
            file_info = await bot.get_file(media.file_id)
            await bot.download_file(file_info.file_path, destination=source_path)

            await status_msg.edit_text("🎛 Audio tayyorlanmoqda...")
            wav_path = job_dir / "prepared.wav"
            await extract_audio_to_wav(source_path, wav_path)

            await status_msg.edit_text(
                "🧠 Ovoz va musiqa ajratilmoqda...\n"
                "Bu bir necha daqiqa vaqt olishi mumkin, iltimos kuting."
            )
            output_dir = job_dir / "output"
            stems = await asyncio.to_thread(separator.separate, wav_path, output_dir)

            await status_msg.edit_text("📦 Natijalar tayyorlanmoqda...")
            vocals_mp3 = job_dir / "vocals.mp3"
            instrumental_mp3 = job_dir / "instrumental_minus.mp3"
            await convert_to_mp3(stems["vocals"], vocals_mp3)
            await convert_to_mp3(stems["instrumental"], instrumental_mp3)

            await message.answer_audio(
                FSInputFile(vocals_mp3, filename="vocals.mp3"),
                caption="🎤 Ovoz (vocals)",
            )
            await message.answer_audio(
                FSInputFile(instrumental_mp3, filename="minus.mp3"),
                caption="🎹 Musiqa / minus (instrumental)",
            )
            await status_msg.edit_text("✅ Tayyor!")

        except MediaError as exc:
            logger.warning("MediaError (job=%s): %s", job_id, exc)
            await status_msg.edit_text(f"❌ Faylni o'qishda xatolik: {exc}")
        except SeparationError as exc:
            logger.warning("SeparationError (job=%s): %s", job_id, exc)
            await status_msg.edit_text(f"❌ Ajratishda xatolik: {exc}")
        except TelegramAPIError as exc:
            logger.warning("TelegramAPIError (job=%s): %s", job_id, exc)
            await message.answer(
                "❌ Telegramga faylni yuborishda xatolik yuz berdi "
                "(ehtimol fayl hajmi juda katta)."
            )
        except Exception:  # kutilmagan har qanday xato uchun oxirgi himoya qatlami
            logger.exception("Kutilmagan xato (job=%s)", job_id)
            await status_msg.edit_text(
                "❌ Kutilmagan xatolik yuz berdi. Iltimos, birozdan so'ng qayta urinib ko'ring."
            )
        finally:
            shutil.rmtree(job_dir, ignore_errors=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
