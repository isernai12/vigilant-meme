from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    Update,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import AsyncSessionLocal
from app.models import Category, Chapter, Question, Subject


bot = Bot(token=settings.bot_token)
router = Router()

dp = Dispatcher()

dp.include_router(router)


@dataclass
class QuizSession:
    subject_id: int
    category_id: int | None = None
    chapter_id: int | None = None
    question_ids: list[int] = field(default_factory=list)
    current_index: int = 0
    correct_count: int = 0


quiz_sessions: dict[int, QuizSession] = {}


async def fetch_subjects(session: AsyncSession) -> list[Subject]:
    result = await session.execute(select(Subject).order_by(Subject.name))
    return result.scalars().all()


async def fetch_categories(session: AsyncSession, subject_id: int) -> list[Category]:
    result = await session.execute(
        select(Category).where(Category.subject_id == subject_id).order_by(Category.name)
    )
    return result.scalars().all()


async def fetch_chapters(session: AsyncSession, category_id: int) -> list[Chapter]:
    result = await session.execute(
        select(Chapter).where(Chapter.category_id == category_id).order_by(Chapter.name)
    )
    return result.scalars().all()


async def fetch_questions(
    session: AsyncSession,
    subject_id: int,
    category_id: int | None,
    chapter_id: int | None,
    limit: int,
) -> list[Question]:
    query = select(Question).where(Question.is_active.is_(True))
    query = query.where(Question.subject_id == subject_id)
    if category_id:
        query = query.where(Question.category_id == category_id)
    if chapter_id:
        query = query.where(Question.chapter_id == chapter_id)
    query = query.order_by(func.random()).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()


def build_keyboard(items: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=label, callback_data=data)] for label, data in items]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_answer_keyboard() -> InlineKeyboardMarkup:
    options = [("A", "answer:A"), ("B", "answer:B"), ("C", "answer:C"), ("D", "answer:D")]
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=label, callback_data=data) for label, data in options]]
    )


async def send_question(message: Message, session_state: QuizSession) -> None:
    async with AsyncSessionLocal() as db_session:
        question = await db_session.get(Question, session_state.question_ids[session_state.current_index])
    if not question:
        await message.answer("No question found.")
        return
    text = (
        f"Q{session_state.current_index + 1}: {question.text}\n\n"
        f"A. {question.option_a}\n"
        f"B. {question.option_b}\n"
        f"C. {question.option_c}\n"
        f"D. {question.option_d}"
    )
    await message.answer(text, reply_markup=build_answer_keyboard())


async def send_next_question(callback: CallbackQuery, session_state: QuizSession) -> None:
    session_state.current_index += 1
    if session_state.current_index >= len(session_state.question_ids):
        await callback.message.answer(
            f"Quiz complete! Score: {session_state.correct_count}/{len(session_state.question_ids)}"
        )
        quiz_sessions.pop(callback.from_user.id, None)
        return
    await send_question(callback.message, session_state)


@router.message(Command("start"))
async def start_command(message: Message) -> None:
    await message.answer("Welcome! Use the buttons below to start practice.")
    async with AsyncSessionLocal() as db_session:
        subjects = await fetch_subjects(db_session)
    if not subjects:
        await message.answer("No subjects available yet. Please check back later.")
        return
    items = [(subject.name, f"subject:{subject.id}") for subject in subjects]
    await message.answer("Choose a subject:", reply_markup=build_keyboard(items))


@router.message(Command("myid"))
async def my_id(message: Message) -> None:
    await message.answer(f"Your Telegram ID is: {message.from_user.id}")


@router.callback_query(lambda c: c.data and c.data.startswith("subject:"))
async def select_subject(callback: CallbackQuery) -> None:
    subject_id = int(callback.data.split(":")[1])
    quiz_sessions[callback.from_user.id] = QuizSession(subject_id=subject_id)
    async with AsyncSessionLocal() as db_session:
        categories = await fetch_categories(db_session, subject_id)
    if not categories:
        await callback.message.answer("No categories found. Skipping to questions.")
        await ask_question_count(callback)
        return
    items = [(category.name, f"category:{category.id}") for category in categories]
    items.append(("Skip", "category:skip"))
    await callback.message.answer("Choose a category (optional):", reply_markup=build_keyboard(items))


