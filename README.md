# vigilant-meme

Simple Telegram MCQ bot with webhook + admin panel (no database).

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Update `config.json`:
   - `telegram_bot_token`: your bot token from BotFather
   - `admin_key`: a secret key for the admin page

3. Run the app:

```bash
python app.py
```

## Webhook

Point your Telegram webhook to:

```
https://<your-render-app>.onrender.com/webhook
```

## Admin Panel

Open:

```
https://<your-render-app>.onrender.com/admin?key=YOUR_ADMIN_KEY
```

Use the form to add new MCQs. All questions are stored in `data/mcqs.json`.

## Local Testing

- `GET /` returns a healthcheck JSON.
- Post a Telegram update JSON to `/webhook` to simulate webhook.

## Data Files

- `data/mcqs.json`: MCQs stored as JSON.
- `data/state.json`: user progress stored as JSON.
