import { NextRequest, NextResponse } from "next/server";
import { validateSessionToken } from "../../../../src/lib/auth";
import { config } from "../../../../src/config";
import { getPrismaClient } from "../../../../src/lib/db";
import { validateImportPayload } from "../../../../src/lib/validation";

export async function POST(request: NextRequest) {
  const token = request.cookies.get(config.SESSION_COOKIE_NAME)?.value ?? null;
  const session = await validateSessionToken(token);
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const payload = await request.json().catch(() => null);
  if (!validateImportPayload(payload)) {
    return NextResponse.json({ error: "Invalid payload" }, { status: 400 });
  }

  const prisma = getPrismaClient();
  const subjectName = payload.subject?.trim() || "General";
  const categoryName = payload.category?.trim() || null;
  const chapterName = payload.chapter?.trim() || null;

  const subject = await prisma.subject.upsert({
    where: { name: subjectName },
    update: {},
    create: { name: subjectName }
  });

  let category = null;
  if (categoryName) {
    category = await prisma.category.upsert({
      where: {
        name_subjectId: {
          name: categoryName,
          subjectId: subject.id
        }
      },
      update: {},
      create: {
        name: categoryName,
        subjectId: subject.id
      }
    });
  }

  let chapter = null;
  if (chapterName && category) {
    chapter = await prisma.chapter.upsert({
      where: {
        name_categoryId: {
          name: chapterName,
          categoryId: category.id
        }
      },
      update: {},
      create: {
        name: chapterName,
        categoryId: category.id
      }
    });
  }

  const created = await prisma.$transaction(
    payload.questions.map((question) =>
      prisma.question.create({
        data: {
          text: question.text,
          optionA: question.options.A,
          optionB: question.options.B,
          optionC: question.options.C,
          optionD: question.options.D,
          correct: question.correct,
          subjectId: subject.id,
          categoryId: category?.id ?? null,
          chapterId: chapter?.id ?? null
        }
      })
    )
  );

  return NextResponse.json({ ok: true, count: created.length });
}
