import { NextRequest, NextResponse } from "next/server";
import { config } from "../../../../src/config";
import { validateSessionToken } from "../../../../src/lib/auth";
import { getPrismaClient } from "../../../../src/lib/db";

function isValidCorrect(value: string): value is "A" | "B" | "C" | "D" {
  return ["A", "B", "C", "D"].includes(value);
}

export async function GET(request: NextRequest) {
  const token = request.cookies.get(config.SESSION_COOKIE_NAME)?.value ?? null;
  const session = await validateSessionToken(token);
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const prisma = getPrismaClient();
  const questions = await prisma.question.findMany({
    orderBy: { createdAt: "desc" },
    take: 50,
    include: {
      subject: true,
      category: true,
      chapter: true
    }
  });
  return NextResponse.json({ questions });
}

export async function POST(request: NextRequest) {
  const token = request.cookies.get(config.SESSION_COOKIE_NAME)?.value ?? null;
  const session = await validateSessionToken(token);
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const body = await request.json().catch(() => null) as
    | {
        subject?: string;
        category?: string | null;
        chapter?: string | null;
        text?: string;
        options?: { A?: string; B?: string; C?: string; D?: string };
        correct?: string;
      }
    | null;

  if (!body?.subject || !body.text || !body.options || !body.correct) {
    return NextResponse.json({ error: "Missing fields" }, { status: 400 });
  }
  if (!isValidCorrect(body.correct)) {
    return NextResponse.json({ error: "Invalid correct answer" }, { status: 400 });
  }
  const { A, B, C, D } = body.options;
  if (![A, B, C, D].every((option) => typeof option === "string" && option.trim() !== "")) {
    return NextResponse.json({ error: "All options required" }, { status: 400 });
  }

  const prisma = getPrismaClient();
  const subject = await prisma.subject.upsert({
    where: { name: body.subject },
    update: {},
    create: { name: body.subject }
  });

  let category = null;
  if (body.category) {
    category = await prisma.category.upsert({
      where: {
        name_subjectId: {
          name: body.category,
          subjectId: subject.id
        }
      },
      update: {},
      create: { name: body.category, subjectId: subject.id }
    });
  }

  let chapter = null;
  if (body.chapter && category) {
    chapter = await prisma.chapter.upsert({
      where: {
        name_categoryId: {
          name: body.chapter,
          categoryId: category.id
        }
      },
      update: {},
      create: { name: body.chapter, categoryId: category.id }
    });
  }

  const question = await prisma.question.create({
    data: {
      text: body.text,
      optionA: A ?? "",
      optionB: B ?? "",
      optionC: C ?? "",
      optionD: D ?? "",
      correct: body.correct,
      subjectId: subject.id,
      categoryId: category?.id ?? null,
      chapterId: chapter?.id ?? null
    }
  });

  return NextResponse.json({ ok: true, question });
}
