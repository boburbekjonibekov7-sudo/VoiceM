# VoiceM — Telegram vocal separation bot

VoiceM Telegram boti audio yoki video fayldan **vocals** va **instrumental/minus** qismlarini ajratib, ikkala natijani alohida MP3 ko‘rinishida qaytaradi. Asosiy bot kodi yangi `vocal_bot.zip` arxividan olindi; Vercel webhook ishlashi uchun serverless adapter saqlandi.

## Vercel webhook deploy

Repository Vercel Python Function sifatida sozlangan. FastAPI endpoint health tekshiruvi uchun `GET /`, Telegram update’lari uchun esa `POST /webhook` yo‘lidan foydalanadi. Vercel project environment variables ichida quyidagilar bo‘lishi kerak:

| O‘zgaruvchi | Tavsiya etilgan qiymat |
|---|---|
| `BOT_TOKEN` | BotFather bergan token |
| `WEBHOOK_SECRET` | Tasodifiy maxfiy satr |
| `MAX_DOWNLOAD_MB` | `20` |
| `MAX_CONCURRENT_JOBS` | `1` |
| `WORK_DIR` | `/tmp/vocal_bot` |
| `MODEL_FILENAME` | Ixtiyoriy model nomi |

Deploy’dan keyin webhook’ni bir marta o‘rnating:

```bash
curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
  -d "url=https://your-project.vercel.app/webhook" \
  -d "secret_token=${WEBHOOK_SECRET}" \
  -d 'allowed_updates=["message"]'
```

Webhook holatini tekshirish:

```bash
curl "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo"
```

`requirements.txt` Vercel bundle hajmini kamaytirish uchun CPU-only PyTorch wheel’dan foydalanadi. `imageio-ffmpeg` Vercel’da system ffmpeg o‘rnatilmagan holatda ham audio konvertatsiyasini bajaradi. Model yuklanishi va separation CPU’da ishlashi sababli birinchi so‘rov cold start’da uzoqroq davom etishi mumkin; katta production yuklamasi uchun alohida worker server ma’qul.

## Lokal ishga tushirish

Windows yoki Linux’da Python 3.12 o‘rnating, `.env.example` faylidan `.env` yarating va `BOT_TOKEN` qiymatini kiriting. Lokal muhitda system `ffmpeg` PATH’da bo‘lishi yoki `imageio-ffmpeg` package binary’si ishlatilishi mumkin.

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows CMD
.venv\Scripts\activate
pip install -r requirements.txt
python bot.py
```

Lokal `python bot.py` polling rejimida ishlaydi. Vercel’da esa `api/index.py` serverless endpointi aiogram dispatcher’iga Telegram update’larini uzatadi.

## Tuzilma

```text
api/index.py      # Vercel FastAPI webhook endpointi
bot.py            # aiogram handlerlari va polling rejimi
config.py         # environment sozlamalari
media.py          # ffmpeg audio konvertatsiyasi
separation.py     # audio-separator modeli
vercel.json       # Vercel Function sozlamalari
requirements.txt  # pinned CPU-only dependencies
```

Maxfiy `.env`, tokenlar va model cache’lari repository’ga qo‘shilmasligi kerak.
