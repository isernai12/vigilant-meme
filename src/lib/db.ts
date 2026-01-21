import { PrismaClient } from "@prisma/client";
import { config } from "../config";

let prisma: PrismaClient | null = null;

export function getPrismaClient(): PrismaClient {
  if (!prisma) {
    prisma = new PrismaClient({
      datasourceUrl: config.DATABASE_URL
    });
  }
  return prisma;
}
