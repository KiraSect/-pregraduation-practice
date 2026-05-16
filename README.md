# AI API Projects
- **ai_article_summarizer** — Telegram-бот для краткого пересказа статей по ссылке.
- **ai_commit_generator** — генератор commit-сообщений по git diff.
- **ai_notes_assistant** — анализ markdown-заметок и поиск связей между ними.
- **ai_unit_test_generator** — генерация pytest-тестов через AST + LLM.
- **ai_comment_moderation** — API для модерации комментариев (ok / spam / toxic / needs_review).
- **ai_github_issue_matcher** — подбор GitHub issues под стек разработчика.
- **ai_markdown_translator** — перевод markdown с сохранением структуры и кода.

---
## Запуск

### Установка зависимостей
```bash
pip install -r requirements.txt
```
Переменные окружения (.env
```bash
GROQ_API_KEY=...
TELEGRAM_TOKEN=...
GITHUB_TOKEN=...
```
### Каждый проект запускается из своей папки следующим образом:
```bash
cd article_summarizer
python main.py
```
```bash
cd ai_comment_moderation
uvicorn main:app --reload
```
```bash
cd ai_commit_generator
python main.py --dry-run
```
```bash
cd ai_unit_test_generator
python main.py example_module.py
```
```bash
cd ai_notes_assistant
python main.py notes
```
```bash
cd ai_github_issue_matcher
python main.py <github_username>
```
```bash
cd ai_markdown_translator
python main.py input.md output.md ru
```
