# =========================
# 実行環境ごとのパス解決
# =========================
import os

from quiz_config import DATA_FOLDER, STATS_FOLDER


def _project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))


def is_android_runtime() -> bool:
    return ("ANDROID_ARGUMENT" in os.environ) or ("ANDROID_PRIVATE" in os.environ)


def get_data_dir() -> str:
    """問題データフォルダの実体パスを返す。"""
    if is_android_runtime():
        android_arg = os.environ.get("ANDROID_ARGUMENT")
        if android_arg:
            return os.path.join(android_arg, DATA_FOLDER)
    return os.path.join(_project_root(), DATA_FOLDER)


def get_stats_dir() -> str:
    """統計情報保存フォルダの実体パスを返す。"""
    if is_android_runtime():
        android_private = os.environ.get("ANDROID_PRIVATE")
        if android_private:
            return os.path.join(android_private, "files", STATS_FOLDER)
    return os.path.join(_project_root(), STATS_FOLDER)
