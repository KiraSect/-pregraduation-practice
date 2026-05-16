import os
import sys
import re

from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

SUPPORTED_LANGUAGES = {
    "en": "English",
    "ru": "Russian",
    "de": "German",
    "fr": "French",
    "es": "Spanish"
}

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)


def split_markdown(text: str):
    patterns = [
        r'^---\n.*?\n---\n',
        r'```[\s\S]*?```',
        r'<[a-zA-Z][^>]*>[\s\S]*?</[a-zA-Z]+>'
    ]

    spans = []

    for pattern in patterns:
        for match in re.finditer(
            pattern,
            text,
            re.DOTALL | re.MULTILINE
        ):
            spans.append(
                (match.start(), match.end())
            )

    spans.sort()

    blocks = []
    pos = 0

    for start, end in spans:
        if start > pos:
            blocks.append({
                "type": "translate",
                "content": text[pos:start]
            })

        blocks.append({"type": "keep","content": text[start:end]
        })
        pos = end

    if pos < len(text):
        blocks.append({"type": "translate","content": text[pos:]})
    return blocks


def clean_result(text: str):
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[-1].startswith("```"):
            text = "\n".join(lines[1:-1])

    return text.strip()


def translate_text(text: str, target_lang: str):
    lang = SUPPORTED_LANGUAGES[target_lang]

    prompt = f"""
Translate markdown fragment to {lang}.

Rules:
- keep markdown syntax
- keep inline code unchanged
- keep urls unchanged
- return only translated text

Fragment:
{text}
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": ("You translate markdown ""without breaking formatting.")
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1
    )

    return clean_result(
        response.choices[0].message.content
    )


def translate_file(input_file, output_file, target_lang):

    text = Path(input_file).read_text(
        encoding="utf-8"
    )
    blocks = split_markdown(text)
    print(f"Блоков: {len(blocks)}")
    result = []

    for i, block in enumerate(blocks, 1):
        if block["type"] == "keep":
            print(f"[{i}] skip")result.append(block["content"])
            continue

        content = block["content"]
        if not content.strip():
            result.append(content)
            continue
        print(f"[{i}] translate")
        try:
            translated = translate_text(content,target_lang)
            result.append(translated)

        except Exception as e:
            print("Ошибка:", e)
            result.append(content)

    Path(output_file).write_text("".join(result),encoding="utf-8")

    print(f"\nСохранено: {output_file}")


def main():
    if len(sys.argv) < 4:
        print( "python main.py ""<input.md> ""<output.md> ""<lang>" )
        sys.exit(1)

    if not GROQ_API_KEY:
        print("GROQ_API_KEY не найден.")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    target_lang = sys.argv[3]

    if target_lang not in SUPPORTED_LANGUAGES:
        print("Доступные языки:",", ".join(SUPPORTED_LANGUAGES.keys()))
        sys.exit(1)

    if not os.path.exists(input_file):
        print("Файл не найден.")
        sys.exit(1)
    translate_file(input_file,output_file,target_lang)

if __name__ == "__main__":
    main()