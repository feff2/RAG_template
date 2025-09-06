#!/usr/bin/env python3
"""
Скрипт для запуска фронтенда (UI) на локальном HTTP сервере.

Usage:
    python run_ui.py [--port PORT]
"""

import argparse
import subprocess
import sys
import webbrowser
from pathlib import Path


def main() -> None:
    """
    Запускает HTTP сервер для фронтенда.
    """
    parser = argparse.ArgumentParser(description="Запуск фронтенда RAG Template")
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Порт для HTTP сервера (по умолчанию: 3000)",
    )
    parser.add_argument(
        "--no-browser", action="store_true", help="Не открывать браузер автоматически"
    )

    args = parser.parse_args()

    # Путь к UI директории
    ui_path = Path("src/services/ui")

    if not ui_path.exists():
        print(f"❌ Папка {ui_path} не найдена!")
        sys.exit(1)

    index_file = ui_path / "index.html"
    if not index_file.exists():
        print(f"❌ Файл {index_file} не найден!")
        sys.exit(1)

    print("🚀 Запуск фронтенда...")
    print(f"📁 Директория: {ui_path}")
    print(f"🌐 URL: http://localhost:{args.port}")
    print("\n💡 Для остановки нажмите Ctrl+C")
    print("📋 Убедитесь, что backend запущен на http://localhost:8080\n")

    # Открытие браузера
    if not args.no_browser:
        try:
            webbrowser.open(f"http://localhost:{args.port}")
        except Exception as e:
            print(f"⚠️  Не удалось открыть браузер: {e}")

    try:
        # Запуск HTTP сервера
        subprocess.run(
            [sys.executable, "-m", "http.server", str(args.port)],
            cwd=ui_path,
            check=True,
        )

    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен пользователем")
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка запуска сервера: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
