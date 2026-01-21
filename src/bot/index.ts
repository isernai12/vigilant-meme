import { Telegraf, Markup } from "telegraf";
import { config } from "../config";
import { getPrismaClient } from "../lib/db";

const prisma = getPrismaClient();
const bot = new Telegraf(config.BOT_TOKEN);

type QuizSession = {
  subjectId?: string;
  categoryId?: string | null;
  chapterId?: string | null;
  questions: Array<{
    id: string;
    text: string;
    optionA: string;
    optionB: string;
    optionC: string;
    optionD: string;
    correct: string;
  }>;
  index: number;
  score: number;
  awaitingCustomCount: boolean;
};

const sessions = new Map<number, QuizSession>();

function getSession(userId: number): QuizSession {
  const existing = sessions.get(userId);
  if (existing) {
    return existing;
  }
  const session: QuizSession = {
    questions: [],
    index: 0,
    score: 0,
    awaitingCustomCount: false
  };
  sessions.set(userId, session);
  return session;
}

function resetSession(userId: number) {
  sessions.set(userId, {
    questions: [],
    index: 0,
    score: 0,
    awaitingCustomCount: false
  });
}

async function sendQuestion(ctx: any, userId: number) {
  const session = getSession(userId);
  const question = session.questions[session.index];
  if (!question) {
    await ctx.reply(`Quiz completed! Score: ${session.score}/${session.questions.length}`);
    resetSession(userId);
    return;
  }

  await ctx.reply(
    `Q${session.index + 1}: ${question.text}\n\nA) ${question.optionA}\nB) ${question.optionB}\nC) ${question.optionC}\nD) ${question.optionD}`,
    Markup.inlineKeyboard([
      [
        Markup.button.callback("A", `answer:${question.id}:A`),
        Markup.button.callback("B", `answer:${question.id}:B`),
        Markup.button.callback("C", `answer:${question.id}:C`),
        Markup.button.callback("D", `answer:${question.id}:D`)
      ]
    ])
  );
}

async function promptForCount(ctx: any, userId: number) {
  const session = getSession(userId);
  session.awaitingCustomCount = false;
  await ctx.reply(
    "How many questions?",
    Markup.inlineKeyboard([
      [
        Markup.button.callback("5", "count:5"),
        Markup.button.callback("10", "count:10"),
        Markup.button.callback("20", "count:20")
      ],
      [Markup.button.callback("Custom", "count:custom")]
    ])
  );
}

bot.start(async (ctx) => {
  resetSession(ctx.from.id);
  await ctx.reply(
    "Welcome to the MCQ Practice Bot!",
    Markup.inlineKeyboard([[Markup.button.callback("Practice", "practice")]])
  );
});

bot.command("myid", async (ctx) => {
  await ctx.reply(`Your Telegram ID is ${ctx.from.id}`);
});

bot.action("practice", async (ctx) => {
  resetSession(ctx.from.id);
  const subjects = await prisma.subject.findMany({ orderBy: { name: "asc" } });
  if (subjects.length === 0) {
    await ctx.reply("No subjects found yet. Ask the admin to import questions.");
    return;
  }
  await ctx.reply(
    "Choose a subject:",
    Markup.inlineKeyboard(subjects.map((subject) => [
      Markup.button.callback(subject.name, `subject:${subject.id}`)
    ]))
  );
});

bot.action(/subject:(.+)/, async (ctx) => {
  const subjectId = ctx.match[1];
  const session = getSession(ctx.from.id);
  session.subjectId = subjectId;
  session.categoryId = null;
  session.chapterId = null;

  const categories = await prisma.category.findMany({
    where: { subjectId },
    orderBy: { name: "asc" }
  });

  if (categories.length === 0) {
    await promptForCount(ctx, ctx.from.id);
    return;
  }

  await ctx.reply(
    "Choose a category (or all):",
    Markup.inlineKeyboard([
      [Markup.button.callback("All categories", "category:all")],
      ...categories.map((category) => [Markup.button.callback(category.name, `category:${category.id}`)])
    ])
  );
});

