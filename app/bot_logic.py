from __future__ import annotations

import random
from typing import Any

from app import db
from app import telegram_api

SESSIONS: dict[int, dict[str, Any]] = {}


def build_inline_keyboard(buttons: list[tuple[str, str]], row_size: int = 2) -> dict:
    keyboard: list[list[dict]] = []
    row: list[dict] = []
    for text, data in buttons:
        row.append({"text": text, "callback_data": data})
        if len(row) == row_size:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return {"inline_keyboard": keyboard}


async def handle_message(message: dict[str, Any]) -> None:
    text = message.get("text", "")
    chat = message.get("chat", {})
    chat_id = int(chat.get("id"))

    if text.startswith("/start"):
        keyboard = build_inline_keyboard(
            [("Start Practice", "start"), ("My ID", "myid")],
            row_size=2,
        )
        await telegram_api.send_message(chat_id, "Welcome! Choose an option:", keyboard)
    elif text.startswith("/myid"):
        await telegram_api.send_message(chat_id, f"Your Telegram ID: {chat_id}")


async def handle_callback(callback: dict[str, Any]) -> None:
    data = callback.get("data", "")
    message = callback.get("message", {})
    chat = message.get("chat", {})
    chat_id = int(chat.get("id"))
    message_id = int(message.get("message_id"))

    if data == "start":
        topics = db.exec_read(
            "SELECT DISTINCT topic FROM questions WHERE is_active = 1 AND topic IS NOT NULL"
        )
        buttons = [("All", "topic:__all__")]
        for (topic,) in topics:
            if topic:
                buttons.append((topic, f"topic:{topic}"))
        keyboard = build_inline_keyboard(buttons, row_size=2)
        await telegram_api.edit_message(chat_id, message_id, "Select a topic:", keyboard)
        return

    if data == "myid":
        await telegram_api.send_message(chat_id, f"Your Telegram ID: {chat_id}")
        return

    if data.startswith("topic:"):
        topic = data.split(":", 1)[1]
        SESSIONS[chat_id] = {"topic": topic, "qids": [], "idx": 0, "score": 0}
        keyboard = build_inline_keyboard(
            [("5", "count:5"), ("10", "count:10"), ("20", "count:20")],
            row_size=3,
        )
        await telegram_api.edit_message(chat_id, message_id, "How many questions?", keyboard)
        return

    if data.startswith("count:"):
        count = int(data.split(":", 1)[1])
        topic = SESSIONS.get(chat_id, {}).get("topic")
        params: tuple[Any, ...]
        if topic and topic != "__all__":
            query = "SELECT id FROM questions WHERE is_active = 1 AND topic = ?"
            params = (topic,)
        else:
            query = "SELECT id FROM questions WHERE is_active = 1"
            params = ()
        rows = db.exec_read(query, params)
        ids = [row[0] for row in rows]
        random.shuffle(ids)
        qids = ids[:count]
        SESSIONS[chat_id] = {"topic": topic, "qids": qids, "idx": 0, "score": 0}
        await send_question(chat_id, message_id)
        return

    if data.startswith("ans:"):
        choice = data.split(":", 1)[1]
        session = SESSIONS.get(chat_id)
        if not session:
            await telegram_api.send_message(chat_id, "Session expired. Send /start to begin again.")
            return
        qid = session["qids"][session["idx"]]
        row = db.exec_read(
            "SELECT question, a, b, c, d, correct, explanation FROM questions WHERE id = ?",
            (qid,),
        )
        if not row:
            await telegram_api.send_message(chat_id, "Question missing. Send /start again.")
            return
        _, _, _, _, _, correct, explanation = row[0]
        correct = str(correct).upper()
        text = "✅ Correct!" if choice.upper() == correct else f"❌ Wrong. Correct: {correct}"
        if explanation:
            text += f"\n\nExplanation: {explanation}"
        keyboard = build_inline_keyboard([("Next", "next")], row_size=1)
        await telegram_api.edit_message(chat_id, message_id, text, keyboard)
        if choice.upper() == correct:
            session["score"] += 1
        return

    if data == "next":
        session = SESSIONS.get(chat_id)
        if not session:
            await telegram_api.send_message(chat_id, "Session expired. Send /start to begin again.")
            return
        session["idx"] += 1
        if session["idx"] >= len(session["qids"]):
            score = session["score"]
            total = len(session["qids"])
            await telegram_api.edit_message(
                chat_id,
                message_id,
                f"Quiz done! Score: {score}/{total}",
                None,
            )
            SESSIONS.pop(chat_id, None)
        else:
            await send_question(chat_id, message_id)
        return


async def send_question(chat_id: int, message_id: int | None = None) -> None:
    session = SESSIONS.get(chat_id)
    if not session or not session.get("qids"):
        await telegram_api.send_message(chat_id, "No questions available. Ask admin to add.")
        return
    qid = session["qids"][session["idx"]]
    row = db.exec_read(
        "SELECT question, a, b, c, d FROM questions WHERE id = ?",
        (qid,),
    )
    if not row:
        await telegram_api.send_message(chat_id, "Question missing. Send /start again.")
        return
    question, a, b, c, d = row[0]
    text = f"{question}\n\nA) {a}\nB) {b}\nC) {c}\nD) {d}"
    keyboard = build_inline_keyboard(
        [("A", "ans:A"), ("B", "ans:B"), ("C", "ans:C"), ("D", "ans:D")],
        row_size=2,
    )
    if message_id is None:
        await telegram_api.send_message(chat_id, text, keyboard)
    else:
        await telegram_api.edit_message(chat_id, message_id, text, keyboard)

