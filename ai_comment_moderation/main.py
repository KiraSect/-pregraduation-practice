import os
import json
import sqlite3

from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from pydantic import BaseModel

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

DB_PATH = "moderation.db"

ALLOWED_LABELS = [
    "ok",
    "spam",
    "toxic",
    "needs_review"
]

SYSTEM_PROMPT = """
Ты система AI-модерации комментариев.

Тебе нужно классифицировать комментарий
по одной из категорий:

- ok
- spam
- toxic
- needs_review

Описание категорий:

ok:
нормальный комментарий без нарушений.

spam:
реклама, мошенничество, массовые ссылки,
нерелевантный текст.

toxic:
оскорбления, агрессия, угрозы,
разжигание ненависти.

needs_review:
сомнительный или неоднозначный случай,
который должен проверить модератор.

Верни только JSON:

{
  "label": "...",
  "reason": "краткое объяснение"
}
"""

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

def init_db():

    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS moderation_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comment TEXT NOT NULL,
            label TEXT NOT NULL,
            reason TEXT,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def log_decision(
    comment: str,
    label: str,
    reason: str
):

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        INSERT INTO moderation_log (
            comment,
            label,
            reason,
            created_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            comment,
            label,
            reason,
            datetime.now().isoformat()
        )
    )

    conn.commit()
    conn.close()


def get_history(limit: int = 50):

    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        SELECT *
        FROM moderation_log
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,)
    ).fetchall()

    conn.close()

    return [dict(r) for r in rows]

def classify_comment(comment: str) -> dict:

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": comment
            }
        ],
        temperature=0.1,
        response_format={
            "type": "json_object"
        }
    )

    result = json.loads(
        response.choices[0].message.content
    )

    if result.get("label") not in ALLOWED_LABELS:

        return {
            "label": "needs_review",
            "reason": "получена неизвестная категория"
        }

    return result


@asynccontextmanager
async def lifespan(app: FastAPI):

    init_db()

    yield


app = FastAPI(
    title="AI Comment Moderation API",
    lifespan=lifespan
)



class CommentRequest(BaseModel):
    text: str


class ModerationResponse(BaseModel):
    label: str
    reason: str


@app.post(
    "/moderate",
    response_model=ModerationResponse
)
def moderate(request: CommentRequest):

    if not GROQ_API_KEY:

        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY не настроен"
        )

    text = request.text.strip()

    if not text:

        raise HTTPException(
            status_code=400,
            detail="Комментарий пустой"
        )

    if len(text) > 5000:

        raise HTTPException(
            status_code=400,
            detail="Комментарий слишком длинный"
        )

    try:

        result = classify_comment(text)

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Ошибка обработки: {e}"
        )

    log_decision(
        text,
        result["label"],
        result["reason"]
    )

    return ModerationResponse(
        label=result["label"],
        reason=result["reason"]
    )


@app.get("/history")
def history(limit: int = 50):

    return get_history(limit)


@app.get("/", response_class=HTMLResponse)
def index():

    return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>AI Comment Moderation</title>

    <style>
        body {
            font-family: sans-serif;
            max-width: 760px;
            margin: 40px auto;
            padding: 20px;
        }

        textarea {
            width: 100%;
            height: 120px;
            font-size: 14px;
            padding: 10px;
        }

        button {
            padding: 10px 20px;
            margin-top: 12px;
            cursor: pointer;
        }

        .result {
            margin-top: 20px;
            padding: 14px;
            border-radius: 8px;
        }

        .label-ok {
            background: #d4edda;
        }

        .label-spam {
            background: #fff3cd;
        }

        .label-toxic {
            background: #f8d7da;
        }

        .label-needs_review {
            background: #e2e3e5;
        }

        .history {
            margin-top: 32px;
        }

        .history-item {
            padding: 10px;
            border-bottom: 1px solid #ddd;
            font-size: 14px;
        }
    </style>
</head>

<body>

<h1>AI Comment Moderation</h1>

<p>
Проверка комментариев через LLM API.
</p>

<textarea
    id="text"
    placeholder="Введите комментарий..."
></textarea>

<br>

<button onclick="moderate()">
    Проверить комментарий
</button>

<button onclick="loadHistory()">
    Загрузить историю
</button>

<div id="result"></div>

<div id="history" class="history"></div>

<script>

async function moderate() {

    const text = document.getElementById('text').value;

    const response = await fetch('/moderate', {

        method: 'POST',

        headers: {
            'Content-Type': 'application/json'
        },

        body: JSON.stringify({
            text
        })
    });

    const data = await response.json();

    const div = document.getElementById('result');

    if (data.label) {

        div.className =
            'result label-' + data.label;

        div.innerHTML =
            '<b>' +
            data.label.toUpperCase() +
            '</b><br>' +
            data.reason;

    } else {

        div.innerHTML =
            'Ошибка: ' +
            JSON.stringify(data);
    }
}

async function loadHistory() {

    const response =
        await fetch('/history?limit=20');

    const data =
        await response.json();

    const div =
        document.getElementById('history');

    div.innerHTML =
        '<h3>Последние решения</h3>' +

        data.map(item =>

            `<div class="history-item label-${item.label}">
                <b>${item.label}</b>
                |
                ${item.created_at.substring(0, 19)}

                <br><br>

                "${item.comment.substring(0, 120)}"

                <br>

                <i>${item.reason}</i>
            </div>`

        ).join('');
}

</script>

</body>
</html>
"""