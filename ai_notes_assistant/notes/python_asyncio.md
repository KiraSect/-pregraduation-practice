---
summary: "Asyncio используется для асинхронных задач и сетевых запросов."
---

# Python Asyncio

Asyncio позволяет запускать асинхронный код в Python.

Его используют для:
- API-клиентов
- Telegram-ботов
- websocket-сервисов
- фоновых задач

Для async-функций используется `async def`.

```python
import asyncio

async def main():
    await asyncio.sleep(1)
```
asyncio.run(main())