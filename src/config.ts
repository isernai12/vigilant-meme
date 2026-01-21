export const config = {
  DATABASE_URL:
    "postgresql://neko_cvdh_user:LRagi69HR0UdQWmXHO5TijgMfF1Sp0Ze@dpg-d5o6t0fgi27c73egfg1g-a.oregon-postgres.render.com/neko_cvdh",
  BOT_TOKEN: "8433875791:AAFs1T4u_8BOXXwpmVW32j09ny97pR2WziQ",
  ADMIN_TELEGRAM_IDS: ["7159848525"],
  OTP_SECRET: "otp-secret-change-me",
  SESSION_SECRET: "session-secret-change-me",
  SESSION_COOKIE_NAME: "admin_session",
  SESSION_TTL_MINUTES: 60 * 12,
  OTP_TTL_MINUTES: 2,
  OTP_MAX_ATTEMPTS: 5,
  OTP_RESEND_COOLDOWN_SECONDS: 45,
  BOT_POLL_INTERVAL_MS: 4000
};
