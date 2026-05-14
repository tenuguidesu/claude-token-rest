#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "==> 依存関係をインストール"
pip install -r requirements-build.txt

echo "==> アイコンを生成"
python scripts/create_icon.py

echo "==> PyInstaller でビルド"
pyinstaller --clean --noconfirm claude-token-rest.spec

echo "==> DMG を作成"
DMG="dist/ClaudeTokenRest.dmg"
rm -f "$DMG"

hdiutil create \
  -volname "Claude Token Rest" \
  -srcfolder "dist/ClaudeTokenRest.app" \
  -ov \
  -format UDZO \
  "$DMG"

echo "==> 完了: $DMG"
open dist/
