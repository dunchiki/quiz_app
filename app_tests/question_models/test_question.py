# =========================
# question.py のユニットテスト
# =========================
import pytest
from datetime import datetime, timedelta

from py_package.question_models.question import Question
from py_package.utils.quiz_field import QuizField
from py_package.utils.stats import Stats


# テスト用の具体サブクラス
class ConcreteQuestion(Question):
    def get_type(self):
        return "concrete"

    def get_correct_answer(self):
        return "correct"

    def is_correct(self, user_input):
        return user_input == "correct"


def make_question(question="Q1", answer="A1", explanation=None):
    item = {
        QuizField.Question.value: question,
        QuizField.Answer.value: answer,
    }
    if explanation:
        item[QuizField.Explanation.value] = explanation
    return ConcreteQuestion(item, "test_source.json")


@pytest.fixture
def q():
    q = make_question()
    q.set_stats(None)   # デフォルト統計でリセット
    return q


class TestQuestionInit:
    def test_question_stripped(self):
        q = make_question(question="  hello  ")
        assert q.question == "hello"

    def test_source_file_set(self):
        q = make_question()
        assert q.source_file == "test_source.json"

    def test_explanation_stripped(self):
        q = make_question(explanation="  exp  ")
        assert q.explanation == "exp"

    def test_explanation_none_when_missing(self):
        q = make_question()
        assert q.explanation is None


class TestSetStats:
    def test_defaults_when_stats_is_none(self, q):
        assert q.view_count == 0
        assert q.disabled is False
        assert q.resent_results == []
        assert q.interval == 0

    def test_loads_provided_stats(self, q):
        now_str = datetime.now().isoformat(timespec="seconds")
        stats = {
            Stats.Count.value: 5,
            Stats.Disabled.value: True,
            Stats.ResentResults.value: [True, False],
            Stats.Interval.value: 3.0,
            Stats.LastViewDate.value: now_str,
        }
        q.set_stats(stats)
        assert q.view_count == 5
        assert q.disabled is True
        assert q.resent_results == [True, False]
        assert q.interval == 3.0


class TestGetStats:
    def test_returns_dict_with_all_keys(self, q):
        stats = q.get_stats()
        assert Stats.Count.value in stats
        assert Stats.Disabled.value in stats
        assert Stats.ResentResults.value in stats
        assert Stats.Interval.value in stats
        assert Stats.LastViewDate.value in stats

    def test_count_reflects_view_count(self, q):
        q.view_count = 7
        assert q.get_stats()[Stats.Count.value] == 7


class TestGetCorrectRate:
    def test_returns_zero_when_no_results(self, q):
        assert q.get_correct_rate() == 0.0

    def test_all_correct(self, q):
        q.resent_results = [True, True, True]
        assert q.get_correct_rate() == 1.0

    def test_all_wrong(self, q):
        q.resent_results = [False, False]
        assert q.get_correct_rate() == 0.0

    def test_mixed(self, q):
        q.resent_results = [True, False, True, False]
        assert q.get_correct_rate() == pytest.approx(0.5)


class TestUpdateStats:
    def test_view_count_incremented(self, q):
        q.update_stats(True)
        assert q.view_count == 1

    def test_resent_results_appended(self, q):
        q.update_stats(True)
        assert q.resent_results[-1] is True

    def test_resent_results_capped_at_recent_answer_count(self, q):
        from quiz_config import RECENT_ANSWER_COUNT
        for _ in range(RECENT_ANSWER_COUNT + 3):
            q.update_stats(True)
        assert len(q.resent_results) == RECENT_ANSWER_COUNT

    def test_correct_increases_interval(self, q):
        q.interval = 2.0
        q.resent_results = [True, True, True]  # 強問題でないようにする
        q.update_stats(True)
        assert q.interval > 2.0

    def test_wrong_decreases_interval(self, q):
        q.interval = 4.0
        q.resent_results = [False]
        q.update_stats(False)
        assert q.interval < 4.0

    def test_wrong_twice_resets_interval_to_one(self, q):
        q.interval = 8.0
        q.update_stats(False)
        q.update_stats(False)
        assert q.interval == pytest.approx(1.0)


class TestIsWeakQuestion:
    def test_is_weak_when_low_rate(self, q):
        q.resent_results = [False, False, False]
        q.view_count = 10
        assert q.is_weak_question() is True

    def test_is_weak_when_few_views(self, q):
        q.view_count = 1
        assert q.is_weak_question() is True

    def test_not_weak_when_high_rate_and_many_views(self, q):
        q.resent_results = [True] * 10
        q.view_count = 10
        assert q.is_weak_question() is False


class TestIsIntervalReady:
    def test_ready_when_interval_zero(self, q):
        q.interval = 0
        q.last_view_date = datetime.now() - timedelta(days=100)
        # interval=0 でも last_view_date が古ければ通る
        # interval=0 の場合は timedelta(0) なので常に True になる
        assert q.is_interval_ready() is True

    def test_not_ready_when_viewed_recently(self, q):
        q.interval = 10.0
        q.last_view_date = datetime.now()
        assert q.is_interval_ready() is False

    def test_ready_when_interval_elapsed(self, q):
        q.interval = 1.0
        q.last_view_date = datetime.now() - timedelta(days=2)
        assert q.is_interval_ready() is True


class TestGetQuizField:
    def test_contains_question_and_explanation(self):
        q = make_question(question="Test Q", explanation="Exp text")
        q.set_stats(None)
        field = q.get_quiz_field()
        assert field[QuizField.Question.value] == "Test Q"
        assert field[QuizField.Explanation.value] == "Exp text"
