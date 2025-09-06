#!/usr/bin/env python3
# minimal_openrouter_chat_retry.py
import os, sys, json, time, random, argparse, requests
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from dotenv import load_dotenv
from tqdm.auto import tqdm

load_dotenv() 

def parse_retry_wait(resp, default=1.0, max_wait=30.0):
    """Определяем, сколько подождать перед повтором."""
    ra = resp.headers.get("Retry-After")
    if ra:
        # Retry-After может быть секундами или HTTP-датой
        try:
            return max(0.0, min(float(ra), max_wait))
        except ValueError:
            try:
                dt = parsedate_to_datetime(ra)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return min(max_wait, max(0.0, (dt - datetime.now(timezone.utc)).total_seconds()))
            except Exception:
                pass

    # Иногда встречаются сбросы лимита в других заголовках
    for key in ("RateLimit-Reset", "X-RateLimit-Reset"):
        v = resp.headers.get(key)
        if v:
            try:
                # трактуем как "секунд до сброса"
                return max(0.0, min(float(v), max_wait))
            except Exception:
                # или как unix-время
                try:
                    ts = float(v)
                    wait = ts - time.time()
                    if wait > 0:
                        return min(wait, max_wait)
                except Exception:
                    pass

    # запасной вариант
    return default + random.random()

def call_openrouter(query: str, model: str, base_url: str, headers: dict,
                    max_retries: int = 6) -> str:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": query}],
        # можете уменьшить расход токенов:
        # "max_tokens": 512
    }

    backoff = 1.0
    for attempt in range(1, max_retries + 1):
        resp = requests.post(base_url, headers=headers, json=payload, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            return (data.get("choices") or [{}])[0].get("message", {}).get("content", "") \
                   or json.dumps(data, ensure_ascii=False, indent=2)

        if resp.status_code in (429, 503, 529):
            wait = parse_retry_wait(resp, default=backoff)
            wait *= random.uniform(0.8, 1.2)  # джиттер
            if attempt == max_retries:
                raise requests.HTTPError(
                    f"{resp.status_code} {resp.reason} after {attempt} attempts; body={resp.text}"
                )
            time.sleep(wait)
            backoff = min(backoff * 2, 30.0)
            continue

        # любые другие ошибки — сразу исключение
        resp.raise_for_status()

    raise RuntimeError("Unreachable")

def main():
    ap = argparse.ArgumentParser(description="Запрос к OpenRouter с ретраями")
    ap.add_argument("-q", "--query", required=True, help="Текст запроса")
    ap.add_argument("-m", "--model", default="qwen/qwq-32b:free", help="ID модели")
    ap.add_argument("--base-url", default="https://openrouter.ai/api/v1/chat/completions",
                    help="Базовый URL OpenRouter")
    args = ap.parse_args()

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Ошибка: установите OPENROUTER_API_KEY", file=sys.stderr)
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        # Рекомендуется указывать реферер/титул для идентификации приложения
        "HTTP-Referer": "https://local-script",
        "X-Title": "Minimal-OpenRouter-Client",
    }

    try:
        out = call_openrouter(args.query, args.model, args.base_url, headers)
        print(out)
    except requests.HTTPError as e:
        print(f"HTTP error: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(3)

if __name__ == "__main__":
    main()
