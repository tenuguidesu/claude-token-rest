# claude-token-rest

Claude Code のトークン残量を macOS メニューバーにリアルタイム表示するアプリです。

![メニューバーのイメージ](assets/)

---

## 機能

- **5時間ウィンドウ** — 直近5時間のトークン使用量と残量をパーセント表示
- **週次ウィンドウ（7日間）** — 直近7日間の累積使用量と残量
- **現在セッション** — 現在の Claude Code セッションの input / output / cache 内訳
- **プラン切り替え** — Pro / Max 5x / Max 20x / カスタム上限を選択可能
- **リアルタイム更新** — `.jsonl` ファイルの変更を検知して自動更新（60秒フォールバックあり）
- **アラートカラー** — 残量に応じてメニューバーアイコンが 🟢 / 🟡 / 🔴 に変化

---

## トークン数の取得方法

Claude Code は会話ログを以下のパスに JSONL 形式で保存しています。

```
~/.claude/projects/<プロジェクトID>/<会話ID>.jsonl
```

各行は1ターン分のレコードで、`message.usage` フィールドにトークン数が含まれます。

```jsonc
{
  "timestamp": "2026-05-14T10:00:00.000Z",
  "sessionId": "abc123",
  "message": {
    "usage": {
      "input_tokens": 1234,
      "output_tokens": 567,
      "cache_creation_input_tokens": 89,
      "cache_read_input_tokens": 4567
    }
  }
}
```

本アプリはこのファイル群を `glob` で全走査し、`timestamp` を基準に以下の集計を行います。

| 集計対象 | 読み取り元 | 期間 |
|---|---|---|
| 5時間ウィンドウ | `~/.claude/projects/**/*.jsonl` | 現在時刻 − 5時間 |
| 週次ウィンドウ | `~/.claude/projects/**/*.jsonl` | 現在時刻 − 7日間 |
| 現在セッション | 同上 + `~/.claude/sessions/*.json` | 最新セッション ID と一致する行 |

現在セッションの特定には `~/.claude/sessions/*.json` の `updatedAt` が最新のレコードを使用します。

> **Note:** Anthropic はトークン上限を公式に公開していません。本アプリが参照する上限値（Pro: 5万tokens/5h、50万tokens/7d）は推定値です。実際の制限と異なる場合はカスタムプランで手動設定してください。

---

## インストール

### 前提条件

- macOS 12 Monterey 以降
- Python 3.11 以上
- Claude Code CLI がインストール済みであること

### 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 直接起動（開発用）

```bash
python src/main.py
```

### .app としてビルド（配布用）

```bash
pip install -r requirements-build.txt
pyinstaller --onefile --windowed --name "Claude Token Rest" src/main.py
```

生成された `dist/Claude Token Rest.app` を `/Applications` にコピーして使用します。

---

## 設定

設定ファイルは `~/.claude-token-rest/config.json` に自動生成されます。

```json
{
  "plan": "pro",
  "warn_pct": 30,
  "danger_pct": 10
}
```

| キー | 説明 | デフォルト |
|---|---|---|
| `plan` | `pro` / `max5` / `max20` / `custom` | `"pro"` |
| `warn_pct` | 残量がこの%を下回ると🟡 | `30` |
| `danger_pct` | 残量がこの%を下回ると🔴 | `10` |
| `custom_5h` | カスタムプラン時の5時間上限 | `50000` |
| `custom_7d` | カスタムプラン時の7日上限 | `500000` |

プランはメニューバーの「📋 プラン」から GUI でも切り替えられます。

---

## プラン別トークン上限（推定値）

| プラン | 5時間ウィンドウ | 7日間ウィンドウ |
|---|---|---|
| Pro (1x) | 50,000 | 500,000 |
| Max (5x) | 250,000 | 2,500,000 |
| Max (20x) | 1,000,000 | 10,000,000 |
| カスタム | 任意 | 任意 |

---

## ライセンス

MIT
