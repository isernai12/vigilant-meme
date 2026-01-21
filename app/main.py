from __future__ import annotations

import asyncio

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.routes_admin import router as admin_router
from app.routes_api import router as api_router
from app.telegram_bot import handle_update, set_webhook

app = FastAPI(title=settings.app_name)

app.include_router(admin_router)
app.include_router(api_router)


@app.post("/telegram/webhook/{secret}")
async def telegram_webhook(secret: str, request: Request):
    if secret != settings.webhook_secret:
        raise HTTPException(status_code=403, detail="Forbidden")
    update_data = await request.json()
    asyncio.create_task(handle_update(update_data))
    return JSONResponse({"status": "ok"})


@app.on_event("startup")
async def startup_event() -> None:
    await set_webhook()
