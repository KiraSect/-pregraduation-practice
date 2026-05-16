import os
import sys
import math
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

SIMILARITY_THRESHOLD = 0.18

STOP_WORDS = {
    "и", "в", "на", "с", "по", "для", "это", "как",
    "a", "the", "and", "to", "of", "in", "for"
}


def load_notes(folder: str) -> list:
    path = Path(folder)

    if not path.exists():
        print(f"папка {folder} не найдена")
        return []

    notes = []

    for file in path.rglob("*.md"):
        try:
            notes.append({
                "name": file.stem,
                "path": str(file),
                "content": file.read_text(encoding="utf-8")
            })
        except Exception as e:
            print(f"ошибка чтения {file.name}: {e}")

    return notes


def make_embedding(text: str) -> list:
    vector = [0.0] * 2048

    for word in re.findall(r"[а-яa-z0-9]+", text.lower()):
        if word in STOP_WORDS or len(word) < 2:
            continue

        vector[hash(word) % len(vector)] += 1

    return vector


def similarity(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))

    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if not norm_a or not norm_b:
        return 0.0

    return dot / (norm_a * norm_b)


def find_links(notes: list) -> list:
    print("анализирую заметки")

    for note in notes:
        note["embedding"] = make_embedding(note["content"])

    pairs = []

    for i in range(len(notes)):
        for j in range(i + 1, len(notes)):
            score = similarity(
                notes[i]["embedding"],
                notes[j]["embedding"]
            )

            if score >= SIMILARITY_THRESHOLD:
                pairs.append({
                    "a": notes[i]["name"],
                    "b": notes[j]["name"],
                    "score": score
                })

    return sorted(pairs, key=lambda x: x["score"], reverse=True)


def generate_summary(text: str) -> str:
    prompt = f"""
сделай краткое summary заметки в одном предложении.

заметка:
{text[:2500]}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=60
    )

    return response.choices[0].message.content.strip()


def insert_summary(path: str, summary: str):
    file = Path(path)
    content = file.read_text(encoding="utf-8")

    if "summary:" in content:
        return

    if content.startswith("---"):
        idx = content.find("---", 3)

        if idx != -1:
            frontmatter = content[:idx]
            rest = content[idx:]

            content = (
                frontmatter.rstrip()
                + f'\nsummary: "{summary}"\n'
                + rest
            )
    else:
        content = f'---\nsummary: "{summary}"\n---\n\n{content}'

    file.write_text(content, encoding="utf-8")
    print(f"summary добавлен: {file.name}")


def main():
    if len(sys.argv) < 2:
        print("использование: python main.py <notes_folder>")
        return

    folder = sys.argv[1]

    notes = load_notes(folder)

    print(f"заметок найдено: {len(notes)}")

    if len(notes) < 2:
        return

    links = find_links(notes)

    print("\nсвязанные заметки:\n")

    if not links:
        print("связи не найдены")

    for link in links[:15]:
        print(f"[{link['score']:.2f}] {link['a']} <-> {link['b']}")

    answer = input("\nдобавить summary? [y/n]: ").lower().strip()

    if answer != "y":
        return

    if not GROQ_API_KEY:
        print("не найден GROQ_API_KEY")
        return

    for note in notes:
        try:
            summary = generate_summary(note["content"])
            print(f"{note['name']}: {summary}")
            insert_summary(note["path"], summary)
        except Exception as e:
            print(f"ошибка для {note['name']}: {e}")
    print("\nготово")


if __name__ == "__main__":
    main()