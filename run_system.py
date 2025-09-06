#!/usr/bin/env python3
"""
Универсальный скрипт для запуска RAG Template системы.

Позволяет запустить backend (fake или реальный) и frontend одновременно.

Usage:
    python run_system.py [--backend fake|real] [--ui-port PORT] [--no-browser]
"""

import argparse
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path


class SystemRunner:
    """Класс для управления запуском системы."""

    def __init__(self):
        self.backend_process = None
        self.ui_process = None
        self.running = True

    def run_backend(self, backend_type="fake"):
        """
        Запускает backend сервер.

        Parameters
        ----------
        backend_type : str
            Тип backend'а: 'fake' или 'real'
        """
        try:
            if backend_type == "fake":
                print("🔧 Запуск fake backend...")
                backend_script = Path("src/services/api_gateway/fake_backend.py")
                if not backend_script.exists():
                    print(f"❌ Файл {backend_script} не найден!")
                    return False

                self.backend_process = subprocess.Popen(
                    [sys.executable, str(backend_script)]
                )
            else:
                print("🔧 Запуск реального API Gateway...")
                main_script = Path("src/services/api_gateway/main.py")
                if not main_script.exists():
                    print(f"❌ Файл {main_script} не найден!")
                    return False

                self.backend_process = subprocess.Popen(
                    [sys.executable, str(main_script)]
                )

            # Даем время backend'у запуститься
            print("⏳ Ожидание запуска backend...")
            time.sleep(3)

            # Проверяем, что процесс запустился
            if self.backend_process.poll() is None:
                print("✅ Backend запущен успешно")
                return True
            else:
                print("❌ Ошибка запуска backend")
                return False

        except Exception as e:
            print(f"❌ Ошибка при запуске backend: {e}")
            return False

    def run_ui(self, port=3000, no_browser=False):
        """
        Запускает UI сервер.

        Parameters
        ----------
        port : int
            Порт для UI сервера
        no_browser : bool
            Не открывать браузер автоматически
        """
        try:
            ui_path = Path("src/services/ui")
            if not ui_path.exists():
                print(f"❌ Папка {ui_path} не найдена!")
                return False

            print(f"🎨 Запуск UI на порту {port}...")

            self.ui_process = subprocess.Popen(
                [sys.executable, "-m", "http.server", str(port)], cwd=ui_path
            )

            # Даем время UI запуститься
            time.sleep(2)

            # Открываем браузер
            if not no_browser:
                try:
                    webbrowser.open(f"http://localhost:{port}")
                except Exception as e:
                    print(f"⚠️  Не удалось открыть браузер: {e}")

            # Проверяем, что процесс запустился
            if self.ui_process.poll() is None:
                print("✅ UI запущен успешно")
                return True
            else:
                print("❌ Ошибка запуска UI")
                return False

        except Exception as e:
            print(f"❌ Ошибка при запуске UI: {e}")
            return False

    def stop_all(self):
        """Останавливает все процессы."""
        print("\n🛑 Остановка системы...")
        self.running = False

        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
                print("✅ Backend остановлен")
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
                print("⚡ Backend принудительно завершен")
            except Exception as e:
                print(f"⚠️  Ошибка при остановке backend: {e}")

        if self.ui_process:
            try:
                self.ui_process.terminate()
                self.ui_process.wait(timeout=5)
                print("✅ UI остановлен")
            except subprocess.TimeoutExpired:
                self.ui_process.kill()
                print("⚡ UI принудительно завершен")
            except Exception as e:
                print(f"⚠️  Ошибка при остановке UI: {e}")

    def monitor_processes(self):
        """Мониторинг процессов."""
        while self.running:
            try:
                # Проверяем backend
                if self.backend_process and self.backend_process.poll() is not None:
                    print("❌ Backend процесс завершился неожиданно")
                    self.running = False
                    break

                # Проверяем UI
                if self.ui_process and self.ui_process.poll() is not None:
                    print("❌ UI процесс завершился неожиданно")
                    self.running = False
                    break

                time.sleep(1)

            except KeyboardInterrupt:
                break


def main():
    """Основная функция запуска системы."""
    parser = argparse.ArgumentParser(description="Запуск RAG Template системы")
    parser.add_argument(
        "--backend",
        choices=["fake", "real"],
        default="fake",
        help="Тип backend'а: fake (для тестирования) или real (API Gateway)",
    )
    parser.add_argument(
        "--ui-port",
        type=int,
        default=3000,
        help="Порт для UI сервера (по умолчанию: 3000)",
    )
    parser.add_argument(
        "--no-browser", action="store_true", help="Не открывать браузер автоматически"
    )
    parser.add_argument(
        "--backend-only", action="store_true", help="Запустить только backend"
    )
    parser.add_argument("--ui-only", action="store_true", help="Запустить только UI")

    args = parser.parse_args()

    runner = SystemRunner()

    try:
        print("🚀 Запуск RAG Template системы")
        print("=" * 50)

        success = True

        # Запуск backend
        if not args.ui_only:
            success &= runner.run_backend(args.backend)

        # Запуск UI
        if not args.backend_only and success:
            success &= runner.run_ui(args.ui_port, args.no_browser)

        if not success:
            print("❌ Не удалось запустить систему")
            sys.exit(1)

        print("\n" + "=" * 50)
        print("🎉 Система запущена успешно!")
        print(f"🔧 Backend: http://localhost:8080 ({args.backend})")
        if not args.backend_only:
            print(f"🎨 Frontend: http://localhost:{args.ui_port}")
        print("\n💡 Для остановки нажмите Ctrl+C")
        print("=" * 50)

        # Мониторинг процессов
        monitor_thread = threading.Thread(target=runner.monitor_processes)
        monitor_thread.daemon = True
        monitor_thread.start()

        # Ожидание завершения
        try:
            while runner.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    except KeyboardInterrupt:
        pass
    finally:
        runner.stop_all()
        print("\n👋 Система остановлена")


if __name__ == "__main__":
    main()
