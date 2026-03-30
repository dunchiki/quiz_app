# =========================
# stats.py のユニットテスト
# =========================
import pytest
from py_package.utils.stats import Stats


class TestStats:
    def test_count_value(self):
        assert Stats.Count.value == "count"

    def test_disabled_value(self):
        assert Stats.Disabled.value == "disabled"

    def test_resent_results_value(self):
        assert Stats.ResentResults.value == "resent_results"

    def test_interval_value(self):
        assert Stats.Interval.value == "Interval"

    def test_last_view_date_value(self):
        assert Stats.LastViewDate.value == "last_view_date"

    def test_all_members_exist(self):
        names = {m.name for m in Stats}
        assert names == {"Count", "Disabled", "ResentResults", "Interval", "LastViewDate"}

    def test_lookup_by_value(self):
        assert Stats("count") is Stats.Count
        assert Stats("disabled") is Stats.Disabled
        assert Stats("resent_results") is Stats.ResentResults
        assert Stats("Interval") is Stats.Interval
        assert Stats("last_view_date") is Stats.LastViewDate

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            Stats("nonexistent")
