# Furs and Fur Coats API

Backend-проект для интернет-магазина меховых изделий и верхней одежды. Приложение предоставляет API для каталога, корзины, заказов и аутентификации, поддерживает OAuth-вход через Yandex, нормализацию контактных данных через Dadata и асинхронную генерацию описаний товаров через Celery + LLM-модель, подключенную через OpenRouter.

## Возможности

- **Каталог товаров** с фильтрацией по категории и диапазону цен.
- **Сортировка товаров по цене**: поддерживаются режимы `price_asc` и `price_desc`.
- **Корзина и оформление заказов** через API.
- **JWT-аутентификация** и регистрация пользователей.
- **Yandex OAuth** для входа через аккаунт Яндекса.
- **Интеграция с Dadata** для очистки и нормализации email, телефона и адреса.
- **Генерация описаний товаров через Celery** с использованием LLM-модели через **OpenRouter**.
- **Seed-скрипт** для инициализации тестовых данных в базе: категорий, 100 товаров и суперпользователя.
- **Docker Compose** для быстрого локального запуска вместе с PostgreSQL и Redis.

## Интеграции

### Dadata
В проекте реализован gateway для работы с Dadata. Интеграция используется для нормализации контактных данных и очистки записей, что особенно полезно при регистрации, оформлении заказов и приведении данных к единому формату.

Необходимые переменные окружения:

- `DADATA_API_KEY`
- `DADATA_SECRET_KEY`

### Yandex OAuth
Поддерживается авторизация через Yandex OAuth:

- `GET /auth/yandex/login` — редирект на страницу авторизации Яндекса.
- `GET /auth/yandex/callback` — обработка callback и вход пользователя в систему.

Необходимые переменные окружения:

- `YANDEX_CLIENT_ID`
- `YANDEX_CLIENT_SECRET`
- `YANDEX_REDIRECT_URI`

### OpenRouter + Celery
Для карточек товаров доступна асинхронная генерация описаний. Логика работает через **Celery worker**, а текст генерируется LLM-моделью, вызываемой через **OpenRouter**.

Необходимые переменные окружения:

- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `OPENROUTER_BASE_URL`
- `OPENROUTER_HTTP_REFERER`
- `OPENROUTER_X_TITLE`

## Стек

- **Python 3.12**
- **FastAPI**
- **SQLAlchemy**
- **Alembic**
- **PostgreSQL**
- **Redis**
- **Celery**
- **Docker / Docker Compose**
- **Dadata API**
- **Yandex OAuth**
- **OpenRouter / LLM**
- **Pytest**

## Структура сервисов

При локальном запуске через Docker Compose поднимаются:

- `backend` — FastAPI-приложение;
- `celery` — Celery worker для фоновых задач;
- `db` — PostgreSQL;
- `redis` — Redis для Celery и вспомогательной инфраструктуры.

## Быстрый старт

### Вариант 1. Запуск через Docker Compose

Это самый простой способ поднять проект локально.

1. Скопируйте пример переменных окружения:

```bash
cp .env.example .env
```

2. Заполните `.env` нужными значениями. Минимально рекомендуется указать:

```env
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=furs
POSTGRES_USER=postgres
POSTGRES_PASSWORD=1234

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

JWT_SECRET_KEY=dev-secret

SUPERUSER_EMAIL=admin@example.com
SUPERUSER_PHONE=79990000000
SUPERUSER_PASSWORD=admin12345

YANDEX_CLIENT_ID=
YANDEX_CLIENT_SECRET=
YANDEX_REDIRECT_URI=

DADATA_API_KEY=
DADATA_SECRET_KEY=

OPENROUTER_API_KEY=
OPENROUTER_MODEL=arcee-ai/trinity-large-preview:free
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1/chat/completions
```

3. Запустите проект:

```bash
docker compose up --build
```

После старта будут автоматически выполнены:

- миграции Alembic;
- seed-скрипт с тестовыми данными;
- создание/обновление суперпользователя;
- запуск FastAPI на `http://localhost:8000`.

Полезные URL:

- API: `http://localhost:8000`
- Healthcheck: `http://localhost:8000/health`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Вариант 2. Локальный запуск без Docker

1. Установите зависимости:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Поднимите отдельно PostgreSQL и Redis.

3. Создайте `.env` и укажите переменные окружения для базы, Redis и внешних интеграций.

4. Примените миграции:

```bash
alembic upgrade head
```

5. Инициализируйте тестовые данные:

```bash
python -m scripts.seed_data
```

6. Запустите API:

```bash
uvicorn main:app --reload
```

7. В отдельном терминале запустите Celery worker:

```bash
celery -A infrastructure.tasks_queue.celery_app:celery_app worker --loglevel=info
```

## Тестовые данные и суперпользователь

В проекте есть скрипт `scripts/seed_data.py`, который:

- создает корневые и дочерние категории;
- создает или обновляет суперпользователя;
- добавляет тестовые товары в базу (до 100 записей).

По умолчанию суперпользователь создается со следующими значениями:

- `SUPERUSER_EMAIL=admin@example.com`
- `SUPERUSER_PHONE=79990000000`
- `SUPERUSER_PASSWORD=admin12345`

Запуск вручную:

```bash
python -m scripts.seed_data
```

## Работа с каталогом

Каталог предоставляет фильтрацию и пагинацию, а также сортировку товаров по цене.

Пример запроса:

```http
GET /products?min_price=50000&max_price=150000&sort=price_asc&limit=20&offset=0
```

Поддерживаемые значения параметра `sort`:

- `price_asc` — сначала более дешевые товары;
- `price_desc` — сначала более дорогие товары.

## Основные API-разделы

- `/auth` — регистрация, логин, Yandex OAuth;
- `/products` и `/product/{product_id}` — каталог и карточка товара;
- `/categories` — дерево категорий;
- `/cart` — корзина;
- `/orders` — оформление и просмотр заказов;
- админские endpoints для генерации описаний товаров.

## Разработка и тесты

Запуск тестов:

```bash
pytest -v
```