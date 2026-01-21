import { NextRequest, NextResponse } from "next/server";
import { config } from "../../../../src/config";
import { getPrismaClient } from "../../../../src/lib/db";
import { generateOtpCode, hashWithSecret } from "../../../../src/lib/auth";

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => null) as { telegramId?: string } | null;
  const telegramId = body?.telegramId?.trim();

  if (!telegramId || !/^[0-9]+$/.test(telegramId)) {
    return NextResponse.json({ error: "Valid Telegram ID required." }, { status: 400 });
  }

  if (!config.ADMIN_TELEGRAM_IDS.includes(telegramId)) {
    return NextResponse.json({ error: "Not authorized." }, { status: 403 });
  }

  const prisma = getPrismaClient();
  const latestOtp = await prisma.adminOtp.findFirst({
    where: { telegramId },
    orderBy: { createdAt: "desc" }
  });

  if (latestOtp) {
    const cooldownMs = config.OTP_RESEND_COOLDOWN_SECONDS * 1000;
    const nextAllowed = latestOtp.lastSentAt.getTime() + cooldownMs;
    if (Date.now() < nextAllowed) {
      return NextResponse.json(
        { error: "Please wait before requesting another code." },
        { status: 429 }
      );
    }
  }

  const otp = generateOtpCode();
  const codeHash = hashWithSecret(otp, config.OTP_SECRET);
  const expiresAt = new Date(Date.now() + config.OTP_TTL_MINUTES * 60 * 1000);

  await prisma.adminOtp.create({
    data: {
      telegramId,
      codeHash,
      expiresAt,
      attempts: 0,
      lastSentAt: new Date()
    }
  });

  await prisma.messageOutbox.create({
    data: {
      telegramId,
      message: `Your admin login code is: ${otp} (expires in ${config.OTP_TTL_MINUTES} min)`
    }
  });

  return NextResponse.json({ ok: true });
}
