# Android build notes

## 1. Build prerequisites (manual)

このリポジトリ内では完結しないため、ローカル環境で次を準備してください。

- Linux/macOS もしくは WSL2
- Java 17
- Android SDK / NDK
- Buildozer

## 2. Optional Japanese font (recommended)

日本語表示を安定させるため、任意で以下を配置してください。

- `assets/fonts/NotoSansJP-Regular.ttf` または
- `assets/fonts/NotoSansCJKjp-Regular.otf`

未配置でも動作はしますが、端末依存フォントにフォールバックします。

## 3. Build and install

```bash
buildozer android debug
buildozer android deploy run
```

## 4. Runtime verification checklist

- 問題データ（`data/*.csv`, `data/*.json`）が読める
- 回答後に統計情報が保存される
- 設定（有効ソース / 正答率フィルター）が保存される
- 解説ポップアップが開ける
