# RAG Template UI

Минималистичный фронтенд для Q&A системы в стиле DeepSeek с системой рейтинга.

## Структура

```
src/services/ui/
├── index.html          # Основная HTML страница
├── styles.css          # CSS стили интерфейса
├── script.js           # JavaScript логика приложения
├── media/
│   └── roseltorg_logo.png  # Логотип (требует замены на реальный файл)
└── README.md           # Данная документация
```

## Запуск

### 1. Запуск backend

```bash
# Fake backend для тестирования
python run_fake_backend.py

# Или реальный API Gateway
cd src/services/api_gateway
python main.py
```

Backend будет доступен на `http://localhost:8080`

### 2. Запуск фронтенда

Откройте файл `src/services/ui/index.html` в браузере или используйте локальный HTTP сервер:

```bash
# Python 3
cd src/services/ui
python -m http.server 3000

# Node.js (если установлен)
cd src/services/ui
npx http-server -p 3000
```

Фронтенд будет доступен на `http://localhost:3000`

## Особенности

### Дизайн
- Минималистичный интерфейс в стиле DeepSeek
- Градиентный фон: #2966e7 → #274d99
- Белый чат с черным текстом
- Шрифт: "Exo 2", "Open Sans", Arial, Helvetica, sans-serif

### Функциональность
- Отправка сообщений (Enter или кнопка)
- Автоматическое изменение размера поля ввода
- Обработка и отображение ссылок
- Кнопка Reset для очистки чата
- UUID для каждого пользователя
- Индикатор загрузки при обработке запроса
- **Система рейтинга**: оценка ответов от 1 до 5 звезд

### Технические детали
- Нативный JavaScript (без фреймворков)
- Адаптивный дизайн
- CORS настроен для работы с localhost:8080
- Обработка ошибок API
- Интеграция с API рейтинга

## API Endpoints

- `POST /api/v1/query` - основной чат
- `POST /api/v1/rating` - отправка рейтинга

## Настройка логотипа

Замените файл `media/roseltorg_logo.png` на реальный логотип:
- Рекомендуемая высота: 60px
- Формат: PNG с прозрачным фоном
