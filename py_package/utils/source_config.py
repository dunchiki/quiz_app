# =========================
# ソース設定 / フィルター設定の読み書き
# =========================
import json
import os

from quiz_config import SOURCE_CONFIG_FILE
from py_package.utils.app_paths import get_profile_dir

_CONFIG_PATH = os.path.join(get_profile_dir(), SOURCE_CONFIG_FILE)


def _load_full() -> dict:
    if not os.path.exists(_CONFIG_PATH):
        return {}
    with open(_CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_full(data: dict):
    os.makedirs(os.path.dirname(_CONFIG_PATH), exist_ok=True)
    with open(_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---- ソースの有効/無効 ----

def load_source_config() -> dict[str, bool]:
    """
    ソースファイルの有効/無効設定をロードする。
    ファイルが存在しない場合は空 dict を返す（デフォルト: 全て有効）。
    """
    return _load_full().get("enabled_sources", {})


def save_source_config(enabled_map: dict[str, bool]):
    """
    ソースファイルの有効/無効設定を保存する。
    enabled_map: { "filename.json": True/False, ... }
    """
    data = _load_full()
    data["enabled_sources"] = enabled_map
    _save_full(data)


# ---- 正答率フィルター設定 ----

def load_rate_filter() -> dict:
    """正答率フィルター設定を返す。なければ空 dict。"""
    return _load_full().get("rate_filter", {})


def save_rate_filter(settings: dict):
    """正答率フィルター設定を保存する。他の設定は上書きしない。"""
    data = _load_full()
    data["rate_filter"] = settings
    _save_full(data)
