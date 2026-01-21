"use client";

import { useState } from "react";

export default function AdminLoginPage() {
  const [telegramId, setTelegramId] = useState("");
  const [code, setCode] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);

  const sendCode = async () => {
    setStatus(null);
    setIsSending(true);
    try {
      const res = await fetch("/api/admin/request-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ telegramId })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "Failed to send code");
      }
      setStatus("OTP sent via Telegram. Check your bot messages.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Unknown error");
    } finally {
      setIsSending(false);
    }
  };

  const verifyCode = async () => {
    setStatus(null);
    setIsVerifying(true);
    try {
      const res = await fetch("/api/admin/verify-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ telegramId, code })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "Failed to verify code");
      }
      window.location.href = "/admin";
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Unknown error");
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <main>
      <div className="card">
        <h1 className="section-title">Admin Login</h1>
        <p>Enter your Telegram numeric ID and request an OTP.</p>
        <form
          onSubmit={(event) => {
            event.preventDefault();
          }}
        >
          <div>
            <label htmlFor="telegramId">Telegram ID</label>
            <input
              id="telegramId"
              placeholder="123456789"
              value={telegramId}
              onChange={(event) => setTelegramId(event.target.value)}
            />
          </div>
          <div className="flex">
            <button type="button" onClick={sendCode} disabled={isSending || !telegramId}>
              {isSending ? "Sending..." : "Send Code"}
            </button>
          </div>
          <div>
            <label htmlFor="code">OTP Code</label>
            <input
              id="code"
              placeholder="6-digit code"
              value={code}
              onChange={(event) => setCode(event.target.value)}
            />
          </div>
          <div className="flex">
            <button
              type="button"
              className="secondary"
              onClick={verifyCode}
              disabled={isVerifying || !telegramId || !code}
            >
              {isVerifying ? "Verifying..." : "Verify Code"}
            </button>
          </div>
          {status && <small>{status}</small>}
        </form>
      </div>
    </main>
  );
}
