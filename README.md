# MCQ Practice Telegram Bot + Admin Panel

A production-ready FastAPI app that serves:
- Telegram MCQ practice bot (webhook-based, aiogram v3)
- Admin website (OTP login via Telegram)

> ⚠️ **Security warning:** Never commit real bot tokens, webhook secrets, or OTP/session secrets to a public repository. Edit `app/config.py` with your real values locally only.

## Features
- FastAPI app serving both admin site and Telegram webhook
- Webhook secret validation
- Admin OTP login via Telegram message (6-digit, expires in 2 minutes)
- Session cookies (HttpOnly) stored as hashes
- CRUD for Subjects, Categories, Chapters, Questions
- MCQ practice flow with inline buttons
- PostgreSQL + SQLAlchemy 2.0 (async) + Alembic migrations

## Project Structure
```
app/
  auth.py
  config.py
  db.py
  main.py
  models.py
  routes_admin.py
  routes_api.py
  telegram_bot.py
  templates/
    base.html
    login.html
    dashboard.html
    subjects_new.html
    categories_new.html
    chapters_new.html
    questions_new.html
    questions_list.html
alembic/
  env.py
  versions/
    0001_initial.py
alembic.ini
requirements.txt
README.md
```

## Configuration (No .env, No env vars)
All configuration is centralized in `app/config.py`. Update these fields:
- `base_url`: Your Render HTTPS URL (e.g. `https://your-service.onrender.com`)
- `webhook_secret`: Secret path segment
- `bot_token`: Telegram bot token
- `admin_telegram_ids`: Allowlist of admin Telegram numeric IDs
- `otp_secret` and `session_secret`: random strings
- `database_url`: Render PostgreSQL URL

## Local Development
1. Create and activate a virtual environment
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run migrations:
   ```bash
   alembic upgrade head
   ```
4. Start the server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
5. Set webhook (auto on startup) or via admin endpoint after login:
   ```bash
   curl -X POST http://localhost:8000/api/telegram/set-webhook
   ```

## Render Deployment
1. Create a **PostgreSQL** database in Render.
2. Create a **Web Service** for this repo.
3. Use build/start commands:
   - Build command:
     ```bash
     pip install -r requirements.txt && alembic upgrade head
     ```
   - Start command:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port 10000
     ```
4. Update `app/config.py` with your Render database URL, bot token, webhook secret, and base URL.
5. Ensure the service is always-on (webhook requires reliable HTTPS).
6. The app auto-calls `setWebhook` on startup. If needed, login to `/admin` and trigger the admin endpoint:
   ```bash
   POST /api/telegram/set-webhook
   ```

## Admin Login Flow (Telegram OTP)
1. Open `/admin/login`.
2. Enter your Telegram numeric ID.
3. The app sends a 6-digit OTP via bot message.
4. Enter the OTP to log in.
5. A session cookie is set for 7 days.

Constraints:
- OTP expires in 2 minutes
- Max attempts: 5
- Resend cooldown: 45 seconds
- Only Telegram IDs in `ADMIN_TELEGRAM_IDS` are allowed

## Telegram Bot Commands
- `/start`: Start practice and select subject/category/chapter
- `/myid`: Returns your Telegram numeric ID

## Webhook Checklist
- ✅ HTTPS URL configured in `base_url`
- ✅ Secret path validated in `/telegram/webhook/{secret}`
- ✅ Telegram update parsing via aiogram `Update`
- ✅ FastAPI responds quickly (async task)

## Troubleshooting
- If webhook doesn’t trigger, confirm Render URL + secret path.
- Ensure bot token is correct.
- Ensure `base_url` uses **https**.
- Verify Render service is not sleeping.

## Seed Data
Use the admin panel to create your first Subject:
- Visit `/admin/subjects/new` after login.