@router.callback_query(lambda c: c.data and c.data.startswith("category:"))
async def select_category(callback: CallbackQuery) -> None:
    session_state = quiz_sessions.get(callback.from_user.id)
    if not session_state:
        await callback.message.answer("Please start again with /start")
        return
    payload = callback.data.split(":")[1]
    if payload != "skip":
        session_state.category_id = int(payload)
        async with AsyncSessionLocal() as db_session:
            chapters = await fetch_chapters(db_session, session_state.category_id)
        if chapters:
            items = [(chapter.name, f"chapter:{chapter.id}") for chapter in chapters]
            items.append(("Skip", "chapter:skip"))
            await callback.message.answer("Choose a chapter (optional):", reply_markup=build_keyboard(items))
            return
    await ask_question_count(callback)


@router.callback_query(lambda c: c.data and c.data.startswith("chapter:"))
async def select_chapter(callback: CallbackQuery) -> None:
    session_state = quiz_sessions.get(callback.from_user.id)
    if not session_state:
        await callback.message.answer("Please start again with /start")
        return
    payload = callback.data.split(":")[1]
    if payload != "skip":
        session_state.chapter_id = int(payload)
    await ask_question_count(callback)


async def ask_question_count(callback: CallbackQuery) -> None:
    items = [("5", "count:5"), ("10", "count:10"), ("20", "count:20")]
    await callback.message.answer("How many questions?", reply_markup=build_keyboard(items))


@router.callback_query(lambda c: c.data and c.data.startswith("count:"))
async def select_count(callback: CallbackQuery) -> None:
    session_state = quiz_sessions.get(callback.from_user.id)
    if not session_state:
        await callback.message.answer("Please start again with /start")
        return
    count = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as db_session:
        questions = await fetch_questions(
            db_session,
            session_state.subject_id,
            session_state.category_id,
            session_state.chapter_id,
            count,
        )
    if not questions:
        await callback.message.answer("No questions found for that selection.")
        quiz_sessions.pop(callback.from_user.id, None)
        return
    session_state.question_ids = [q.id for q in questions]
    session_state.current_index = 0
    session_state.correct_count = 0
    await send_question(callback.message, session_state)


@router.callback_query(lambda c: c.data and c.data.startswith("answer:"))
async def answer_question(callback: CallbackQuery) -> None:
    session_state = quiz_sessions.get(callback.from_user.id)
    if not session_state:
        await callback.message.answer("Please start again with /start")
        return
    answer = callback.data.split(":")[1]
    async with AsyncSessionLocal() as db_session:
        question = await db_session.get(Question, session_state.question_ids[session_state.current_index])
    if not question:
        await callback.message.answer("Question not found.")
        return
    correct = question.correct.upper()
    if answer == correct:
        session_state.correct_count += 1
        result_text = "✅ Correct!"
    else:
        result_text = f"❌ Incorrect. Correct answer: {correct}"
    explanation = f"\n\nExplanation: {question.explanation}" if question.explanation else ""
    await callback.message.answer(f"{result_text}{explanation}")
    await callback.message.answer("Next question?", reply_markup=build_keyboard([("Next", "next")]))


@router.callback_query(lambda c: c.data == "next")
async def next_question(callback: CallbackQuery) -> None:
    session_state = quiz_sessions.get(callback.from_user.id)
    if not session_state:
        await callback.message.answer("Please start again with /start")
        return
    await send_next_question(callback, session_state)


async def set_webhook() -> None:
    webhook_url = f"{settings.base_url}/telegram/webhook/{settings.webhook_secret}"
    await bot.set_webhook(url=webhook_url, drop_pending_updates=True)


async def handle_update(update_data: dict[str, Any]) -> None:
    update = Update.model_validate(update_data)
    await dp.feed_update(bot, update)
