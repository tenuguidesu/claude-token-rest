"""
~/.claude/projects/ 以下の .jsonl 変更を監視し、コールバックを呼ぶ。
デバウンス 1 秒でバースト書き込みをまとめる。
"""

import threading
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

WATCH_DIR = Path.home() / ".claude" / "projects"


class _Handler(FileSystemEventHandler):
    def __init__(self, cb: Callable[[], None]) -> None:
        self._cb = cb
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def _trigger(self) -> None:
        with self._lock:
            if self._timer:
                self._timer.cancel()
            self._timer = threading.Timer(1.0, self._cb)
            self._timer.daemon = True
            self._timer.start()

    def on_modified(self, event) -> None:
        if not event.is_directory and event.src_path.endswith(".jsonl"):
            self._trigger()

    def on_created(self, event) -> None:
        if not event.is_directory and event.src_path.endswith(".jsonl"):
            self._trigger()


def start(callback: Callable[[], None]) -> Observer:
    WATCH_DIR.mkdir(parents=True, exist_ok=True)
    handler = _Handler(callback)
    observer = Observer()
    observer.schedule(handler, str(WATCH_DIR), recursive=True)
    observer.daemon = True
    observer.start()
    return observer
