
---
### `fastapi_auth.md`

```md id="7m3xqa"
---
summary: "FastAPI поддерживает JWT-аутентификацию и dependency injection."
---

# FastAPI Authentication

В FastAPI часто используют JWT-токены для авторизации пользователей.

Основные компоненты:
- OAuth2PasswordBearer
- Depends
- JWT access token
- middleware

FastAPI хорошо подходит для backend API и микросервисов.

```python
from fastapi import Depends
```