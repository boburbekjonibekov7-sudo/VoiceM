# Ovoz/Musiqa Ajratuvchi Telegram Bot

Audio yoki video fayl yuborilganda, undan **ovoz (vocals)** va **musiqa/minus (instrumental)** qismlarini alohida-alohida ajratib beruvchi Telegram bot.

## Qanday ishlaydi

1. Foydalanuvchi audio, ovozli xabar, audio fayl, video yoki video fayl yuboradi.
2. Bot faylni yuklab oladi.
3. `ffmpeg` yordamida undan toza WAV audio ajratib olinadi.
4. `audio-separator` kutubxonasi ovoz va musiqani ajratadi.
5. Ikkala natija MP3 formatga o‘girilib, foydalanuvchiga qaytariladi.

## Vercel webhook rejimida deploy qilish

Loyiha Vercel Python Function sifatida tayyorlangan. Telegram update’lari `POST /api/webhook` endpoint’iga keladi; lokal ishga tushirish uchun esa `python bot.py` polling rejimi saqlab qolingan.

Vercel project’ini ushbu repository bilan ulang va quyidagi Environment Variables’ni Production, Preview va Development muhitlariga kiriting:

| O‘zgaruvchi | Qiymat |
|---|---|
| `BOT_TOKEN` | @BotFather bergan haqiqiy bot tokeni |
| `WEBHOOK_SECRET` | Uzun, tasodifiy secret; webhook requestlarini tekshiradi |
| `MAX_DOWNLOAD_MB` | Odatda `20` |
| `MAX_CONCURRENT_JOBS` | Vercel uchun `1` tavsiya etiladi |
| `WORK_DIR` | Vercel’da `/tmp/vocal_bot` bo‘lishi kerak |
| `MODEL_FILENAME` | Ixtiyoriy model nomi |

Deploy tugagach, Vercel URL’ingizni `https://your-project.vercel.app` o‘rniga qo‘yib webhook’ni bir marta o‘rnating:

```bash
curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \\
  -d "url=https://your-project.vercel.app/api/webhook" \\
  -d "secret_token=${WEBHOOK_SECRET}" \\
  -d 'allowed_updates=["message"]'
```

Webhook holatini tekshirish:

```bash
curl "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo"
```

Vercel Function serverless va vaqtinchalik filesystem’dan foydalanadi. Shu sababli `/tmp` faqat bitta invocation davomida kafolatlanadi; model cache’i cold start’dan keyin qayta yuklanishi mumkin. Audio separation CPU va `ffmpeg` talab qilgani uchun katta yoki uzoq audio fayllar Vercel Hobby duration limitiga yetishi mumkin. Yuqori hajmli production ishlatish uchun separation worker’ini alohida doimiy serverga ajratish ma’qul.

## O‘rnatish (Windows, CMD)

### 1. Python 3.12 o‘rnatilganini tekshiring

```cmd
py -3.12 --version
```

Agar bo‘lmasa, [Python](https://www.python.org/downloads/) ni o‘rnating va `Add python.exe to PATH` belgisini yoqing.

### 2. Loyihani tayyorlang va virtual muhit yarating

```cmd
cd vocal_bot
py -3.12 -m venv venv
venv\Scripts\activate
```

### 3. ffmpeg o‘rnating

`ffmpeg` pip orqali emas, alohida dastur sifatida o‘rnatiladi. [Windows build](https://www.gyan.dev/ffmpeg/builds/) arxivini o‘rnating, `bin` papkasini PATH’ga qo‘shing va tekshiring:

```cmd
ffmpeg -version
```

### 4. Python kutubxonalarini o‘rnating

```cmd
pip install -r requirements.txt
```

### 5. `.env` faylini sozlang

```cmd
copy .env.example .env
notepad .env
```

`.env` ichida `BOT_TOKEN` qatoriga @BotFather’dan olgan tokeningizni yozing.

### 6. Botni ishga tushiring

```cmd
python bot.py
```

## Muhim cheklovlar

- **Fayl hajmi:** standart Telegram Bot API odatda taxminan 20 MB gacha bo‘lgan fayllarni yuklab olishga imkon beradi.
- **Vaqt:** ajratish jarayoni CPU’da ishlaydi va uzun audio/video bir necha daqiqa davom etishi mumkin.
- **Vercel:** serverless invocation’lar vaqtinchalik fayl tizimiga ega; model cache’i doimiy saqlanmasligi mumkin. Uzoq davom etadigan separation vazifalari Vercel Function timeout’iga yetishi ehtimoli bor.

## Loyihaviy tuzilma

```text
vocal_bot/
├── api/index.py          # Vercel webhook serverless endpointi
├── vercel.json           # Vercel function va route sozlamalari
├── bot.py                # aiogram bot va umumiy handlerlar
├── separation.py         # audio-separator xizmat qatlami
├── media.py              # ffmpeg orqali audio konvertatsiyasi
├── config.py             # environment sozlamalari
├── requirements.txt
├── .env.example
└── tmp_jobs/             # lokal ishlash vaqtida yaratiladigan katalog
```
