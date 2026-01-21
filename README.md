# Telegram MCQ Bot + Admin Website (FastAPI + Turso libSQL)

Minimal single-server app that hosts both:

- Admin website (Telegram OTP login)
- Telegram bot webhook endpoint

## Features

- Telegram OTP login for admin panel
- Add/list MCQ questions
- Telegram bot quiz with inline buttons
- Turso libSQL via embedded replica
- Tables auto-created on first run

## Project Structure

```
app/
  admin.py
  admin_pages.py
  bot_logic.py
  config.py
  db.py
  main.py
  security.py
  telegram_api.py
requirements.txt
README.md
```

## Setup

1. Create a Telegram bot via BotFather.
2. Update `app/config.py` placeholders:
   - `BOT_TOKEN`
   - `WEBHOOK_SECRET`
   - `LIBSQL_URL`
   - `LIBSQL_AUTH_TOKEN`
   - `APP_SECRET`
   - `ADMIN_TELEGRAM_IDS`
   - `SERVER_BASE_URL`
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run locally:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 10000
```

## Render Deployment

1. Create a new Render Web Service.
2. Build command:

```bash
pip install -r requirements.txt
```

3. Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 10000
```

4. Add the required values directly in `app/config.py` (Render uses your repo).

## Set Telegram Webhook

Replace placeholders and run:

```
https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=https://<RENDER_DOMAIN>/telegram/webhook/<SECRET>
```

Example:

```
https://api.telegram.org/bot123:ABC/setWebhook?url=https://my-app.onrender.com/telegram/webhook/CHANGE_ME_WEBHOOK_SECRET
```

## Admin Panel

- Login: `/admin/login`
- Send code using your Telegram numeric ID
- Verify the OTP to open dashboard

## Notes

- No `.env` or environment variables used.
- Uses only `CREATE TABLE IF NOT EXISTS` for schema.
- Sessions and OTP are hashed (SHA256 + secret).

