# Changelog: Миграция на OpenRouter

## [2.0.0] - 2024-XX-XX

### 🚀 Крупные изменения

#### Замена Ollama на OpenRouter API

**Мотивация:**
- Упрощение развертывания (не нужна локальная установка)
- Снижение требований к железу (не нужен GPU)
- Быстрый старт для новых пользователей
- Доступ к бесплатным моделям Meta Llama 3.2

### ✨ Добавлено

- `bot/openrouter_client.py` - новый клиент для OpenRouter API
- `OPENROUTER_SETUP.md` - руководство по настройке OpenRouter
- `MIGRATION_TO_OPENROUTER.md` - инструкция по миграции с Ollama
- `CHANGELOG_OPENROUTER.md` - этот файл
- Поддержка бесплатных моделей Meta Llama 3.2
- Автоматическая обработка ошибок API с retry логикой
- Поддержка vision моделей через OpenRouter

### 🔄 Изменено

#### Конфигурация (`bot/config.py`)
- Удалены настройки Ollama:
  - `OLLAMA_URL`
  - `OLLAMA_TEXT_MODEL`
  - `OLLAMA_VISION_MODEL`
  - `OLLAMA_REASONING_MODEL`
  - `OLLAMA_TIMEOUT`
  
- Добавлены настройки OpenRouter:
  - `OPENROUTER_API_KEY` - API ключ (обязательно)
  - `OPENROUTER_BASE_URL` - базовый URL API
  - `OPENROUTER_TEXT_MODEL` - модель для текста
  - `OPENROUTER_VISION_MODEL` - модель для изображений
  - `OPENROUTER_REASONING_MODEL` - модель для reasoning
  - `OPENROUTER_TIMEOUT` - таймаут запросов

#### AI Service (`bot/services/ai_service.py`)
- Заменен `OllamaClient` на `OpenRouterClient`
- Обновлены все методы для работы с OpenRouter API
- Сохранена обратная совместимость интерфейса

#### Handlers
Обновлены все handlers, использующие AI:
- `bot/handlers/verification.py` - верификация через OpenRouter
- `bot/handlers/swipe.py` - матчинг через OpenRouter
- `bot/handlers/chat.py` - подсказки для чата через OpenRouter
- `bot/handlers/profile.py` - улучшение профиля через OpenRouter

#### Environment Variables (`.env.example`)
- Удалены переменные Ollama
- Добавлены переменные OpenRouter
- Обновлены комментарии и примеры

#### README.md
- Обновлена секция "Настройка AI"
- Добавлена информация об OpenRouter
- Обновлены инструкции по развертыванию
- Добавлена таблица сравнения OpenRouter vs Ollama

#### Tests
- Переименован `test_ollama_integration.py` → `test_openrouter_integration.py`
- Обновлены тесты для работы с OpenRouter API
- Добавлены тесты для обработки ошибок API

### 🗑️ Удалено

- `bot/ollama_client.py` - заменен на `openrouter_client.py`
- Зависимость от локального Ollama сервера
- Требование GPU для работы AI функций

### 🔧 Технические детали

#### OpenRouter Client
```python
class OpenRouterClient:
    - Асинхронный HTTP клиент
    - Retry логика с exponential backoff
    - Поддержка text и vision моделей
    - Автоматическая обработка ошибок
    - Health check endpoint
```

#### Используемые модели (бесплатные)
- **Text**: `meta-llama/llama-3.2-3b-instruct:free`
- **Vision**: `meta-llama/llama-3.2-11b-vision-instruct:free`
- **Reasoning**: `meta-llama/llama-3.2-3b-instruct:free`

#### API Endpoints
- `POST /chat/completions` - генерация текста
- `POST /chat/completions` (с images) - анализ изображений
- `GET /models` - список доступных моделей

### 📊 Сравнение производительности

| Метрика | Ollama (локально) | OpenRouter |
|---------|-------------------|------------|
| Время первого запроса | ~1-2 сек | ~2-5 сек |
| Время последующих | ~0.5-1 сек | ~1-3 сек |
| Требования RAM | 8-32 GB | 0 GB |
| Требования GPU | Желательно | Не требуется |
| Требования диска | 10-50 GB | 0 GB |
| Стоимость | Бесплатно | Бесплатный tier |

### 🔐 Безопасность

- API ключ передается через заголовок `Authorization`
- Поддержка `HTTP-Referer` для идентификации приложения
- Все запросы через HTTPS
- Данные не сохраняются на серверах OpenRouter (согласно политике)

### 📝 Миграция

Для миграции существующего проекта:

1. Получите API ключ на https://openrouter.ai/keys
2. Обновите `.env`:
   ```env
   OPENROUTER_API_KEY=sk-or-v1-your-key
   ```
3. Удалите старые переменные Ollama
4. Перезапустите бота

Подробнее: [MIGRATION_TO_OPENROUTER.md](MIGRATION_TO_OPENROUTER.md)

### 🐛 Известные проблемы

- Vision модели могут быть медленнее локального Ollama
- Зависимость от интернет-соединения
- Лимиты бесплатного тарифа (~100k токенов/день)

### 🔮 Планы на будущее

- [ ] Добавить fallback на другие AI провайдеры
- [ ] Реализовать кэширование AI ответов
- [ ] Добавить мониторинг использования API
- [ ] Оптимизировать промпты для экономии токенов
- [ ] Добавить поддержку streaming ответов

### 💡 Рекомендации

**Для production:**
1. Настройте мониторинг использования API
2. Реализуйте rate limiting на уровне приложения
3. Используйте кэширование для частых запросов
4. Рассмотрите платный тариф для больших нагрузок

**Для development:**
1. Используйте бесплатный tier OpenRouter
2. Тестируйте с mock данными где возможно
3. Следите за лимитами на https://openrouter.ai/activity

### 📚 Дополнительные ресурсы

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter Pricing](https://openrouter.ai/docs/pricing)
- [Meta Llama 3.2](https://ai.meta.com/blog/llama-3-2-connect-2024-vision-edge-mobile-devices/)

---

**Версия:** 2.0.0  
**Дата:** 2024-XX-XX  
**Автор:** UltraDating Team
