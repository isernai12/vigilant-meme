from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import config
from app import db
from app.admin import router as admin_router
from app.bot_logic import handle_callback, handle_message

app = FastAPI()


@app.on_event("startup")
async def startup() -> None:
    db.init_db()


@app.post("/telegram/webhook/{secret}")
async def telegram_webhook(secret: str, request: Request) -> JSONResponse:
    if secret != config.WEBHOOK_SECRET:
        return JSONResponse({"ok": False, "error": "invalid secret"}, status_code=403)
    update = await request.json()
    if "message" in update:
        await handle_message(update["message"])
    if "callback_query" in update:
        await handle_callback(update["callback_query"])
    return JSONResponse({"ok": True})


app.include_router(admin_router)

