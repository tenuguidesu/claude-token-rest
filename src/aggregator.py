"""
~/.claude/projects/**/*.jsonl からトークン使用量を集計する。
各行は message.usage + timestamp を持つ assistant ターン。
"""

import glob
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
PROJECTS_DIR = CLAUDE_DIR / "projects"
SESSIONS_DIR = CLAUDE_DIR / "sessions"


@dataclass
class Usage:
    input: int = 0
    cache_create: int = 0
    cache_read: int = 0
    output: int = 0

    @property
    def total(self) -> int:
        return self.input + self.cache_create + self.cache_read + self.output


@dataclass
class Snapshot:
    five_hour: Usage = field(default_factory=Usage)
    seven_day: Usage = field(default_factory=Usage)
    session: Usage = field(default_factory=Usage)
    session_id: str = ""
    session_started: datetime | None = None


def _parse_file(path: Path) -> list[tuple[datetime, dict, str]]:
    """(timestamp, usage_dict, session_id) のリストを返す。"""
    results = []
    try:
        with open(path, encoding="utf-8") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    d = json.loads(raw)
                    usage = d.get("message", {}).get("usage")
                    ts_str = d.get("timestamp")
                    sid = d.get("sessionId", "")
                    if usage and ts_str:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        results.append((ts, usage, sid))
                except (json.JSONDecodeError, ValueError):
                    pass
    except OSError:
        pass
    return results


def _latest_session_id() -> tuple[str, datetime | None]:
    """最新の Claude Code セッション ID を返す。"""
    best_sid = ""
    best_ts: datetime | None = None
    try:
        for p in SESSIONS_DIR.glob("*.json"):
            try:
                with open(p) as f:
                    d = json.load(f)
                raw = d.get("updatedAt") or d.get("startedAt")
                if raw is None:
                    continue
                # updatedAt は Unix ミリ秒（int）または ISO 文字列のどちらかが返る
                if isinstance(raw, (int, float)):
                    ts = datetime.fromtimestamp(raw / 1000, tz=timezone.utc)
                else:
                    ts = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
                if best_ts is None or ts > best_ts:
                    best_ts = ts
                    best_sid = d.get("sessionId", "")
            except Exception:
                pass
    except OSError:
        pass
    return best_sid, best_ts


def collect() -> Snapshot:
    now = datetime.now(timezone.utc)
    cutoff_5h = now.timestamp() - 5 * 3600
    cutoff_7d = now.timestamp() - 7 * 86400

    snap = Snapshot()
    snap.session_id, snap.session_started = _latest_session_id()

    pattern = str(PROJECTS_DIR / "**" / "*.jsonl")
    for path_str in glob.glob(pattern, recursive=True):
        for ts, u, sid in _parse_file(Path(path_str)):
            ts_unix = ts.timestamp()

            def _add(target: Usage) -> None:
                target.input        += u.get("input_tokens", 0)
                target.cache_create += u.get("cache_creation_input_tokens", 0)
                target.cache_read   += u.get("cache_read_input_tokens", 0)
                target.output       += u.get("output_tokens", 0)

            if ts_unix >= cutoff_5h:
                _add(snap.five_hour)
            if ts_unix >= cutoff_7d:
                _add(snap.seven_day)
            if sid and sid == snap.session_id:
                _add(snap.session)

    return snap
