# Быстрый старт UltraDating Bot

Запустите бота за 5 минут!

## Шаг 1: Клонируйте репозиторий

```bash
git clone <repository-url>
cd ultradating
```

## Шаг 2: Установите зависимости

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

## Шаг 3: Настройте базу данных

### Вариант A: Docker (рекомендуется)

```bash
docker-compose up -d postgres redis
```

### Вариант B: Локальная установка

Установите PostgreSQL 16 и Redis 7, затем создайте базу:

```sql
CREATE DATABASE ultradating;
CREATE EXTENSION postgis;
```

## Шаг 4: Получите API ключи

### Telegram Bot Token
1. Откройте [@BotFather](https://t.me/BotFather)
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте токен

### OpenRouter API Key (бесплатно!)
1. Зарегистрируйтесь на https://openrouter.ai/
2. Перейдите в https://openrouter.ai/keys
3. Нажмите "Create Key"
4. Скопируйте ключ (показывается только один раз!)

## Шаг 5: Настройте .env

```bash
cp .env.example .env
```

Отредактируйте `.env`:

```env
# Обязательные параметры
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
BOT_USERNAME=your_bot_username
OPENROUTER_API_KEY=sk-or-v1-ваш-ключ-здесь

# База данных (если используете Docker, оставьте как есть)
DATABASE_URL=postgresql+asyncpg://ultradating:ultradating@localhost:5432/ultradating
REDIS_URL=redis://localhost:6379/0

# Опционально
LOG_LEVEL=INFO
SENTRY_DSN=
```

## Шаг 6: Примените миграции

```bash
alembic upgrade head
```

## Шаг 7: Запустите бота

```bash
python -m bot.main
```

Готово! 🎉

Откройте вашего бота в Telegram и отправьте `/start`

## Проверка работы

1. Отправьте `/start` - должно появиться приветствие
2. Заполните профиль
3. Попробуйте поиск - AI должен подобрать совместимость

## Troubleshooting

### "Database connection failed"
- Проверьте, что PostgreSQL запущен: `docker-compose ps`
- Проверьте DATABASE_URL в .env

### "Redis connection failed"
- Проверьте, что Redis запущен: `docker-compose ps`
- Проверьте REDIS_URL в .env

### "OpenRouter API error"
- Проверьте API ключ на https://openrouter.ai/keys
- Убедитесь, что ключ начинается с `sk-or-v1-`
- Проверьте лимиты на https://openrouter.ai/activity

### "Alembic migration failed"
- Убедитесь, что база данных создана
- Проверьте, что PostGIS установлен: `CREATE EXTENSION postgis;`
- Попробуйте: `alembic downgrade base && alembic upgrade head`

## Следующие шаги

1. Настройте платежи (Telegram Stars / ЮKassa)
2. Настройте мониторинг (Sentry)
3. Прочитайте [README.md](README.md) для подробностей
4. Изучите [OPENROUTER_SETUP.md](OPENROUTER_SETUP.md) для оптимизации AI

## Полезные команды

```bash
# Запуск тестов
pytest

# Создание миграции
alembic revision --autogenerate -m "Description"

# Просмотр логов Docker
docker-compose logs -f

# Остановка сервисов
docker-compose down

# Очистка базы данных
docker-compose down -v
```

## Поддержка

Если что-то не работает:
1. Проверьте логи бота
2. Проверьте `.env` файл
3. Убедитесь, что все сервисы запущены
4. Создайте issue в репозитории

Удачи! 🚀
