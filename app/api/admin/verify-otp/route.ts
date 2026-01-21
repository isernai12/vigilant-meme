import { NextRequest, NextResponse } from "next/server";
import { config } from "../../../../src/config";
import { createSession, hashWithSecret } from "../../../../src/lib/auth";
import { getPrismaClient } from "../../../../src/lib/db";

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => null) as { telegramId?: string; code?: string } | null;
  const telegramId = body?.telegramId?.trim();
  const code = body?.code?.trim();

  if (!telegramId || !code) {
    return NextResponse.json({ error: "Telegram ID and code required." }, { status: 400 });
  }

  if (!config.ADMIN_TELEGRAM_IDS.includes(telegramId)) {
    return NextResponse.json({ error: "Not authorized." }, { status: 403 });
  }

  const prisma = getPrismaClient();
  const latestOtp = await prisma.adminOtp.findFirst({
    where: { telegramId },
    orderBy: { createdAt: "desc" }
  });

  if (!latestOtp) {
    return NextResponse.json({ error: "No OTP found." }, { status: 404 });
  }

  if (latestOtp.expiresAt < new Date()) {
    return NextResponse.json({ error: "OTP expired." }, { status: 400 });
  }

  if (latestOtp.attempts >= config.OTP_MAX_ATTEMPTS) {
    return NextResponse.json({ error: "Too many attempts." }, { status: 429 });
  }

  const codeHash = hashWithSecret(code, config.OTP_SECRET);
  if (codeHash !== latestOtp.codeHash) {
    await prisma.adminOtp.update({
      where: { id: latestOtp.id },
      data: { attempts: { increment: 1 } }
    });
    return NextResponse.json({ error: "Invalid code." }, { status: 401 });
  }

  const token = await createSession(telegramId);
  const response = NextResponse.json({ ok: true });
  response.cookies.set(config.SESSION_COOKIE_NAME, token, {
    httpOnly: true,
    sameSite: "lax",
    secure: false,
    path: "/",
    maxAge: config.SESSION_TTL_MINUTES * 60
  });
  return response;
}
