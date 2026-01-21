# Telegram MCQ Practice Bot + Admin Website

This project includes:
- **Next.js (App Router) admin website** with Telegram OTP login
- **Telegraf bot worker** that sends OTPs and runs MCQ practice sessions
- **PostgreSQL (Render) + Prisma ORM**

> **Note:** All configuration is hardcoded in `src/config.ts` (no `.env`).

## Local setup

```bash
npm install
npm run prisma:generate
npm run prisma:migrate
npm run dev
```

In a second terminal for the bot:

```bash
npm run bot
```

## Render deployment

- **Web Service**
  - Build command: `npm install && npm run prisma:generate && npm run build`
  - Start command: `npm run start`
- **Worker Service (bot)**
  - Start command: `npm run bot`

Run `npm run prisma:migrate` either locally or via the Render shell/console.

## API endpoints

- `POST /api/admin/request-otp`
- `POST /api/admin/verify-otp`
- `POST /api/admin/import-json`
- `GET /api/admin/questions`
- `POST /api/admin/questions`
