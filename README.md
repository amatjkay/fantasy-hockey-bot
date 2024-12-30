# Fantasy Hockey Bot

Телеграм-бот для отслеживания статистики фэнтези-хоккея. Бот собирает данные о лучших игроках дня и недели из ESPN Fantasy Hockey, создает коллажи с их фотографиями и отправляет в Telegram.

## Основные функции

- Ежедневные отчеты о лучших игроках (команда дня)
- Еженедельные сводки команд (команда недели)
- Автоматическое определение дат недели (понедельник-воскресенье)
- Кэширование изображений игроков для оптимизации производительности
- Система грейдов игроков на основе частоты попадания в команду дня
- Поддержка часовых поясов (синхронизация с ESPN)
- Автоматическая обработка пропущенных дней

## Структура проекта

```
fantasy-hockey-bot/
├── data/
│   ├── cache/              # Кэшированные изображения игроков
│   ├── processed/          # Обработанные данные статистики
│   └── temp/              # Временные файлы (коллажи)
├── logs/                  # Логи приложения
├── scripts/
│   ├── app_day.py        # Скрипт обработки дневной статистики
│   └── app_week.py       # Скрипт обработки недельной статистики
└── src/
    ├── config/           # Конфигурационные файлы
    └── utils/            # Вспомогательные функции
```

## Настройка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/fantasy-hockey-bot.git
cd fantasy-hockey-bot
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` в корневой директории и добавьте необходимые переменные окружения:
```
TELEGRAM_TOKEN=your_telegram_bot_token
CHAT_ID=your_telegram_chat_id
DAY_START_HOUR=4  # Час начала нового дня по времени ESPN (default: 4)
```

4. Создайте необходимые директории:
```bash
mkdir -p data/{cache,processed,temp} logs
```

## Использование

### Дневная статистика (app_day.py)

- Обработка последнего дня:
```bash
python3 scripts/app_day.py
```

- Обработка конкретной даты:
```bash
python3 scripts/app_day.py --date YYYY-MM-DD
```

- Обработка всех дней с начала сезона:
```bash
python3 scripts/app_day.py --all-weeks
```

- Принудительный пересчет статистики:
```bash
python3 scripts/app_day.py --force
```

### Недельная статистика (app_week.py)

- Обработка последней завершенной недели:
```bash
python3 scripts/app_week.py
```

- Обработка всех недель с начала сезона:
```bash
python3 scripts/app_week.py --all-weeks
```

- Принудительный пересчет недельной статистики:
```bash
python3 scripts/app_week.py --force
```

## Система грейдов

Игроки получают грейды в зависимости от частоты попадания в команду дня:
- common (1 раз) - черный цвет
- uncommon (2 раза) - зеленый цвет
- rare (3 раза) - синий цвет
- epic (4 раза) - фиолетовый цвет
- legend (5+ раз) - оранжевый цвет

## Требования

- Python 3.8+
- Необходимые библиотеки:
  - python-telegram-bot
  - requests
  - Pillow
  - python-dotenv
  - pytz
- Telegram Bot API Token
- Доступ к ESPN Fantasy Hockey API

## Логирование

Все действия бота логируются в `logs/app/log.txt`. Логи включают:
- Информацию о запросах к API
- Результаты обработки статистики
- Ошибки и предупреждения
- Статус отправки сообщений

## Последние изменения

- Добавлена возможность обработки конкретной даты через флаг --date
- Улучшена логика обработки пропущенных дней
- Оптимизирована работа с часовыми поясами
- Добавлена дополнительная проверка дат при обработке статистики
- Добавлено кэширование изображений игроков для ускорения работы
- Исправлен расчет дат недели (теперь корректно с понедельника по воскресенье)
- Улучшена система логирования
- Оптимизирована структура проекта
- Добавлены флаги для гибкого управления обработкой данных
- Реализована система грейдов игроков
- Добавлена обработка ошибок сети и повторные попытки

## Известные проблемы

- При отсутствии изображения игрока используется серый placeholder
- Возможны задержки при первом запуске из-за загрузки изображений
- API ESPN может иметь ограничения на количество запросов

## Лицензия

MIT License