bot.action(/category:(.+)/, async (ctx) => {
  const categoryId = ctx.match[1];
  const session = getSession(ctx.from.id);
  if (categoryId === "all") {
    session.categoryId = null;
    session.chapterId = null;
    await promptForCount(ctx, ctx.from.id);
    return;
  }

  session.categoryId = categoryId;
  const chapters = await prisma.chapter.findMany({
    where: { categoryId },
    orderBy: { name: "asc" }
  });

  if (chapters.length === 0) {
    await promptForCount(ctx, ctx.from.id);
    return;
  }

  await ctx.reply(
    "Choose a chapter (or all):",
    Markup.inlineKeyboard([
      [Markup.button.callback("All chapters", "chapter:all")],
      ...chapters.map((chapter) => [Markup.button.callback(chapter.name, `chapter:${chapter.id}`)])
    ])
  );
});

bot.action(/chapter:(.+)/, async (ctx) => {
  const chapterId = ctx.match[1];
  const session = getSession(ctx.from.id);
  session.chapterId = chapterId === "all" ? null : chapterId;
  await promptForCount(ctx, ctx.from.id);
});

bot.action(/count:(.+)/, async (ctx) => {
  const countRaw = ctx.match[1];
  const session = getSession(ctx.from.id);

  if (countRaw === "custom") {
    session.awaitingCustomCount = true;
    await ctx.reply("Send the number of questions you want (e.g., 7)." );
    return;
  }

  const count = Number(countRaw);
  if (!Number.isFinite(count) || count <= 0) {
    await ctx.reply("Invalid count.");
    return;
  }

  await loadQuestionsAndStart(ctx, count);
});

bot.on("text", async (ctx) => {
  const session = getSession(ctx.from.id);
  if (!session.awaitingCustomCount) {
    return;
  }
  const count = Number(ctx.message.text.trim());
  if (!Number.isFinite(count) || count <= 0 || count > 100) {
    await ctx.reply("Please send a valid number between 1 and 100.");
    return;
  }
  session.awaitingCustomCount = false;
  await loadQuestionsAndStart(ctx, count);
});

async function loadQuestionsAndStart(ctx: any, count: number) {
  const session = getSession(ctx.from.id);
  if (!session.subjectId) {
    await ctx.reply("Please choose a subject first.");
    return;
  }

  const questions = await prisma.question.findMany({
    where: {
      subjectId: session.subjectId,
      categoryId: session.categoryId ?? undefined,
      chapterId: session.chapterId ?? undefined
    },
    orderBy: { createdAt: "desc" },
    take: count
  });

  if (questions.length === 0) {
    await ctx.reply("No questions found for this selection.");
    return;
  }

  session.questions = questions;
  session.index = 0;
  session.score = 0;

  await sendQuestion(ctx, ctx.from.id);
}

bot.action(/answer:(.+):([ABCD])/, async (ctx) => {
  const questionId = ctx.match[1];
  const answer = ctx.match[2];
  const session = getSession(ctx.from.id);
  const question = session.questions[session.index];

  if (!question || question.id !== questionId) {
    await ctx.reply("This question is no longer active.");
    return;
  }

  const isCorrect = question.correct === answer;
  if (isCorrect) {
    session.score += 1;
  }

  await ctx.reply(
    `${isCorrect ? "✅ Correct" : "❌ Incorrect"}. Correct answer: ${question.correct}`,
    Markup.inlineKeyboard([[Markup.button.callback("Next", "next")]])
  );
});

bot.action("next", async (ctx) => {
  const session = getSession(ctx.from.id);
  session.index += 1;
  await sendQuestion(ctx, ctx.from.id);
});

async function pollOutbox() {
  const pending = await prisma.messageOutbox.findMany({
    where: { status: "pending" },
    orderBy: { createdAt: "asc" },
    take: 10
  });

  for (const message of pending) {
    try {
      await bot.telegram.sendMessage(Number(message.telegramId), message.message);
      await prisma.messageOutbox.update({
        where: { id: message.id },
        data: { status: "sent", sentAt: new Date() }
      });
    } catch (error) {
      await prisma.messageOutbox.update({
        where: { id: message.id },
        data: { status: "failed" }
      });
    }
  }
}

setInterval(() => {
  pollOutbox().catch(() => null);
}, config.BOT_POLL_INTERVAL_MS);

bot.launch();

process.once("SIGINT", () => bot.stop("SIGINT"));
process.once("SIGTERM", () => bot.stop("SIGTERM"));
