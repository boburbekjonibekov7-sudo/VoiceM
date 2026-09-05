"""Vercel serverless entrypoint for Telegram webhook updates."""
from __future__ import annotations

import hmac
import logging
from functools import lru_cache
from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from bot import build_application
from config import Settings, load_settings

app = FastAPI(title="VoiceM Telegram Webhook")
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_runtime() -> tuple[Settings, Bot, Dispatcher]:
    settings = load_settings()
    bot, dispatcher = build_application(settings)
    return settings, bot, dispatcher


@app.get("/")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "VoiceM Telegram webhook"}


@app.post("/diagnostic/runtime")
async def diagnostic_runtime(
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> JSONResponse:
    settings = load_settings()
    if not settings.webhook_secret or not hmac.compare_digest(
        x_telegram_bot_api_secret_token or "", settings.webhook_secret
    ):
        raise HTTPException(status_code=404, detail="Not Found")
    try:
        _, bot, dispatcher = get_runtime()
        return JSONResponse(
            {
                "ok": True,
                "dispatcher_ready": bool(dispatcher),
                "bot_token_configured": bool(settings.bot_token),
                "webhook_secret_configured": bool(settings.webhook_secret),
                "work_dir": str(settings.work_dir),
            }
        )
    except Exception as exc:
        logger.exception("Runtime diagnostic failed")
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error_type": type(exc).__name__,
                "error": str(exc)[:500],
            },
        )


@app.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> JSONResponse:
    settings, bot, dispatcher = get_runtime()

    # If configured, Telegram's secret header is required for every webhook call.
    if settings.webhook_secret and not hmac.compare_digest(
        x_telegram_bot_api_secret_token or "", settings.webhook_secret
    ):
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    try:
        payload: dict[str, Any] = await request.json()
        update = Update.model_validate(payload)
        await dispatcher.feed_update(bot, update)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid Telegram update payload") from exc

    return JSONResponse({"ok": True})
