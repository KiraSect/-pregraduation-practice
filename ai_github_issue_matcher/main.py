import os
import sys
import json
import time
import hashlib

from pathlib import Path
from collections import Counter

import requests

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GITHUB_API = "https://api.github.com"

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

CACHE_TTL_HOURS = 6

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)


def github_headers():
    headers = {
        "Accept": "application/vnd.github+json"
    }

    if GITHUB_TOKEN:
        headers["Authorization"] = (
            f"Bearer {GITHUB_TOKEN}"
        )

    return headers


def cache_get(key: str):
    file = CACHE_DIR / (hashlib.md5(key.encode()).hexdigest() + ".json")

    if not file.exists():
        return None

    age = (time.time() - file.stat().st_mtime) / 3600

    if age > CACHE_TTL_HOURS:
        return None

    try:
        return json.loads(
            file.read_text(encoding="utf-8")
        )
    except Exception:
        return None


def cache_set(key: str, data):
    file = CACHE_DIR / (hashlib.md5(key.encode()).hexdigest()+ ".json")

    file.write_text(
        json.dumps(data, ensure_ascii=False),
        encoding="utf-8"
    )


def get_user_languages(username: str):
    cache_key = f"langs:{username}"
    cached = cache_get(cache_key)
    if cached:
        print("(данные из кэша)")
        return cached

    print(f"Получаю репозитории @{username}...")

    url = (
        f"{GITHUB_API}/users/"
        f"{username}/repos"
    )

    response = requests.get(
        url, headers=github_headers(),
        params={"per_page": 30,"sort": "updated"},timeout=15
    )

    if response.status_code == 404:
        print("Пользователь не найден.")
        return []

    response.raise_for_status()

    repos = response.json()

    if not repos:
        print("Нет публичных репозиториев.")
        return []

    counter = Counter()

    for repo in repos:

        if repo.get("language"):
            counter[repo["language"]] += 1

    languages = [
        lang
        for lang, _ in counter.most_common(5)
    ]

    print("Топ языков:", languages)
    cache_set(cache_key, languages)
    return languages


def search_issues(language: str, limit: int = 15):

    cache_key = f"issues:{language}"

    cached = cache_get(cache_key)

    if cached:
        print(f"{language}: issues из кэша")
        return cached

    query = (
        'is:issue is:open '
        'label:"good first issue" '
        f'language:{language}'
    )

    response = requests.get(
        f"{GITHUB_API}/search/issues",
        headers=github_headers(),
        params={
            "q": query,
            "sort": "comments",
            "order": "desc",
            "per_page": limit
        },
        timeout=20
    )

    if response.status_code != 200:
        print(f"Ошибка поиска {language}")
        return []

    items = response.json().get("items", [])

    issues = []

    for item in items:

        repo_url = item.get(
            "repository_url",
            ""
        )

        repo = "/".join(
            repo_url.split("/")[-2:]
        )

        issues.append({
            "title": item["title"],
            "url": item["html_url"],
            "repo": repo,
            "body": (
                item.get("body") or ""
            )[:300],
            "comments": item.get(
                "comments",
                0
            )
        })

    print(f"{language}: {len(issues)} issues")

    cache_set(cache_key, issues)

    return issues


def rank_issues(issues, languages, top_n=10):

    short_issues = []

    for i, issue in enumerate(issues):

        short_issues.append({
            "index": i,
            "repo": issue["repo"],
            "title": issue["title"],
            "body": issue["body"][:150]
        })

    prompt = f"""
Ты помогаешь подобрать GitHub issues.

Разработчик использует:
{', '.join(languages)}

Выбери {top_n} самых релевантных
good-first-issues.

Верни JSON:

{{
  "selected": [
    {{
      "index": 0,
      "reason": "почему подходит"
    }}
  ]
}}

Issues:
{json.dumps(short_issues, ensure_ascii=False)}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.3,

        response_format={
            "type": "json_object"
        }
    )

    result = json.loads(
        response.choices[0].message.content
    )

    ranked = []

    for item in result.get("selected", []):

        idx = item.get("index")

        if (isinstance(idx, int) and 0 <= idx < len(issues)):

            issue = issues[idx].copy()
            issue["reason"] = item.get(
                "reason",
                "")
            ranked.append(issue)

    return ranked[:top_n]


def main():

    if len(sys.argv) < 2:
        print("Использование:\n"
            "python main.py <github_username>")
        sys.exit(1)

    if not GROQ_API_KEY:
        print("GROQ_API_KEY не найден.")
        sys.exit(1)

    username = sys.argv[1]

    if not GITHUB_TOKEN:
        print("GITHUB_TOKEN не указан.\n"
            "Лимит API: 60 запросов/час.")

    languages = get_user_languages(username)

    if not languages:
        print("Не удалось определить стек.")
        sys.exit(1)

    print("\nИщу issues...\n")
    all_issues = []
    for lang in languages[:3]:
        all_issues.extend(search_issues(lang))

    if not all_issues:
        print("Подходящих issues нет.")
        return

    print(f"\nВсего найдено:"f" {len(all_issues)}")

    print("Ранжирую задачи...\n")
    top_issues = rank_issues(all_issues,languages)

    print("=" * 70)
    print(f"TOP-{len(top_issues)} ISSUES")
    print("=" * 70)

    for i, issue in enumerate(top_issues, 1):
        print(f"\n{i}. "f"[{issue['repo']}] "f"{issue['title']}")
        print(issue["url"])
        print(f"Комментарии: "f"{issue['comments']}")
        print(f"Почему подходит: "f"{issue['reason']}")


if __name__ == "__main__":
    main()