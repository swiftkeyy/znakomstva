# Моя половинка — AI-Powered Dating Telegram Bot

Полнофункциональный Telegram-бот для знакомств с AI-функциями на базе OpenRouter. Система предоставляет расширенные возможности матчинга, AI-ассистента для общения, верификацию пользователей, премиум-функции и монетизацию.

## Ключевые особенности

- 🤖 **AI-матчинг**: Гибридный алгоритм подбора пар (геолокация + AI-совместимость)
- 💬 **AI-ассистент**: Генерация подсказок для общения (3 варианта: дерзкий, тёплый, игривый)
- ✅ **Верификация**: 3-уровневая система верификации с face matching
- 💎 **Монетизация**: Премиум подписка, кристаллы, бусты
- ⚡ **Speed Dating**: Быстрые знакомства с автоматическим подбором пар
- 📊 **Аналитика**: Ежедневные отчёты с персонализированными советами
- 🔒 **Модерация**: Автоматическая модерация контента через AI

## Технологический стек

- **Backend**: Python 3.12+, aiogram 3.13+
- **Database**: PostgreSQL 16 + PostGIS
- **Cache**: Redis 7+
- **AI**: OpenRouter API (Meta Llama 3.2 бесплатные модели)
- **Payments**: Telegram Stars, ЮKassa
- **Deployment**: Railway, Docker

## Быстрый старт

### Требования

- Python 3.12+
- PostgreSQL 16 с PostGIS
- Redis 7+
- OpenRouter API ключ (бесплатный)

### Локальная установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd ultradating
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

5. Настройте переменные окружения в `.env`:
```env
BOT_TOKEN=your_telegram_bot_token
BOT_USERNAME=your_bot_username
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ultradating
REDIS_URL=redis://localhost:6379/0
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here
LOG_LEVEL=INFO
SENTRY_DSN=  # опционально
```

**Получение OpenRouter API ключа:**
1. Зарегистрируйтесь на https://openrouter.ai/
2. Перейдите в https://openrouter.ai/keys
3. Создайте новый API ключ
4. Скопируйте ключ в `.env`

Подробнее: [OPENROUTER_SETUP.md](OPENROUTER_SETUP.md)

6. Примените миграции базы данных:
```bash
alembic upgrade head
```

7. Запустите бота:
```bash
python -m bot
```

## Настройка AI (OpenRouter)

Бот использует OpenRouter API для доступа к бесплатным AI моделям от Meta (Llama 3.2).

### Преимущества OpenRouter

✅ **Не требует установки** - только API ключ  
✅ **Бесплатные модели** - Meta Llama 3.2 доступны бесплатно  
✅ **Быстрый старт** - работает сразу после получения ключа  
✅ **Не требует GPU** - все вычисления на стороне сервера  
✅ **Автообновления** - модели обновляются автоматически  

### Используемые модели

- **Текст**: `meta-llama/llama-3.2-3b-instruct:free` - для совместимости, подсказок, советов
- **Vision**: `meta-llama/llama-3.2-11b-vision-instruct:free` - для анализа фото, верификации
- **Reasoning**: `meta-llama/llama-3.2-3b-instruct:free` - для глубокого поиска

### Лимиты бесплатного тарифа

- ~20-30 запросов в минуту
- ~100,000 токенов в день
- Только модели с пометкой `:free`

Для большинства ботов этого достаточно. При необходимости можно пополнить баланс на https://openrouter.ai/credits

### Альтернатива: Локальный Ollama

Если нужна максимальная приватность или автономность, можно использовать локальный Ollama:

1. Установите Ollama: https://ollama.ai/download
2. Скачайте модели: `ollama pull qwen3:32b`
3. Откатите код на предыдущую версию (см. [MIGRATION_TO_OPENROUTER.md](MIGRATION_TO_OPENROUTER.md))

**Сравнение:**

