#!/usr/bin/env python3
"""Простой замер скорости скачивания.

Делает N последовательных GET-запросов к указанному URL, полностью
дочитывает каждый ответ и выводит среднее время запроса, общий объём
скачанных данных и среднюю скорость скачивания в Мбит/с.

Только стандартная библиотека Python (3.7+).
"""

import argparse
import sys
import time
import urllib.error
import urllib.request

CHUNK_SIZE = 64 * 1024
USER_AGENT = "simple-speedtest/1.0"


def fetch(url, timeout):
    """Скачивает URL целиком. Возвращает (байт скачано, секунд затрачено)."""
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            # Не даём кэшам отдать ответ без реального скачивания.
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            # Просим не сжимать, чтобы считать реальные байты по сети = байты тела.
            "Accept-Encoding": "identity",
        },
    )
    start = time.perf_counter()
    total = 0
    with urllib.request.urlopen(request, timeout=timeout) as response:
        while True:
            chunk = response.read(CHUNK_SIZE)
            if not chunk:
                break
            total += len(chunk)
    elapsed = time.perf_counter() - start
    return total, elapsed


def format_bytes(num):
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if num < 1024 or unit == "ГБ":
            return f"{num:.2f} {unit}" if unit != "Б" else f"{num} {unit}"
        num /= 1024


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Замер скорости скачивания: N последовательных запросов к URL."
    )
    parser.add_argument("url", help="адрес для скачивания (например, большая картинка)")
    parser.add_argument(
        "-n", "--requests", type=int, default=10,
        help="количество запросов (по умолчанию 10)",
    )
    parser.add_argument(
        "-t", "--timeout", type=float, default=30.0,
        help="таймаут одного запроса в секундах (по умолчанию 30)",
    )
    args = parser.parse_args(argv)
    if args.requests < 1:
        parser.error("--requests должно быть >= 1")
    if not args.url.startswith(("http://", "https://")):
        parser.error("URL должен начинаться с http:// или https://")
    return args


def main(argv=None):
    args = parse_args(argv)
    print(f"URL: {args.url}")
    print(f"Запросов: {args.requests}\n")

    total_bytes = 0
    total_time = 0.0
    successes = 0

    for i in range(1, args.requests + 1):
        try:
            size, elapsed = fetch(args.url, args.timeout)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            reason = getattr(exc, "reason", exc)
            print(f"  #{i:>2}: ошибка — {reason}")
            continue
        successes += 1
        total_bytes += size
        total_time += elapsed
        speed = size * 8 / elapsed / 1_000_000 if elapsed > 0 else 0.0
        print(f"  #{i:>2}: {format_bytes(size):>12}  {elapsed * 1000:9.1f} мс  {speed:8.2f} Мбит/с")

    print()
    if successes == 0:
        print("Ни один запрос не завершился успешно.")
        return 1

    avg_time = total_time / successes
    speed_mbps = total_bytes * 8 / total_time / 1_000_000 if total_time > 0 else 0.0

    print(f"Успешных запросов:      {successes} из {args.requests}")
    print(f"Среднее время запроса:  {avg_time * 1000:.1f} мс")
    print(f"Всего скачано:          {format_bytes(total_bytes)} ({total_bytes} байт)")
    print(f"Скорость скачивания:    {speed_mbps:.2f} Мбит/с ({speed_mbps / 8:.2f} МБ/с)")
    return 0 if successes == args.requests else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nПрервано.")
        sys.exit(130)
