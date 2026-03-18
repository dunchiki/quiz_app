# =========================
# ソース設定の読み書き
# =========================
import json
import os

from quiz_config import SOURCE_CONFIG_FILE, STATS_FOLDER

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../..", STATS_FOLDER,  SOURCE_CONFIG_FILE)


def load_source_config() -> dict[str, bool]:
    """
    ソースファイルの有効/無効設定をロードする。
    ファイルが存在しない場合は空 dict を返す（デフォルト: 全て有効）。
    """
    if not os.path.exists(_CONFIG_PATH):
        return {}

    with open(_CONFIG_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data.get("enabled_sources", {})


def save_source_config(enabled_map: dict[str, bool]):
    """
    ソースファイルの有効/無効設定を保存する。
    enabled_map: { "filename.json": True/False, ... }
    """
    data = {"enabled_sources": enabled_map}
    with open(_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
