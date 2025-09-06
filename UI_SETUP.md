 RAG Template - Быстрый старт UI

## 🚀 Запуск системы одной командой

```bash
# Запуск fake backend + UI
python run_system.py

# Запуск реального API Gateway + UI
python run_system.py --backend real
```

Система автоматически откроется в браузере:
- **Backend**: http://localhost:8080
- **Frontend**: http://localhost:3000

## 📁 Структура UI

```
src/services/ui/
├── index.html      # Главная страница
├── styles.css      # Стили DeepSeek
├── script.js       # Логика чата + рейтинг
└── media/          # Медиафайлы
```

## 🛠️ Дополнительные команды

```bash
# Только backend
python run_system.py --backend-only

# Только UI
python run_ui.py

# UI на другом порту
python run_ui.py --port 8000
```

## ⭐ Функции

- ✅ Минималистичный дизайн в стиле DeepSeek
- ✅ Чат с Q&A системой
- ✅ Система рейтинга от 1 до 5 звезд (🔘/🔵)
- ✅ Обработка ссылок в ответах
- ✅ Адаптивный дизайн
- ✅ Кнопка Reset для очистки чата

## 🔧 API

- `POST /api/v1/query` - отправка вопроса
- `POST /api/v1/rating` - отправка оценки

Подробная документация в [FRONTEND_SETUP.md](FRONTEND_SETUP.md)
