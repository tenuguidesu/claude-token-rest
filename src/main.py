"""
Claude Token Rest — macOS メニューバーアプリ
~/.claude/projects/**/*.jsonl を解析してトークン残量を表示する。
"""

import sys
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

import rumps

sys.path.insert(0, str(Path(__file__).parent))

import aggregator
import config
import watcher

# ──────────────────────────────────────────────────────────────────────────────
# ヘルパー
# ──────────────────────────────────────────────────────────────────────────────

def _pct(used: int, limit: int) -> float:
    if limit <= 0:
        return 0.0
    return max(0.0, min(100.0, (1 - used / limit) * 100))


def _indicator(pct: float, warn: int, danger: int) -> str:
    if pct > warn:
        return "🟢"
    if pct > danger:
        return "🟡"
    return "🔴"


def _delta_str(seconds: float) -> str:
    if seconds <= 0:
        return "まもなく"
    h, rem = divmod(int(seconds), 3600)
    m = rem // 60
    if h > 0:
        return f"{h}h {m}m 後"
    return f"{m}m 後"


# ──────────────────────────────────────────────────────────────────────────────
# メニューバーアプリ
# ──────────────────────────────────────────────────────────────────────────────

class App(rumps.App):
    def __init__(self) -> None:
        super().__init__("⏳ 読込中", quit_button=None)
        self.cfg = config.load()

        # ── 5時間ウィンドウ ──
        self._5h_header   = rumps.MenuItem("⏱  5時間ウィンドウ")
        self._5h_used     = rumps.MenuItem("　 使用: --")
        self._5h_remain   = rumps.MenuItem("　 残量: --")
        self._5h_reset    = rumps.MenuItem("　 リセット: --")

        # ── 7日間ウィンドウ ──
        self._7d_header   = rumps.MenuItem("📅  週次ウィンドウ (7日間)")
        self._7d_used     = rumps.MenuItem("　 使用: --")
        self._7d_remain   = rumps.MenuItem("　 残量: --")
        self._7d_reset    = rumps.MenuItem("　 リセット: --")

        # ── 現在セッション ──
        self._sess_header = rumps.MenuItem("💬  現在セッション")
        self._sess_in     = rumps.MenuItem("　 input:       --")
        self._sess_out    = rumps.MenuItem("　 output:      --")
        self._sess_cc     = rumps.MenuItem("　 cache_create: --")
        self._sess_cr     = rumps.MenuItem("　 cache_read:  --")
        self._sess_total  = rumps.MenuItem("　 合計:        --")

        # ── プラン選択サブメニュー ──
        self._plan_menu = rumps.MenuItem("📋  プラン")
        self._plan_items: dict[str, rumps.MenuItem] = {}
        for key, meta in config.PLANS.items():
            item = rumps.MenuItem(meta["label"], callback=self._on_plan)
            item.state = 1 if key == self.cfg.get("plan", "pro") else 0
            self._plan_items[key] = item
            self._plan_menu.add(item)

        self._last_updated = rumps.MenuItem("　 最終更新: --")

        self.menu = [
            self._5h_header,
            self._5h_used,
            self._5h_remain,
            self._5h_reset,
            None,
            self._7d_header,
            self._7d_used,
            self._7d_remain,
            self._7d_reset,
            None,
            self._sess_header,
            self._sess_in,
            self._sess_out,
            self._sess_cc,
            self._sess_cr,
            self._sess_total,
            None,
            self._plan_menu,
            self._last_updated,
            None,
            rumps.MenuItem("↺ 今すぐ更新", callback=self._on_refresh),
            rumps.MenuItem("✕ 終了",       callback=self._on_quit),
        ]

        self._observer = watcher.start(self._schedule_refresh)
        self._refresh_now()

    # ── タイマー（60秒ごとのフォールバック更新） ──
    @rumps.timer(60)
    def _tick(self, _) -> None:
        self._refresh_now()

    # ── ファイル変更 → メインスレッドで更新 ──
    def _schedule_refresh(self) -> None:
        rumps.Timer(self._on_timer_fire, 0).start()

    def _on_timer_fire(self, timer) -> None:
        timer.stop()
        self._refresh_now()

    def _on_refresh(self, _) -> None:
        self._refresh_now()

    def _refresh_now(self) -> None:
        threading.Thread(target=self._do_refresh, daemon=True).start()

    def _do_refresh(self) -> None:
        try:
            snap = aggregator.collect()
            lim_5h, lim_7d = config.limits(self.cfg)
            warn  = self.cfg.get("warn_pct",   config.DEFAULTS["warn_pct"])
            danger = self.cfg.get("danger_pct", config.DEFAULTS["danger_pct"])
            now = datetime.now(timezone.utc)
            self._apply(snap, lim_5h, lim_7d, warn, danger, now)
        except Exception as e:
            self.title = f"⚠ エラー: {e}"

    def _apply(self, snap, lim_5h, lim_7d, warn, danger, now) -> None:
        # 5時間ウィンドウ
        used_5h = snap.five_hour.total
        if lim_5h > 0:
            pct_5h = _pct(used_5h, lim_5h)
            self._5h_used.title   = f"　 使用: {used_5h:>12,} / {lim_5h:,} tokens"
            self._5h_remain.title = f"　 残量: {max(0, lim_5h - used_5h):>12,} tokens ({pct_5h:.0f}%)"
        else:
            pct_5h = -1  # 上限未設定
            self._5h_used.title   = f"　 使用: {used_5h:>12,} tokens"
            self._5h_remain.title = f"　 残量: 上限未設定 (⚙ 設定から入力)"
        self._5h_reset.title = f"　 リセット: 最大 {_delta_str(5 * 3600)}"

        # 7日間ウィンドウ
        used_7d = snap.seven_day.total
        if lim_7d > 0:
            pct_7d = _pct(used_7d, lim_7d)
            self._7d_used.title   = f"　 使用: {used_7d:>12,} / {lim_7d:,} tokens"
            self._7d_remain.title = f"　 残量: {max(0, lim_7d - used_7d):>12,} tokens ({pct_7d:.0f}%)"
        else:
            pct_7d = -1  # 上限未設定
            self._7d_used.title   = f"　 使用: {used_7d:>12,} tokens"
            self._7d_remain.title = f"　 残量: 上限未設定 (⚙ 設定から入力)"
        self._7d_reset.title = f"　 リセット: 最大 {_delta_str(7 * 86400)}"

        # セッション
        s = snap.session
        self._sess_in.title    = f"　 input:        {s.input:>10,}"
        self._sess_out.title   = f"　 output:       {s.output:>10,}"
        self._sess_cc.title    = f"　 cache_create: {s.cache_create:>10,}"
        self._sess_cr.title    = f"　 cache_read:   {s.cache_read:>10,}"
        self._sess_total.title = f"　 合計:         {s.total:>10,}"

        # 最終更新
        jst = now.astimezone()
        self._last_updated.title = f"　 最終更新: {jst.strftime('%H:%M:%S')}"

        # メニューバータイトル
        def _fmt_pct(pct: float) -> str:
            return f"{pct:.0f}%" if pct >= 0 else "--"

        if pct_5h >= 0 or pct_7d >= 0:
            known_pcts = [p for p in (pct_5h, pct_7d) if p >= 0]
            min_pct = min(known_pcts)
            ind = _indicator(min_pct, warn, danger)
        else:
            ind = "⏱"

        self.title = f"{ind} 5h:{_fmt_pct(pct_5h)}  7d:{_fmt_pct(pct_7d)}"

    # ── プラン選択 ──
    def _on_plan(self, sender) -> None:
        for key, item in self._plan_items.items():
            if item.title == sender.title:
                self.cfg["plan"] = key
                item.state = 1
            else:
                item.state = 0

        if self.cfg["plan"] == "custom":
            self._ask_custom_limits()

        config.save(self.cfg)
        self._refresh_now()

    def _ask_custom_limits(self) -> None:
        w5 = rumps.Window(
            title="カスタム上限 — 5時間ウィンドウ",
            message="5時間あたりの上限トークン数を入力:",
            default_text=str(self.cfg.get("custom_5h", config.BASE_5H)),
            ok="OK", cancel="キャンセル",
        )
        r5 = w5.run()
        if r5.clicked:
            try:
                self.cfg["custom_5h"] = int(r5.text.replace(",", ""))
            except ValueError:
                pass

        w7 = rumps.Window(
            title="カスタム上限 — 週次ウィンドウ",
            message="7日あたりの上限トークン数を入力:",
            default_text=str(self.cfg.get("custom_7d", config.BASE_7D)),
            ok="OK", cancel="キャンセル",
        )
        r7 = w7.run()
        if r7.clicked:
            try:
                self.cfg["custom_7d"] = int(r7.text.replace(",", ""))
            except ValueError:
                pass

    def _on_quit(self, _) -> None:
        self._observer.stop()
        rumps.quit_application()


# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    App().run()
