from __future__ import annotations

from typing import Iterable


def base_page(title: str, body: str) -> str:
    return f"""
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>{title}</title>
        <style>
          body {{
            margin: 0;
            font-family: system-ui, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
          }}
          .container {{
            max-width: 720px;
            margin: 0 auto;
            padding: 24px;
          }}
          .card {{
            background: #1e293b;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 16px;
          }}
          input, textarea, select {{
            width: 100%;
            padding: 10px;
            margin-top: 6px;
            border-radius: 8px;
            border: 1px solid #334155;
            background: #0f172a;
            color: #e2e8f0;
          }}
          button {{
            padding: 10px 16px;
            border: none;
            border-radius: 8px;
            background: #38bdf8;
            color: #0f172a;
            font-weight: 600;
            cursor: pointer;
          }}
          a {{
            color: #38bdf8;
            text-decoration: none;
          }}
          .row {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
          }}
          .row > div {{
            flex: 1 1 220px;
          }}
        </style>
      </head>
      <body>
        <div class="container">
          {body}
        </div>
      </body>
    </html>
    """


def login_page(message: str | None = None) -> str:
    msg_html = f"<p>{message}</p>" if message else ""
    body = f"""
    <div class="card">
      <h1>Admin Login</h1>
      {msg_html}
      <form method="post" action="/admin/request-otp">
        <label>Telegram Numeric ID</label>
        <input name="telegram_id" type="number" required />
        <button type="submit" style="margin-top: 12px;">Send Code</button>
      </form>
    </div>
    """
    return base_page("Admin Login", body)


def verify_page(telegram_id: int, message: str | None = None) -> str:
    msg_html = f"<p>{message}</p>" if message else ""
    body = f"""
    <div class="card">
      <h1>Verify OTP</h1>
      {msg_html}
      <form method="post" action="/admin/verify-otp">
        <input type="hidden" name="telegram_id" value="{telegram_id}" />
        <label>6 Digit Code</label>
        <input name="code" type="text" minlength="6" maxlength="6" required />
        <button type="submit" style="margin-top: 12px;">Verify</button>
      </form>
    </div>
    """
    return base_page("Verify OTP", body)


def dashboard_page() -> str:
    body = """
    <div class="card">
      <h1>Admin Dashboard</h1>
      <p>Quick actions:</p>
      <div class="row">
        <div><a href="/admin/questions/new">Add Question</a></div>
        <div><a href="/admin/questions">View Questions</a></div>
      </div>
      <form method="post" action="/admin/logout" style="margin-top: 20px;">
        <button type="submit">Logout</button>
      </form>
    </div>
    """
    return base_page("Dashboard", body)


def new_question_page(message: str | None = None) -> str:
    msg_html = f"<p>{message}</p>" if message else ""
    body = f"""
    <div class="card">
      <h1>Add Question</h1>
      {msg_html}
      <form method="post" action="/admin/questions/new">
        <label>Topic (optional)</label>
        <input name="topic" type="text" />
        <label>Question</label>
        <textarea name="question" rows="4" required></textarea>
        <label>Option A</label>
        <input name="a" type="text" required />
        <label>Option B</label>
        <input name="b" type="text" required />
        <label>Option C</label>
        <input name="c" type="text" required />
        <label>Option D</label>
        <input name="d" type="text" required />
        <label>Correct (A/B/C/D)</label>
        <select name="correct" required>
          <option value="A">A</option>
          <option value="B">B</option>
          <option value="C">C</option>
          <option value="D">D</option>
        </select>
        <label>Explanation (optional)</label>
        <textarea name="explanation" rows="3"></textarea>
        <button type="submit" style="margin-top: 12px;">Save</button>
      </form>
    </div>
    """
    return base_page("Add Question", body)


def questions_list_page(rows: Iterable[tuple]) -> str:
    items = ""
    for row in rows:
        question_id, topic, question, correct, created_at = row
        items += f"""
        <div class="card">
          <strong>#{question_id}</strong> ({topic or "General"}) - {correct}<br />
          <div>{question}</div>
          <small>Created: {created_at}</small>
        </div>
        """
    body = f"""
    <div class="card">
      <h1>Latest Questions</h1>
      <p><a href="/admin">Back to dashboard</a></p>
    </div>
    {items if items else '<div class="card">No questions yet.</div>'}
    """
    return base_page("Questions", body)

