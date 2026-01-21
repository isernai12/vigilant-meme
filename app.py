import json
import os
from datetime import datetime
from pathlib import Path

import requests
from flask import Flask, abort, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MCQ_PATH = DATA_DIR / "mcqs.json"
STATE_PATH = DATA_DIR / "state.json"
CONFIG_PATH = BASE_DIR / "config.json"

app = Flask(__name__)


def load_config():
    if not CONFIG_PATH.exists():
        return {}
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def load_mcqs():
    if not MCQ_PATH.exists():
        return []
    return json.loads(MCQ_PATH.read_text(encoding="utf-8"))


def save_mcqs(mcqs):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MCQ_PATH.write_text(
        json.dumps(mcqs, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_state():
    if not STATE_PATH.exists():
        return {}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def send_telegram_message(chat_id, text):
    config = load_config()
    token = config.get("telegram_bot_token")
    if not token:
        raise RuntimeError("telegram_bot_token missing in config.json")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()


def format_question(mcq):
    options = "\n".join(
        f"{index + 1}. {option}" for index, option in enumerate(mcq["options"])
    )
    return f"{mcq['question']}\n\n{options}\n\nউত্তর দিতে অপশন নম্বর পাঠান (1-4)।"


def get_next_index(state, chat_id, mcq_count):
    current = state.get(str(chat_id), 0)
    next_index = current + 1
    if next_index >= mcq_count:
        return 0
    return next_index


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}
    message = update.get("message") or {}
    text = (message.get("text") or "").strip()
    chat = message.get("chat") or {}
    chat_id = chat.get("id")

    if not chat_id:
        return {"status": "ignored"}, 200

    mcqs = load_mcqs()
    if not mcqs:
        send_telegram_message(chat_id, "এখনো কোন MCQ যোগ করা হয়নি।")
        return {"status": "no_mcq"}, 200

    state = load_state()
    current_index = state.get(str(chat_id), 0)

    if text.lower() in {"/start", "start"}:
        state[str(chat_id)] = 0
        save_state(state)
        send_telegram_message(chat_id, format_question(mcqs[0]))
        return {"status": "started"}, 200

    if text.lower() in {"/next", "next"}:
        next_index = get_next_index(state, chat_id, len(mcqs))
        state[str(chat_id)] = next_index
        save_state(state)
        send_telegram_message(chat_id, format_question(mcqs[next_index]))
        return {"status": "next"}, 200

    if text.isdigit():
        answer = int(text)
        current_mcq = mcqs[current_index]
        correct_index = current_mcq["answer"]
        if answer == correct_index:
            reply = "সঠিক উত্তর! ✅"
        else:
            correct_option = current_mcq["options"][correct_index - 1]
            reply = f"ভুল উত্তর। সঠিক উত্তর: {correct_index}. {correct_option}"
        send_telegram_message(chat_id, reply)

        next_index = get_next_index(state, chat_id, len(mcqs))
        state[str(chat_id)] = next_index
        save_state(state)
        send_telegram_message(chat_id, format_question(mcqs[next_index]))
        return {"status": "answered"}, 200

    send_telegram_message(
        chat_id,
        "দয়া করে 1-4 এর মধ্যে অপশন নম্বর দিন অথবা /next লিখুন।",
    )
    return {"status": "unknown"}, 200


@app.route("/admin", methods=["GET", "POST"])
def admin():
    config = load_config()
    admin_key = config.get("admin_key")
    request_key = request.args.get("key")
    if admin_key and request_key != admin_key:
        abort(403)

    mcqs = load_mcqs()

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        options = [
            request.form.get("option1", "").strip(),
            request.form.get("option2", "").strip(),
            request.form.get("option3", "").strip(),
            request.form.get("option4", "").strip(),
        ]
        answer = request.form.get("answer", "").strip()
        if not question or any(not option for option in options) or not answer:
            return render_template(
                "admin.html",
                mcqs=mcqs,
                error="সব ফিল্ড পূরণ করতে হবে।",
                admin_key=request_key,
            )
        if not answer.isdigit() or int(answer) not in range(1, 5):
            return render_template(
                "admin.html",
                mcqs=mcqs,
                error="উত্তর 1-4 এর মধ্যে হতে হবে।",
                admin_key=request_key,
            )

        mcq_id = max([mcq["id"] for mcq in mcqs], default=0) + 1
        mcqs.append(
            {
                "id": mcq_id,
                "question": question,
                "options": options,
                "answer": int(answer),
                "created_at": datetime.utcnow().isoformat() + "Z",
            }
        )
        save_mcqs(mcqs)
        return redirect(url_for("admin", key=request_key))

    return render_template("admin.html", mcqs=mcqs, admin_key=request_key)


@app.route("/")
def healthcheck():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
