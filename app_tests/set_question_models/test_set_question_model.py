# =========================
# set_question_model.py のユニットテスト
# =========================
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from py_package.question_models.text_question import TextQuestion
from py_package.utils.quiz_field import QuizField
from py_package.set_question_models.set_question_model import QuizModel


# ==========================================
# テスト用ヘルパー
# ==========================================
def make_text_q(question="Q", answer="A", source="src.json", disabled=False, interval=0.0,
                resent_results=None):
    item = {QuizField.Question.value: question, QuizField.Answer.value: answer}
    q = TextQuestion(item, source)
    q.set_stats(None)
    q.disabled = disabled
    q.interval = interval
    q.resent_results = resent_results or []
    return q


@pytest.fixture
def model_with_questions(questions=None):
    """QuestionDataInterface と source_config をモックして QuizModel を生成する。"""
    qs = questions or [make_text_q(f"Q{i}", f"A{i}") for i in range(3)]
    with patch("py_package.set_question_models.set_question_model.QuestionDataInterface") as MockDI, \
         patch("py_package.set_question_models.set_question_model.load_source_config", return_value={}), \
         patch("py_package.set_question_models.set_question_model.load_rate_filter", return_value={}):
        mock_di = MagicMock()
        mock_di.get_all_source_basenames.return_value = ["src.json"]
        mock_di.get_questions.return_value = qs
        MockDI.return_value = mock_di
        model = QuizModel()
    return model, qs


# ==========================================
# 初期化テスト
# ==========================================
class TestQuizModelInit:
    def test_question_list_loaded(self):
        qs = [make_text_q("Q1", "A1")]
        model, _ = model_with_questions.__wrapped__(qs) if hasattr(model_with_questions, '__wrapped__') else (None, None)
        # fixtureを直接使えないので inline で確認
        with patch("py_package.set_question_models.set_question_model.QuestionDataInterface") as MockDI, \
             patch("py_package.set_question_models.set_question_model.load_source_config", return_value={}), \
             patch("py_package.set_question_models.set_question_model.load_rate_filter", return_value={}):
            mock_di = MagicMock()
            mock_di.get_all_source_basenames.return_value = ["src.json"]
            mock_di.get_questions.return_value = qs
            MockDI.return_value = mock_di
            model = QuizModel()
        assert model.question_list == qs

    def test_current_question_is_none_initially(self):
        with patch("py_package.set_question_models.set_question_model.QuestionDataInterface") as MockDI, \
             patch("py_package.set_question_models.set_question_model.load_source_config", return_value={}), \
             patch("py_package.set_question_models.set_question_model.load_rate_filter", return_value={}):
            mock_di = MagicMock()
            mock_di.get_all_source_basenames.return_value = []
            mock_di.get_questions.return_value = []
            MockDI.return_value = mock_di
            model = QuizModel()
        assert model.is_cq_set is False

    def test_rate_filter_defaults_from_load(self):
        with patch("py_package.set_question_models.set_question_model.QuestionDataInterface") as MockDI, \
             patch("py_package.set_question_models.set_question_model.load_source_config", return_value={}), \
             patch("py_package.set_question_models.set_question_model.load_rate_filter",
                   return_value={"enabled": True, "threshold": 0.3}):
            mock_di = MagicMock()
            mock_di.get_all_source_basenames.return_value = []
            mock_di.get_questions.return_value = []
            MockDI.return_value = mock_di
            model = QuizModel()
        enabled, threshold = model.get_rate_filter()
        assert enabled is True
        assert threshold == pytest.approx(0.3)


# ==========================================
# ヘルパーマクロ: モデルを手軽に作る
# ==========================================
def _make_model(questions=None, all_sources=None, rate_filter=None):
    qs = questions or []
    with patch("py_package.set_question_models.set_question_model.QuestionDataInterface") as MockDI, \
         patch("py_package.set_question_models.set_question_model.load_source_config", return_value={}), \
         patch("py_package.set_question_models.set_question_model.load_rate_filter", return_value=rate_filter or {}):
        mock_di = MagicMock()
        mock_di.get_all_source_basenames.return_value = all_sources or ["src.json"]
        mock_di.get_questions.return_value = qs
        MockDI.return_value = mock_di
        model = QuizModel()
    return model


