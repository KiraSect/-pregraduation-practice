import os
import sys
import argparse
import subprocess

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

ALLOWED_TYPES = ["feat", "fix", "refactor", "docs","style", "test", "chore", "perf"]

SYSTEM_PROMPT = """
Ты генерируешь commit-сообщения в формате Conventional Commits.

Формат:
<type>(<scope>): <message>

Правила:
- одна строка
- английский язык
- максимум 70 символов
- без точки в конце
- без markdown и пояснений
"""

client = OpenAI(
    api_key=GROQ_API_KEY, 
    base_url="https://api.groq.com/openai/v1"
)


def get_staged_diff():
    try:
        result = subprocess.run(
            ["git", "diff", "--staged"],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )

        if result.returncode != 0:
            print("Ошибка git:", result.stderr)
            return None

        return result.stdout

    except FileNotFoundError:
        print("Git не найден.")
        return None


def make_commit(message: str):
    result = subprocess.run(
        ["git", "commit", "-m", message],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )

    print(result.stdout)

    if result.returncode != 0:
        print("Ошибка commit:", result.stderr)


def generate_commit_message(diff: str, force_type=None, scope=None):

    rules = ""

    if force_type: rules += f"\nИспользуй type: {force_type}"

    if scope: rules += f"\nИспользуй scope: {scope}"

    if len(diff) > 8000: diff = diff[:8000] + "\n(diff truncated)"

    prompt = f"""
Сгенерируй commit message по git diff.

{rules}

Git diff:
{diff}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    message = response.choices[0].message.content.strip()

    message = (
        message
        .strip('"')
        .strip("'")
        .strip("`")
        .split("\n")[0]
        .strip()
    )

    return message


def main():
    parser = argparse.ArgumentParser(description="AI commit generator")
    parser.add_argument("--type",choices=ALLOWED_TYPES)
    parser.add_argument("--scope")
    parser.add_argument("--dry-run",action="store_true")
    args = parser.parse_args()
    if not GROQ_API_KEY:
        print("GROQ_API_KEY не найден.")
        sys.exit(1)

    diff = get_staged_diff()

    if diff is None:
        sys.exit(1)

    if not diff.strip():
        print("Нет staged изменений.")
        sys.exit(1)

    print("Генерирую commit message...")

    message = generate_commit_message(
        diff,
        args.type,
        args.scope
    )

    print("\n" + "=" * 50)
    print(message)
    print("=" * 50)

    if args.dry_run:
        print("\nDry-run режим.")
        return

    answer = input(
        "\nСделать commit? [y/N]: "
    ).strip().lower()

    if answer == "y":
        make_commit(message)
    else:
        print("Commit отменён.")


if __name__ == "__main__":
    main()