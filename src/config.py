import json
from pathlib import Path

CONFIG_FILE = Path.home() / ".claude-token-rest" / "config.json"

PLANS = {
    "pro":    {"label": "Pro (1x)",    "mul": 1},
    "max5":   {"label": "Max (5x)",    "mul": 5},
    "max20":  {"label": "Max (20x)",   "mul": 20},
    "custom": {"label": "カスタム",    "mul": None},
}

# Anthropic 非公開のため推定値。UI 上で「推定」と明示して使用する
BASE_5H = 50_000
BASE_7D = 500_000

DEFAULTS = {
    "plan":       "pro",
    "custom_5h":  50_000,
    "custom_7d":  500_000,
    "warn_pct":   30,
    "danger_pct": 10,
}


def load() -> dict:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                return {**DEFAULTS, **json.load(f)}
        except Exception:
            pass
    return DEFAULTS.copy()


def save(cfg: dict) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def limits(cfg: dict) -> tuple[int, int]:
    plan = cfg.get("plan", "pro")
    if plan == "custom":
        return cfg.get("custom_5h", BASE_5H), cfg.get("custom_7d", BASE_7D)
    mul = PLANS.get(plan, PLANS["pro"])["mul"]
    return BASE_5H * mul, BASE_7D * mul