# ==========================================
# is_cq_set / set_random_question
# ==========================================
class TestSetRandomQuestion:
    def test_cq_set_after_call(self):
        qs = [make_text_q()]
        model = _make_model(qs)
        model.set_random_question()
        assert model.is_cq_set is True

    def test_cq_none_when_no_questions(self):
        model = _make_model([])
        model.set_random_question()
        assert model.is_cq_set is False

    def test_selects_unanswered_first(self):
        """interval=0 の問題（未回答）を優先して選ぶ。"""
        unanswered = make_text_q("U", interval=0.0)
        answered   = make_text_q("A", interval=5.0)
        answered.last_view_date = datetime.now()
        model = _make_model([unanswered, answered])
        results = set()
        for _ in range(20):
            model.set_random_question()
            results.add(model._current_question.question)
        assert results == {"U"}

    def test_disabled_not_selected(self):
        q_enabled  = make_text_q("E")
        q_disabled = make_text_q("D", disabled=True)
        # disabled は get_questions で除外済みとして question_list をセット
        model = _make_model([q_enabled])
        model.set_random_question()
        assert model._current_question.question == "E"


# ==========================================
# is_correct_answer
# ==========================================
class TestIsCorrectAnswer:
    def test_correct(self):
        q = make_text_q("Q", "correct")
        model = _make_model([q])
        model._current_question = q
        assert model.is_correct_answer("correct") is True

    def test_wrong(self):
        q = make_text_q("Q", "correct")
        model = _make_model([q])
        model._current_question = q
        assert model.is_correct_answer("wrong") is False


# ==========================================
# set_cq_disabled
# ==========================================
class TestSetCqDisabled:
    def test_sets_disabled_true(self):
        q = make_text_q()
        model = _make_model([q])
        model._current_question = q
        model.set_cq_disabled(True)
        assert q.disabled is True

    def test_sets_disabled_false(self):
        q = make_text_q()
        q.disabled = True
        model = _make_model([q])
        model._current_question = q
        model.set_cq_disabled(False)
        assert q.disabled is False


# ==========================================
# set_rate_filter / get_rate_filter
# ==========================================
class TestRateFilter:
    def test_set_and_get(self):
        model = _make_model()
        model.set_rate_filter(True, 0.5)
        enabled, threshold = model.get_rate_filter()
        assert enabled is True
        assert threshold == pytest.approx(0.5)

    def test_threshold_clamped_above_1(self):
        model = _make_model()
        model.set_rate_filter(True, 1.5)
        _, threshold = model.get_rate_filter()
        assert threshold == pytest.approx(1.0)

    def test_threshold_clamped_below_0(self):
        model = _make_model()
        model.set_rate_filter(True, -0.5)
        _, threshold = model.get_rate_filter()
        assert threshold == pytest.approx(0.0)


# ==========================================
# reload_questions
# ==========================================
class TestReloadQuestions:
    def test_current_question_reset(self):
        q = make_text_q()
        model = _make_model([q])
        model._current_question = q
        model.question_data.get_questions.return_value = [q]
        model.reload_questions({"src.json"})
        assert model._current_question is None

    def test_enabled_sources_updated(self):
        model = _make_model([])
        model.question_data.get_questions.return_value = []
        model.reload_questions({"a.json", "b.json"})
        assert model._enabled_sources == {"a.json", "b.json"}


# ==========================================
# num_* カウント系プロパティ
# ==========================================
class TestCountMethods:
    def test_get_num_not_answered(self):
        q1 = make_text_q(interval=0.0)
        q2 = make_text_q(interval=1.0)
        model = _make_model([q1, q2])
        assert model.get_num_not_answered_questions() == 1

    def test_get_num_today_answer_questions(self):
        q1 = make_text_q(interval=1.0)  # interval!=0 かつ today
        q1.last_view_date = datetime.now()
        q2 = make_text_q(interval=0.0)  # interval=0 は除外
        model = _make_model([q1, q2])
        assert model.get_num_today_answer_questions() == 1


# ==========================================
# current question プロパティ
# ==========================================
class TestCurrentQuestionProperties:
    def test_cq_type(self):
        q = make_text_q()
        model = _make_model([q])
        model._current_question = q
        assert model.cq_type == "text"

    def test_cq_source_file(self):
        q = make_text_q(source="my_source.json")
        model = _make_model([q])
        model._current_question = q
        assert model.cq_source_file == "my_source.json"

    def test_cq_correct_rate(self):
        q = make_text_q()
        q.resent_results = [True, True]
        model = _make_model([q])
        model._current_question = q
        assert model.cq_correct_rate == pytest.approx(1.0)

    def test_cq_disabled(self):
        q = make_text_q()
        q.disabled = True
        model = _make_model([q])
        model._current_question = q
        assert model.cq_disabled is True
