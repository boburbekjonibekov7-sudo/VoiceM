"""
Ovoz (vocal) va musiqa (instrumental / "minus") ajratish xizmati.

`audio-separator` kutubxonasidan foydalanamiz (UVR/MDX-Net/Demucs
modellari asosida) — bu loyiha faol qo'llab-quvvatlanadi va Python 3.12
bilan yaxshi ishlaydi. Model faqat bot ishga tushganda BIR MARTA
yuklanadi (xotira va vaqtni tejash uchun); har bir so'rov uchun
qayta yuklanmaydi.

Diqqat: bu modul CPU'ni band qiladigan (bloklovchi) chaqiruvlarni ichida
saqlaydi — shuning uchun uni har doim asyncio.to_thread(...) orqali
chaqirish kerak, aks holda bot boshqa foydalanuvchilarga javob
bera olmay qoladi.
"""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SeparationError(RuntimeError):
    """Ovoz/musiqa ajratish jarayonida xatolik yuz berganda ko'tariladi."""


class VocalSeparator:
    """`audio_separator.separator.Separator`ni o'rab turuvchi thread-xavfsiz singleton."""

    def __init__(self, model_file_dir: Path, model_filename: Optional[str] = None) -> None:
        self._model_file_dir = model_file_dir
        self._model_filename = model_filename
        self._separator = None
        self._lock = threading.Lock()  # model yuklash/ishlatish parallel bo'lib ketmasligi uchun

    def _ensure_loaded(self) -> None:
        if self._separator is not None:
            return

        # Import shu yerda (funksiya ichida) qilinadi — bot boshqa
        # buyruqlarga tezroq javob berishi uchun og'ir kutubxona faqat
        # birinchi audio kelganda yuklanadi.
        from audio_separator.separator import Separator

        logger.info("Ajratish modeli yuklanmoqda (birinchi so'rovda biroz vaqt olishi mumkin)...")
        self._model_file_dir.mkdir(parents=True, exist_ok=True)
        self._separator = Separator(
            model_file_dir=str(self._model_file_dir),
            output_format="WAV",
        )
        self._separator.load_model(model_filename=self._model_filename)
        logger.info("Model muvaffaqiyatli yuklandi.")

    def separate(self, input_wav: Path, output_dir: Path) -> dict[str, Path]:
        """
        Berilgan WAV faylni Vocals va Instrumental (minus) stemlarga ajratadi.
        Qaytadi: {"vocals": Path, "instrumental": Path}
        """
        with self._lock:
            self._ensure_loaded()
            output_dir.mkdir(parents=True, exist_ok=True)

            # audio-separator o'z ichida output_dir'ni Separator obyekti
            # yaratilganda belgilaydi, shuning uchun har bir so'rov uchun
            # uni qayta ko'rsatamiz.
            self._separator.output_dir = str(output_dir)

            try:
                output_names = {
                    "Vocals": "vocals",
                    "Instrumental": "instrumental",
                }
                result_files = self._separator.separate(str(input_wav), output_names)
            except Exception as exc:  # kutubxona turli xil xatoliklar chiqarishi mumkin
                logger.exception("Ajratish jarayonida xato")
                raise SeparationError(f"Ovoz/musiqa ajratishda xatolik: {exc}") from exc

        vocals_path: Optional[Path] = None
        instrumental_path: Optional[Path] = None
        for name in result_files:
            full_path = Path(name)
            if not full_path.is_absolute():
                full_path = output_dir / full_path
            lower = full_path.name.lower()
            if "vocals" in lower and "instrumental" not in lower:
                vocals_path = full_path
            elif "instrumental" in lower:
                instrumental_path = full_path

        if vocals_path is None or instrumental_path is None:
            raise SeparationError(
                "Ajratilgan fayllar topilmadi — kutubxona natija formatini o'zgartirgan bo'lishi mumkin."
            )

        return {"vocals": vocals_path, "instrumental": instrumental_path}