| Параметр | OpenRouter | Ollama |
|----------|-----------|--------|
| Установка | Не требуется | Требуется |
| Железо | Не требуется | GPU желательно |
| Диск | Не требуется | 10-50 GB на модель |
| Стоимость | Бесплатный tier | Полностью бесплатно |
| Приватность | Данные на сервере | 100% локально |

## Развёртывание на Railway

### Подготовка

1. Создайте аккаунт на [Railway](https://railway.app)

2. Установите Railway CLI:
```bash
npm install -g @railway/cli
```

3. Войдите в Railway:
```bash
railway login
```

### Развёртывание

1. Создайте новый проект:
```bash
railway init
```

2. Добавьте сервисы:
```bash
# PostgreSQL
railway add postgresql

# Redis
railway add redis
```

3. Настройте переменные окружения в Railway Dashboard:
- `BOT_TOKEN`: Токен вашего Telegram бота
- `BOT_USERNAME`: Username бота (без @)
- `DATABASE_URL`: Автоматически настроен Railway
- `REDIS_URL`: Автоматически настроен Railway
- `OPENROUTER_API_KEY`: Ваш API ключ OpenRouter
- `LOG_LEVEL`: INFO
- `SENTRY_DSN`: (опционально)

4. Разверните приложение:
```bash
railway up
```

### OpenRouter на Railway

OpenRouter работает через API и не требует дополнительной настройки на Railway:

✅ Не нужен GPU  
✅ Не нужны дополнительные сервисы  
✅ Работает из коробки  

Просто укажите `OPENROUTER_API_KEY` в переменных окружения.

## Структура проекта

```
ultradating/
├── bot/                    # Основной код бота
│   ├── handlers/          # Обработчики команд и событий
│   ├── keyboards/         # Клавиатуры и callback data
│   ├── middlewares/       # Middleware для обработки запросов
│   ├── services/          # Бизнес-логика
│   ├── fsm/              # FSM состояния
│   ├── utils/            # Утилиты
│   ├── config.py         # Конфигурация
│   ├── main.py           # Точка входа
│   ├── openrouter_client.py  # Клиент OpenRouter
│   ├── prompts.py        # AI промпты
│   └── scheduler.py      # Планировщик задач
├── database/              # Работа с БД
│   ├── models/           # SQLAlchemy модели
│   ├── repositories/     # Репозитории (Data Access Layer)
│   ├── migrations/       # Alembic миграции
│   └── connection.py     # Подключение к БД
├── tests/                 # Тесты
│   ├── unit/             # Unit тесты
│   ├── integration/      # Integration тесты
│   ├── property/         # Property-based тесты
│   └── conftest.py       # Pytest фикстуры
├── docker/                # Docker конфигурация
├── .env.example          # Пример переменных окружения
├── alembic.ini           # Конфигурация Alembic
├── docker-compose.yml    # Docker Compose для разработки
├── Dockerfile            # Dockerfile для production
├── railway.toml          # Конфигурация Railway
├── requirements.txt      # Python зависимости
└── README.md            # Этот файл
```

## Разработка

### Запуск тестов

```bash
# Все тесты
pytest

# Unit тесты
pytest tests/unit/

# Integration тесты
pytest tests/integration/

# Property-based тесты
pytest tests/property/

# С покрытием
pytest --cov=bot --cov=database
```

### Создание миграции

```bash
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Docker Compose для разработки

```bash
docker-compose up -d
```

Это запустит:
- PostgreSQL с PostGIS
- Redis

## Документация

- [OPENROUTER_SETUP.md](OPENROUTER_SETUP.md) - Подробная настройка OpenRouter
- [MIGRATION_TO_OPENROUTER.md](MIGRATION_TO_OPENROUTER.md) - Миграция с Ollama на OpenRouter
- [TESTING.md](TESTING.md) - Руководство по тестированию

## Мониторинг и логирование

Бот использует:
- **structlog** для JSON-логирования
- **Sentry** для отслеживания ошибок (опционально)
- **Health check endpoint** на порту 8000 (`/health`)

## Лицензия

MIT License

## Поддержка

Для вопросов и поддержки создайте issue в репозитории.
