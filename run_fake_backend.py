#!/usr/bin/env python3
"""
Скрипт для запуска fake backend сервера для тестирования фронтенда.

Usage:
    python run_fake_backend.py
"""

import subprocess
import sys
from pathlib import Path


def main():
    """
    Запускает fake backend сервер.
    """
    # Путь к fake backend файлу
    fake_backend_path = Path("src/services/api_gateway/fake_backend.py")

    if not fake_backend_path.exists():
        print(f"❌ Файл {fake_backend_path} не найден!")
        sys.exit(1)

    print("🚀 Запуск fake backend сервера...")
    print(f"📁 Файл: {fake_backend_path}")
    print("🌐 URL: http://localhost:8080")
    print("📖 API Docs: http://localhost:8080/api/docs")
    print("\n💡 Для остановки нажмите Ctrl+C\n")

    try:
        # Запуск fake backend
        subprocess.run([sys.executable, str(fake_backend_path)], check=True)
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
