# =========================
# source_config.py のユニットテスト
# =========================
import json
import os
import pytest

import py_package.utils.source_config as source_config_module
from py_package.utils.source_config import (
    load_source_config,
    save_source_config,
    load_rate_filter,
    save_rate_filter,
)


@pytest.fixture(autouse=True)
def patch_config_path(tmp_path, monkeypatch):
    """テスト用に設定ファイルパスを一時ディレクトリに差し替える。"""
    tmp_file = str(tmp_path / "source_config.json")
    monkeypatch.setattr(source_config_module, "_CONFIG_PATH", tmp_file)
    yield tmp_file


class TestLoadSourceConfig:
    def test_returns_empty_dict_when_file_not_exists(self):
        result = load_source_config()
        assert result == {}

    def test_returns_empty_dict_when_key_missing(self, patch_config_path):
        with open(patch_config_path, "w", encoding="utf-8") as f:
            json.dump({"rate_filter": {}}, f)
        assert load_source_config() == {}

    def test_returns_enabled_sources(self, patch_config_path):
        data = {"enabled_sources": {"file_a.json": True, "file_b.json": False}}
        with open(patch_config_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        result = load_source_config()
        assert result == {"file_a.json": True, "file_b.json": False}


class TestSaveSourceConfig:
    def test_saves_enabled_sources(self, patch_config_path):
        enabled_map = {"q1.json": True, "q2.json": False}
        save_source_config(enabled_map)
        with open(patch_config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["enabled_sources"] == enabled_map

    def test_does_not_overwrite_other_keys(self, patch_config_path):
        initial = {"rate_filter": {"enabled": True, "threshold": 0.5}}
        with open(patch_config_path, "w", encoding="utf-8") as f:
            json.dump(initial, f)

        save_source_config({"q.json": True})

        with open(patch_config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["rate_filter"] == {"enabled": True, "threshold": 0.5}
        assert data["enabled_sources"] == {"q.json": True}


class TestLoadRateFilter:
    def test_returns_empty_dict_when_no_file(self):
        assert load_rate_filter() == {}

    def test_returns_rate_filter_section(self, patch_config_path):
        data = {"rate_filter": {"enabled": True, "threshold": 0.3}}
        with open(patch_config_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        result = load_rate_filter()
        assert result == {"enabled": True, "threshold": 0.3}


class TestSaveRateFilter:
    def test_saves_rate_filter(self, patch_config_path):
        save_rate_filter({"enabled": False, "threshold": 0.6})
        with open(patch_config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["rate_filter"] == {"enabled": False, "threshold": 0.6}

    def test_does_not_overwrite_enabled_sources(self, patch_config_path):
        initial = {"enabled_sources": {"q.json": True}}
        with open(patch_config_path, "w", encoding="utf-8") as f:
            json.dump(initial, f)

        save_rate_filter({"enabled": True, "threshold": 0.4})

        with open(patch_config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["enabled_sources"] == {"q.json": True}
        assert data["rate_filter"]["threshold"] == 0.4
