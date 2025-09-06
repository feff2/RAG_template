# RAG Template - Настройка Frontend и Fake Backend

## Обзор

Создан минималистичный фронтенд для Q&A системы в стиле DeepSeek с fake backend для тестирования. Добавлена система оценки ответов от 1 до 5 звезд.

## Структура созданных файлов

```
RAG_template/
├── src/services/
│   ├── ui/                            # Фронтенд приложения
│   │   ├── index.html                 # Основная HTML страница
│   │   ├── styles.css                 # CSS стили (DeepSeek дизайн + рейтинг)
│   │   ├── script.js                  # JavaScript логика + рейтинг
│   │   ├── media/
│   │   │   └── roseltorg_logo.png     # Заглушка логотипа (требует замены)
│   │   └── README.md                  # Документация UI
│   └── api_gateway/
│       └── fake_backend.py            # Fake backend для тестирования + рейтинг API
├── run_fake_backend.py                # Скрипт запуска fake backend
├── run_ui.py                          # Скрипт запуска UI
├── run_system.py                      # Универсальный скрипт запуска системы
└── FRONTEND_SETUP.md                  # Данная документация
```

## Быстрый запуск

### 🚀 Универсальный запуск (рекомендуется)

```bash
# Запуск всей системы (fake backend + UI)
python run_system.py

# Запуск с реальным API Gateway
python run_system.py --backend real

# Запуск только backend
python run_system.py --backend-only

# Запуск только UI (если backend уже запущен)
python run_system.py --ui-only
```

### 🔧 Раздельный запуск

#### 1. Запуск backend

```bash
# Fake backend для тестирования
python run_fake_backend.py

# Или напрямую
cd src/services/api_gateway
python fake_backend.py

# Реальный API Gateway
cd src/services/api_gateway
python main.py
```

Backend будет доступен на: http://localhost:8080
API документация: http://localhost:8080/api/docs

#### 2. Запуск UI

```bash
# Простой запуск
python run_ui.py

# С кастомным портом
python run_ui.py --port 8000

# Без автоматического открытия браузера
python run_ui.py --no-browser
```

Или вручную:
```bash
cd src/services/ui
python -m http.server 3000
```

UI будет доступен на: http://localhost:3000

## Новая функциональность: Система рейтинга

### ✅ **Компонент оценки**:
- После каждого ответа ассистента появляется блок для оценки
- 5 звезд в виде эмодзи: 🔘 (пустая) и 🔵 (заполненная)
- Интерактивное наведение с подсветкой звезд
- Клик по звезде отправляет оценку на сервер
- После отправки блок становится неактивным с подтверждением

### ✅ **API интеграция**:
- Эндпоинт: `POST /api/v1/rating`
- Схема данных: `RatingIn` (request_id, history_session, rating, comment)
- Автоматическая связка rating с конкретным ответом через request_id
- Обработка ошибок с визуальной обратной связью

### ✅ **UX особенности**:
- Компактный дизайн блока рейтинга (маленькая высота, ширина сообщения)
- Плавные анимации при наведении
- Цветовая индикация состояний (обычное, отправлено, ошибка)
- Отключение интерактивности во время отправки

## Особенности реализации

### Fake Backend (`fake_backend.py`)
- ✅ Полная совместимость с API схемами основного сервиса
- ✅ Эндпоинт `POST /api/v1/query` с моделями `QueryIn`/`QueryOut`
- ✅ **НОВОЕ**: Эндпоинт `POST /api/v1/rating` с моделью `RatingIn`
- ✅ CORS настроен для работы с фронтендом
- ✅ Имитация задержки обработки запроса (1-3 сек)
- ✅ Случайные ответы с ссылками для демонстрации
- ✅ Полная документация в numpydoc стиле

### Frontend
- ✅ **Дизайн**: Точная копия стиля DeepSeek
  - Градиентный фон: #2966e7 → #274d99
  - Белый чат (#ffffff) с черным текстом (#000000)
  - Placeholder цвет: #81868f
  - Шрифт: "Exo 2", "Open Sans", Arial, Helvetica, sans-serif

- ✅ **Функциональность**:
  - Один чат без истории
  - Кнопка Reset для очистки
  - UUID пользователя (генерируется при загрузке)
  - Автоматическое изменение размера поля ввода
  - Обработка ссылок (markdown и обычные URL)
  - Индикатор загрузки с анимацией точек
  - Отправка по Enter или кнопке
  - **НОВОЕ**: Система оценки ответов от 1 до 5 звезд

- ✅ **Технические особенности**:
  - Нативный JavaScript (без фреймворков)
  - Адаптивный дизайн
  - JSDoc документация
  - Обработка ошибок API
  - Автоматическая прокрутка чата
  - **НОВОЕ**: Интеграция с API рейтинга

## Переключение на реальный backend

Когда будете готовы использовать реальный API Gateway:

1. Остановите fake backend (Ctrl+C)
2. Запустите основной API Gateway на порту 8080
3. Фронтенд автоматически начнет работать с реальным backend

**Никаких изменений в коде фронтенда не требуется!**

## Настройка логотипа

Замените файл `src/services/ui/media/roseltorg_logo.png` на реальный логотип:
- Рекомендуемая высота: 60px
- Формат: PNG с прозрачным фоном

## API Endpoints

Фронтенд использует следующие эндпоинты:

### Основной чат
```
POST /api/v1/query
Content-Type: application/json

{
    "request_id": "uuid-string",
    "query": "пользовательский вопрос"
}

Response:
{
    "request_id": "uuid-string",
    "response": "ответ системы"
}
```

### Рейтинг ответов
```
POST /api/v1/rating
Content-Type: application/json

{
    "request_id": "uuid-string",
    "history_session": "user-uuid",
    "rating": 1-5,
    "comment": "необязательный комментарий"
}

Response:
{
    "ok": true
}
```

## Требования

- Python 3.8+ (для fake backend)
- FastAPI, Pydantic, Uvicorn (для fake backend)
- Современный браузер (для фронтенда)

Фронтенд работает без дополнительных зависимостей - только нативные веб-технологии.
