# Ovoz/Musiqa Ajratuvchi Telegram Bot

Audio yoki video fayl yuborilganda, undan **ovoz (vocals)** va
**musiqa/minus (instrumental)** qismlarini alohida-alohida ajratib
beruvchi Telegram bot.

## Qanday ishlaydi

1. Foydalanuvchi audio, ovozli xabar, audio fayl, video yoki video fayl yuboradi.
2. Bot faylni yuklab oladi.
3. `ffmpeg` yordamida undan toza WAV audio ajratib olinadi (video bo'lsa — tasvir tashlab yuboriladi).
4. `audio-separator` kutubxonasi (UVR/MDX-Net modellari asosida) ovoz va musiqani ajratadi.
5. Ikkala natija MP3 formatga o'girilib, foydalanuvchiga qaytariladi.

## O'rnatish (Windows, CMD)

### 1. Python 3.12 o'rnatilganini tekshiring

```cmd
py -3.12 --version
```

Agar bo'lmasa, https://www.python.org/downloads/ dan Python 3.12 ni yuklab oling
(o'rnatishda "Add python.exe to PATH" belgisini bosishni unutmang).

### 2. Loyihani tayyorlang va virtual muhit yarating

```cmd
cd vocal_bot
py -3.12 -m venv venv
venv\Scripts\activate
```

### 3. ffmpeg o'rnating

`ffmpeg` alohida dastur bo'lib, pip orqali o'rnatilmaydi:

1. https://www.gyan.dev/ffmpeg/builds/ saytidan "release full" arxivini yuklab oling.
2. Arxivni masalan `C:\ffmpeg` papkaga oching.
3. `C:\ffmpeg\bin` papkasini Windows PATH'ga qo'shing
   (Sozlamalar → Tizim haqida → Qo'shimcha tizim sozlamalari → Muhit
   o'zgaruvchilari → Path → Yangi → `C:\ffmpeg\bin`).
4. Yangi CMD oynasini oching va tekshiring:

```cmd
ffmpeg -version
```

### 4. Python kutubxonalarini o'rnating

```cmd
pip install -r requirements.txt
```

> ⚠️ Bu qadam biroz vaqt olishi mumkin — `torch` va `onnxruntime`
> kutubxonalari ancha katta hajmda (bir necha yuz MB).

### 5. `.env` faylini sozlang

```cmd
copy .env.example .env
notepad .env
```

`.env` ichida `BOT_TOKEN` qatoriga @BotFather'dan olgan tokeningizni yozing.

### 6. Botni ishga tushiring

```cmd
python bot.py
```

Birinchi audio/video kelganda, separatsion model avtomatik yuklab olinadi
(internet tezligiga qarab bir necha daqiqa vaqt olishi mumkin) — bu bir
marta bo'ladi, keyingi so'rovlarda model qayta yuklanmaydi.

## Muhim cheklovlar (halol ogohlantirish)

- **Fayl hajmi:** standart Telegram Bot API orqali botlar odatda faqat
  **~20MB gacha** bo'lgan faylni yuklab ola oladi. Kattaroq fayllar uchun
  botni mahalliy (self-hosted) Bot API serveriga ulash kerak bo'ladi —
  bu alohida sozlash talab qiladi.
- **Vaqt:** ajratish jarayoni CPU'da ishlaydi, uzunroq audio/video
  (masalan 5+ daqiqa) bir necha daqiqa davom etishi mumkin.
- **"100% xatosiz" haqida:** kod barcha kutilgan xatoliklarni (noto'g'ri
  format, katta fayl, ffmpeg xatosi, tarmoq uzilishi) ushlab, foydalanuvchiga
  tushunarli xabar bilan qaytaradi va botni yiqilib qolishdan saqlaydi.
  Ammo uchinchi tomon xizmatlari (Telegram serverlari, model fayllarini
  yuklab olish manzili) vaqtinchalik ishlamay qolishi kabi holatlarni
  hech bir dastur 100% oldindan bilib bo'lmaydi — shu sabab tavsiya
  etilgan barqaror muhit (Python 3.12) va xatolarni to'liq ushlash orqali
  bu xavf iloji boricha kamaytirilgan.

## Loyihaviy tuzilma

```
vocal_bot/
├── bot.py              # aiogram bot: handlerlar va asosiy oqim
├── separation.py        # audio-separator kutubxonasini o'rovchi xizmat
├── media.py              # ffmpeg orqali audio ajratish/konvertatsiya
├── config.py             # .env'dan sozlamalarni o'qish
├── requirements.txt
├── .env.example
└── tmp_jobs/             # ishlash vaqtida yaratiladi, avtomatik tozalanadi
```
