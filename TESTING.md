# Testing Guide

Руководство по тестированию проекта "Моя половинка".

## Структура тестов

```
tests/
├── unit/              # Unit тесты с моками
├── integration/       # Integration тесты с реальными сервисами
├── property/          # Property-based тесты (Hypothesis)
├── smoke/            # Smoke тесты для базовой проверки
└── conftest.py       # Общие фикстуры
```

## Запуск тестов

### Все тесты

```bash
pytest
```

### По категориям

```bash
# Unit тесты
pytest -m unit

# Integration тесты
pytest -m integration

# Property-based тесты
pytest -m property

# Smoke тесты
pytest -m smoke
```

### С покрытием кода

```bash
pytest --cov=bot --cov=database --cov-report=html
```

Отчёт будет доступен в `htmlcov/index.html`.

### Конкретный файл

```bash
pytest tests/unit/test_repositories.py
```

### Конкретный тест

```bash
pytest tests/unit/test_repositories.py::TestUserRepository::test_add_crystals
```

## Требования для тестов

### Unit тесты

Не требуют внешних зависимостей. Используют:
- In-memory SQLite
- Mock Redis
- Mock Ollama

```bash
pytest -m unit
```

### Integration тесты

Требуют запущенные сервисы:

**PostGIS тесты:**
```bash
# Запустите PostgreSQL с PostGIS
docker run -d \
  --name postgis-test \
  -e POSTGRES_PASSWORD=test \
  -p 5432:5432 \
  postgis/postgis:16-3.4

# Запустите тесты
pytest tests/integration/test_geo_search.py
```

**Ollama тесты:**
```bash
# Убедитесь, что Ollama запущен
ollama serve

# Загрузите модели
ollama pull qwen3:32b

# Запустите тесты
pytest tests/integration/test_ollama_integration.py
```

### Property-based тесты

Используют Hypothesis для генерации тестовых данных:

```bash
pytest -m property
```

Hypothesis автоматически генерирует множество тестовых случаев для проверки свойств кода.

## Smoke тесты на Railway

### Подготовка

1. Разверните приложение на Railway staging environment
2. Настройте переменные окружения
3. Дождитесь успешного деплоя

### Проверка health endpoint

```bash
curl https://your-app.railway.app/health
```

Ожидаемый ответ:
```json
{"status":"ok"}
```

### Проверка базовых функций

1. **Запуск бота:**
   - Отправьте `/start` боту в Telegram
   - Проверьте, что бот отвечает

2. **Регистрация:**
   - Пройдите процесс регистрации
   - Проверьте, что профиль создаётся

3. **Базовые команды:**
   - Проверьте главное меню
   - Проверьте настройки
   - Проверьте просмотр профиля

4. **AI функции:**
   - Попробуйте улучшить профиль через AI
   - Проверьте генерацию подсказок (если есть матч)

5. **Планировщик:**
   - Проверьте логи на наличие запланированных задач
   - Убедитесь, что задачи выполняются

### Проверка логов

```bash
# Railway CLI
railway logs

# Или в Railway Dashboard
# Project → Deployments → View Logs
```

Проверьте на наличие:
- ✅ `bot_started`
- ✅ `all_scheduled_jobs_registered`
- ❌ Отсутствие критических ошибок

### Проверка базы данных

```bash
# Подключитесь к Railway PostgreSQL
railway connect postgres

# Проверьте таблицы
\dt

# Проверьте пользователей
SELECT count(*) FROM users;

# Проверьте расширение PostGIS
SELECT PostGIS_Version();
```

### Проверка Redis

```bash
# Подключитесь к Railway Redis
railway connect redis

# Проверьте ключи
KEYS *

# Проверьте rate limiting
GET rate:swipe:1
```

## Continuous Integration

### GitHub Actions (пример)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgis/postgis:16-3.4
        env:
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run unit tests
        run: pytest -m unit
      
      - name: Run property tests
        run: pytest -m property
      
      - name: Run smoke tests
        run: pytest -m smoke
```

## Отладка тестов

### Verbose режим

```bash
pytest -vv
```

### Показать print statements

```bash
pytest -s
```

### Остановиться на первой ошибке

```bash
pytest -x
```

### Запустить только упавшие тесты

```bash
pytest --lf
```

### Отладка с pdb

```bash
pytest --pdb
```

## Best Practices

1. **Изоляция тестов:** Каждый тест должен быть независимым
2. **Фикстуры:** Используйте фикстуры для переиспользования кода
3. **Моки:** Мокайте внешние зависимости в unit тестах
4. **Именование:** Используйте описательные имена тестов
5. **Документация:** Добавляйте docstrings к тестам
6. **Покрытие:** Стремитесь к покрытию >80%

## Troubleshooting

### Тесты падают с ошибкой подключения к БД

```bash
# Проверьте, что PostgreSQL запущен
docker ps | grep postgres

# Проверьте переменные окружения
echo $DATABASE_URL
```

### Тесты падают с ошибкой Redis

```bash
# Проверьте, что Redis запущен
docker ps | grep redis

# Проверьте подключение
redis-cli ping
```

### Ollama тесты пропускаются

```bash
# Проверьте, что Ollama запущен
curl http://localhost:11434/api/tags

# Загрузите модели
ollama pull qwen3:32b
```

### Медленные тесты

```bash
# Запустите только быстрые тесты
pytest -m "not slow"

# Или увеличьте timeout
pytest --timeout=600
```

## Дополнительные ресурсы

- [Pytest Documentation](https://docs.pytest.org/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Railway Documentation](https://docs.railway.app/)
