from __future__ import annotations

import httpx

from app import config


async def send_message(chat_id: int, text: str, reply_markup: dict | None = None) -> None:
    payload: dict[str, object] = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage",
            json=payload,
            timeout=10,
        )


async def answer_callback_query(callback_query_id: str, text: str | None = None) -> None:
    payload: dict[str, object] = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{config.BOT_TOKEN}/answerCallbackQuery",
            json=payload,
            timeout=10,
        )


async def edit_message(chat_id: int, message_id: int, text: str, reply_markup: dict | None = None) -> None:
    payload: dict[str, object] = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{config.BOT_TOKEN}/editMessageText",
            json=payload,
            timeout=10,
        )

