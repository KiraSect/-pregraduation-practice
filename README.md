# AI API Projects
## Проекты
- **article_summarizer_bot** — Telegram-бот, который делает краткий пересказ статьи по ссылке (5 пунктов).
- **ai_commit_helper** — генерация commit-сообщений по `git diff` (Conventional Commits).
- **ai_notes_assistant** — поиск похожих markdown-заметок и генерация summary во frontmatter.
- **ai_unit_test_generator** — генерация pytest-тестов по Python-коду через AST + LLM.
- **ai_comment_moderator** — API для классификации комментариев (ok / spam / toxic / needs_review).
- **ai_issue_matcher** — подбор GitHub issues под стек разработчика.
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
cd article_summarizer_bot
python main.py
```
```bash
cd ai_comment_moderator
uvicorn main:app --reload
```
```bash
cd ai_commit_helper
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
cd ai_issue_matcher
python main.py <github_username>
```
```bash
cd ai_markdown_translator
python main.py input.md output.md ru
```
