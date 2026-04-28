# Миграция с Ollama на OpenRouter

## Что изменилось

Бот теперь использует **OpenRouter API** вместо локального Ollama. Это дает следующие преимущества:

✅ Не требуется локальная установка и настройка Ollama  
✅ Не нужно скачивать большие модели (десятки GB)  
✅ Доступ к бесплатным моделям Meta Llama  
✅ Быстрый старт - только API ключ  
✅ Автоматические обновления моделей  

## Шаги миграции

### 1. Получите API ключ OpenRouter

1. Зарегистрируйтесь на https://openrouter.ai/
2. Перейдите в https://openrouter.ai/keys
3. Создайте новый API ключ
4. Скопируйте ключ (показывается только один раз!)

### 2. Обновите .env файл

Замените старые настройки Ollama:

```env
# СТАРЫЕ НАСТРОЙКИ (удалите)
# OLLAMA_URL=http://localhost:11434
# OLLAMA_TEXT_MODEL=qwen3:32b
# OLLAMA_VISION_MODEL=qwen3-vl:7b
# OLLAMA_REASONING_MODEL=deepseek-r1:14b
# OLLAMA_TIMEOUT=30
```

На новые настройки OpenRouter:

```env
# НОВЫЕ НАСТРОЙКИ
OPENROUTER_API_KEY=sk-or-v1-ваш-ключ-здесь
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_TEXT_MODEL=meta-llama/llama-3.2-3b-instruct:free
OPENROUTER_VISION_MODEL=meta-llama/llama-3.2-11b-vision-instruct:free
OPENROUTER_REASONING_MODEL=meta-llama/llama-3.2-3b-instruct:free
OPENROUTER_TIMEOUT=60
```

### 3. Удалите Ollama (опционально)

Если вы больше не используете Ollama:

```bash
# Linux/Mac
sudo systemctl stop ollama
sudo systemctl disable ollama

# Windows
# Удалите через "Установка и удаление программ"
```

### 4. Перезапустите бота

```bash
# Остановите бота
# Ctrl+C или kill процесс

# Запустите снова
python -m bot.main
```

## Изменения в коде

Все изменения уже внесены в код:

- ✅ `bot/openrouter_client.py` - новый клиент для OpenRouter
- ✅ `bot/config.py` - обновлены настройки
- ✅ `bot/services/ai_service.py` - использует OpenRouterClient
- ✅ Все handlers обновлены
- ✅ `.env.example` обновлен

## Сравнение производительности

| Параметр | Ollama (локально) | OpenRouter |
|----------|-------------------|------------|
| Скорость первого запроса | Быстро (локально) | Зависит от сети |
| Скорость последующих | Очень быстро | Средне |
| Требования к железу | Высокие (GPU желательно) | Нет |
| Требования к диску | 10-50 GB на модель | Нет |
| Стоимость | Бесплатно | Бесплатный tier + платные модели |
| Приватность | 100% локально | Данные на сервере |

## Бесплатные лимиты OpenRouter

- **Запросы в минуту**: ~20-30 (зависит от модели)
- **Токены в день**: ~100,000
- **Модели**: Только с пометкой `:free`

Для большинства ботов этого достаточно. Если нужно больше - пополните баланс.

## Откат на Ollama

Если нужно вернуться на Ollama:

1. Установите Ollama: https://ollama.ai/download
2. Скачайте модели:
   ```bash
   ollama pull qwen3:32b
   ollama pull qwen3-vl:7b
   ollama pull deepseek-r1:14b
   ```
3. Восстановите старый код из git:
   ```bash
   git checkout HEAD~1 -- bot/ollama_client.py
   git checkout HEAD~1 -- bot/config.py
   git checkout HEAD~1 -- bot/services/ai_service.py
   ```
4. Обновите .env с настройками Ollama

## Поддержка

Если возникли проблемы:

1. Проверьте API ключ на https://openrouter.ai/keys
2. Посмотрите логи бота на наличие ошибок
3. Проверьте использование на https://openrouter.ai/activity
4. Прочитайте OPENROUTER_SETUP.md для подробностей

## FAQ

**Q: Можно ли использовать оба варианта одновременно?**  
A: Нет, нужно выбрать один. Рекомендуется OpenRouter для простоты.

**Q: Безопасно ли отправлять данные пользователей в OpenRouter?**  
A: OpenRouter не сохраняет данные запросов. Но для максимальной приватности используйте Ollama локально.

**Q: Что делать если закончились бесплатные лимиты?**  
A: Пополните баланс на https://openrouter.ai/credits или оптимизируйте использование (кэширование, меньше запросов).

**Q: Можно ли использовать другие модели?**  
A: Да! Смотрите список на https://openrouter.ai/models - выбирайте модели с `:free` для бесплатного использования.
