# Развертывание на Railway

Пошаговое руководство по развертыванию UltraDating бота на Railway.

## Шаг 1: Подготовка

### 1.1 Создайте аккаунт Railway

1. Перейдите на https://railway.app
2. Нажмите "Start a New Project"
3. Войдите через GitHub (рекомендуется)

### 1.2 Получите необходимые ключи

Вам понадобятся:
- ✅ Telegram Bot Token (от @BotFather)
- ✅ OpenRouter API Key (от https://openrouter.ai/keys)
- ⚠️ Telegram Payment Token (опционально, для платежей)
- ⚠️ Sentry DSN (опционально, для мониторинга)

## Шаг 2: Создание проекта на Railway

### 2.1 Создайте новый проект

1. На главной странице Railway нажмите **"New Project"**
2. Выберите **"Deploy from GitHub repo"**
3. Выберите репозиторий **swiftkeyy/znakomstva**
4. Railway автоматически обнаружит Python проект

### 2.2 Добавьте базу данных PostgreSQL

1. В вашем проекте нажмите **"+ New"**
2. Выберите **"Database"** → **"Add PostgreSQL"**
3. Railway автоматически создаст базу данных
4. Переменная `DATABASE_URL` будет создана автоматически

### 2.3 Добавьте Redis

1. Нажмите **"+ New"** снова
2. Выберите **"Database"** → **"Add Redis"**
3. Railway автоматически создаст Redis
4. Переменная `REDIS_URL` будет создана автоматически

## Шаг 3: Настройка переменных окружения

### 3.1 Откройте настройки сервиса

1. Кликните на ваш Python сервис (не на базы данных)
2. Перейдите на вкладку **"Variables"**

### 3.2 Добавьте обязательные переменные

Нажмите **"+ New Variable"** и добавьте:

```env
# Telegram Bot
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
BOT_USERNAME=your_bot_username

# OpenRouter AI
OPENROUTER_API_KEY=sk-or-v1-ваш-ключ-здесь

# Настройки
LOG_LEVEL=INFO
```

### 3.3 Проверьте автоматические переменные

Railway должен автоматически создать:
- ✅ `DATABASE_URL` - подключение к PostgreSQL
- ✅ `REDIS_URL` - подключение к Redis

Если их нет, добавьте вручную (значения можно найти в настройках баз данных).

### 3.4 Опциональные переменные

Для продакшена рекомендуется добавить:

```env
# Мониторинг (опционально)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project

# Платежи (опционально)
TELEGRAM_PAYMENT_TOKEN=your_payment_token
YUKASSA_SHOP_ID=your_shop_id
YUKASSA_SECRET_KEY=your_secret_key

# Лимиты (опционально, есть значения по умолчанию)
RATE_LIMIT_SWIPES_FREE=100
RATE_LIMIT_SWIPES_PREMIUM=500
RATE_LIMIT_MESSAGES_FREE=50
RATE_LIMIT_MESSAGES_PREMIUM=250
```

## Шаг 4: Настройка развертывания

### 4.1 Проверьте настройки сборки

Railway должен автоматически определить:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python -m bot.main`

Если нет, добавьте вручную:

1. Перейдите в **"Settings"** → **"Deploy"**
2. **Build Command**: 
   ```bash
   pip install -r requirements.txt
   ```
3. **Start Command**:
   ```bash
   python -m bot.main
   ```

### 4.2 Настройте Healthcheck (опционально)

1. В **"Settings"** → **"Healthcheck"**
2. Включите healthcheck
3. **Path**: `/health`
4. **Port**: `8000`
5. **Timeout**: `30` секунд

## Шаг 5: Применение миграций базы данных

### 5.1 Подключитесь к Railway CLI

Установите Railway CLI:

```bash
# Windows (PowerShell)
iwr https://railway.app/install.ps1 | iex

# Mac/Linux
curl -fsSL https://railway.app/install.sh | sh
```

Войдите в аккаунт:

```bash
railway login
```

### 5.2 Свяжите проект

```bash
cd ultradating
railway link
```

Выберите ваш проект из списка.

### 5.3 Примените миграции

```bash
railway run alembic upgrade head
```

Или через Railway Dashboard:

1. Перейдите в **"Settings"** → **"Deploy"**
2. Добавьте **"Custom Start Command"**:
   ```bash
   alembic upgrade head && python -m bot.main
   ```

## Шаг 6: Развертывание

### 6.1 Запустите развертывание

Railway автоматически начнет развертывание после:
- Добавления переменных окружения
- Push в GitHub репозиторий

Или запустите вручную:
1. Перейдите в **"Deployments"**
2. Нажмите **"Deploy"**

### 6.2 Проверьте логи

1. Откройте вкладку **"Deployments"**
2. Кликните на последнее развертывание
3. Проверьте логи на наличие ошибок

Должны увидеть:
```
bot_starting version=1.0.0
bot_started
```

## Шаг 7: Проверка работы

### 7.1 Проверьте healthcheck

Если настроили healthcheck, Railway покажет статус "Healthy" ✅

### 7.2 Проверьте бота в Telegram

1. Откройте вашего бота в Telegram
2. Отправьте `/start`
3. Должно появиться приветственное сообщение

### 7.3 Проверьте базу данных

Подключитесь к PostgreSQL:

```bash
railway connect postgres
```

Проверьте таблицы:
```sql
\dt
```

Должны увидеть все таблицы (users, profiles, matches и т.д.)

## Шаг 8: Настройка автоматического развертывания

### 8.1 Включите автодеплой

1. Перейдите в **"Settings"** → **"Service"**
2. Найдите **"Deploy Triggers"**
3. Убедитесь, что включено:
   - ✅ **Deploy on push to main branch**

Теперь каждый push в GitHub автоматически запустит развертывание!

### 8.2 Настройте ветки (опционально)

Для staging окружения:
1. Создайте новый сервис
2. Настройте его на ветку `develop`
3. Используйте отдельные переменные окружения

## Troubleshooting

### Ошибка: "Database connection failed"

**Решение:**
1. Проверьте, что PostgreSQL сервис запущен
2. Проверьте переменную `DATABASE_URL`
3. Убедитесь, что миграции применены

### Ошибка: "Redis connection failed"

**Решение:**
1. Проверьте, что Redis сервис запущен
2. Проверьте переменную `REDIS_URL`
3. Перезапустите сервис

### Ошибка: "OpenRouter API error"

**Решение:**
1. Проверьте `OPENROUTER_API_KEY`
2. Убедитесь, что ключ активен на https://openrouter.ai/keys
3. Проверьте лимиты на https://openrouter.ai/activity

### Бот не отвечает в Telegram

**Решение:**
1. Проверьте логи в Railway
2. Убедитесь, что `BOT_TOKEN` правильный
3. Проверьте, что сервис запущен (статус "Active")
4. Проверьте healthcheck endpoint

### Миграции не применяются

**Решение:**
1. Примените миграции вручную через CLI:
   ```bash
   railway run alembic upgrade head
   ```
2. Или добавьте в start command:
   ```bash
   alembic upgrade head && python -m bot.main
   ```

### Высокое использование ресурсов

**Решение:**
1. Проверьте логи на наличие бесконечных циклов
2. Оптимизируйте запросы к базе данных
3. Настройте кэширование
4. Рассмотрите upgrade плана Railway

## Мониторинг

### Просмотр логов

```bash
# Через CLI
railway logs

# Или в Dashboard
Deployments → Latest → View Logs
```

### Метрики

1. Перейдите в **"Metrics"**
2. Отслеживайте:
   - CPU usage
   - Memory usage
   - Network traffic

### Алерты

Настройте уведомления:
1. **"Settings"** → **"Notifications"**
2. Добавьте email или Slack webhook
3. Выберите события для уведомлений

## Стоимость

### Бесплатный план

Railway предоставляет:
- $5 бесплатных кредитов в месяц
- Достаточно для небольшого бота
- Автоматическое отключение при превышении

### Платный план

Для продакшена рекомендуется:
- **Hobby Plan**: $5/месяц + usage
- **Pro Plan**: $20/месяц + usage

Калькулятор: https://railway.app/pricing

## Оптимизация затрат

1. **Используйте кэширование** - меньше запросов к AI
2. **Оптимизируйте запросы** - меньше нагрузка на БД
3. **Настройте rate limiting** - защита от злоупотреблений
4. **Мониторьте использование** - отслеживайте расходы

## Резервное копирование

### Автоматические бэкапы PostgreSQL

Railway автоматически создает бэкапы PostgreSQL.

Восстановление:
1. **"Database"** → **"Backups"**
2. Выберите бэкап
3. **"Restore"**

### Ручной бэкап

```bash
# Экспорт базы данных
railway run pg_dump $DATABASE_URL > backup.sql

# Импорт базы данных
railway run psql $DATABASE_URL < backup.sql
```

## Масштабирование

### Вертикальное масштабирование

1. Upgrade плана Railway
2. Больше CPU и RAM автоматически

### Горизонтальное масштабирование

Для высоких нагрузок:
1. Используйте несколько инстансов бота
2. Настройте load balancer
3. Используйте Redis для синхронизации

## Полезные команды Railway CLI

```bash
# Просмотр логов
railway logs

# Выполнение команды
railway run <command>

# Подключение к базе данных
railway connect postgres
railway connect redis

# Просмотр переменных
railway variables

# Открыть проект в браузере
railway open
```

## Дополнительные ресурсы

- [Railway Documentation](https://docs.railway.app/)
- [Railway Discord](https://discord.gg/railway)
- [Railway Status](https://status.railway.app/)
- [Railway Blog](https://blog.railway.app/)

## Поддержка

Если возникли проблемы:
1. Проверьте логи в Railway Dashboard
2. Посмотрите [Railway Docs](https://docs.railway.app/)
3. Спросите в [Railway Discord](https://discord.gg/railway)
4. Создайте issue в GitHub репозитории

---

**Готово!** 🚀 Ваш бот теперь работает на Railway!
