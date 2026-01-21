import crypto from "crypto";
import { cookies } from "next/headers";
import { config } from "../config";
import { getPrismaClient } from "./db";

export function hashWithSecret(value: string, secret: string): string {
  return crypto.createHmac("sha256", secret).update(value).digest("hex");
}

export function generateOtpCode(): string {
  return Math.floor(100000 + Math.random() * 900000).toString();
}

export function generateSessionToken(): string {
  return crypto.randomBytes(32).toString("hex");
}

export async function createSession(telegramId: string): Promise<string> {
  const prisma = getPrismaClient();
  const token = generateSessionToken();
  const tokenHash = hashWithSecret(token, config.SESSION_SECRET);
  const expiresAt = new Date(Date.now() + config.SESSION_TTL_MINUTES * 60 * 1000);
  await prisma.adminSession.create({
    data: {
      telegramId,
      tokenHash,
      expiresAt
    }
  });
  return token;
}

export async function validateSession(): Promise<{ telegramId: string } | null> {
  const cookieStore = cookies();
  const token = cookieStore.get(config.SESSION_COOKIE_NAME)?.value;
  return validateSessionToken(token ?? null);
}

export function setSessionCookie(token: string): void {
  const cookieStore = cookies();
  cookieStore.set(config.SESSION_COOKIE_NAME, token, {
    httpOnly: true,
    sameSite: "lax",
    secure: false,
    path: "/",
    maxAge: config.SESSION_TTL_MINUTES * 60
  });
}

export async function validateSessionToken(token: string | null): Promise<{ telegramId: string } | null> {
  if (!token) {
    return null;
  }
  const prisma = getPrismaClient();
  const tokenHash = hashWithSecret(token, config.SESSION_SECRET);
  const session = await prisma.adminSession.findFirst({
    where: {
      tokenHash,
      expiresAt: {
        gt: new Date()
      }
    }
  });
  if (!session) {
    return null;
  }
  return { telegramId: session.telegramId };
}
