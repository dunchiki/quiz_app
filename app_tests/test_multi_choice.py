# =========================
# multi_choice.py のユニットテスト
# =========================
import pytest
from py_package.question_models.multi_choice import MultiChoiceQuestion
from py_package.utils.quiz_field import QuizField


def make_q(choices, question="問1", explanation=None):
    item = {QuizField.Question.value: question, QuizField.Choices.value: choices}
    if explanation:
        item[QuizField.Explanation.value] = explanation
    q = MultiChoiceQuestion(item, "src.json")
    q.set_stats(None)
    return q


class TestMultiChoiceInit:
    def test_correct_answers_extracted(self):
        q = make_q(["A", "*B", "*C"])
        assert q.correct_answers == {"B", "C"}

    def test_asterisk_stripped_from_choices(self):
        q = make_q(["*A", "B"])
        assert "*A" not in q.choices
        assert "A" in q.choices

    def test_all_choices_present(self):
        q = make_q(["*A", "B", "*C"])
        assert set(q.choices) == {"A", "B", "C"}

    def test_fallback_when_no_answer_marked(self):
        """正解なしのとき先頭の選択肢が正解になる。"""
        q = make_q(["X", "Y", "Z"])
        assert q.correct_answers == {"X"}

    def test_source_file_stored(self):
        q = make_q(["*A"])
        assert q.source_file == "src.json"


class TestMultiChoiceGetType:
    def test_returns_multi_choice(self):
        q = make_q(["*A", "B"])
        assert q.get_type() == "multi_choice"


class TestMultiChoiceGetCorrectAnswer:
    def test_returns_comma_joined(self):
        q = make_q(["*A"])
        assert q.get_correct_answer() == "A"

    def test_returns_all_answers(self):
        q = make_q(["*A", "*B"])
        result = q.get_correct_answer()
        assert "A" in result
        assert "B" in result


class TestMultiChoiceIsCorrect:
    def test_exact_correct_set(self):
        q = make_q(["*A", "*B", "C"])
        assert q.is_correct(["A", "B"]) is True

    def test_order_independent(self):
        q = make_q(["*A", "*B"])
        assert q.is_correct(["B", "A"]) is True

    def test_missing_one_answer(self):
        q = make_q(["*A", "*B"])
        assert q.is_correct(["A"]) is False

    def test_extra_answer(self):
        q = make_q(["*A", "B"])
        assert q.is_correct(["A", "B"]) is False

    def test_empty_input(self):
        q = make_q(["*A", "*B"])
        assert q.is_correct([]) is False

    def test_all_wrong(self):
        q = make_q(["*A", "*B", "C"])
        assert q.is_correct(["C"]) is False


class TestMultiChoiceGetQuizField:
    def test_contains_choices(self):
        q = make_q(["*A", "B"])
        field = q.get_quiz_field()
        assert set(field[QuizField.Choices.value]) == {"A", "B"}

    def test_contains_correct_answers_set(self):
        q = make_q(["*A", "*B", "C"])
        field = q.get_quiz_field()
        assert field[QuizField.Answer.value] == {"A", "B"}

    def test_contains_question(self):
        q = make_q(["*A"], question="複数選択問題")
        assert q.get_quiz_field()[QuizField.Question.value] == "複数選択問題"
