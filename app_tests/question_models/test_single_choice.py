# =========================
# single_choice.py のユニットテスト
# =========================
import pytest
from py_package.question_models.single_choice import SingleChoiceQuestion
from py_package.utils.quiz_field import QuizField


def make_item(choices, question="問1", explanation=None):
    item = {
        QuizField.Question.value: question,
        QuizField.Choices.value: choices,
    }
    if explanation:
        item[QuizField.Explanation.value] = explanation
    return item


def make_q(choices, question="問1", explanation=None):
    q = SingleChoiceQuestion(make_item(choices, question, explanation), "src.json")
    q.set_stats(None)
    return q


class TestSingleChoiceInit:
    def test_answer_extracted_from_asterisk(self):
        q = make_q(["A", "*B", "C"])
        assert q.answer == "B"

    def test_choices_contains_clean_answer(self):
        q = make_q(["A", "*B", "C"])
        assert "B" in q.choices
        assert "*B" not in q.choices

    def test_all_choices_in_list(self):
        q = make_q(["A", "*B", "C"])
        assert set(q.choices) == {"A", "B", "C"}

    def test_no_answer_raises_assertion(self):
        with pytest.raises(AssertionError):
            make_q(["A", "B", "C"])  # アスタリスクなし

    def test_source_file_stored(self):
        q = make_q(["*A"])
        assert q.source_file == "src.json"


class TestSingleChoiceGetType:
    def test_returns_single_choice(self):
        q = make_q(["*A", "B"])
        assert q.get_type() == "single_choice"


class TestSingleChoiceGetCorrectAnswer:
    def test_returns_correct_answer(self):
        q = make_q(["A", "*correct", "C"])
        assert q.get_correct_answer() == "correct"


class TestSingleChoiceIsCorrect:
    def test_correct_input(self):
        q = make_q(["A", "*correct", "C"])
        assert q.is_correct("correct") is True

    def test_wrong_input(self):
        q = make_q(["A", "*correct", "C"])
        assert q.is_correct("A") is False

    def test_empty_input(self):
        q = make_q(["A", "*correct"])
        assert q.is_correct("") is False

    def test_case_sensitive(self):
        q = make_q(["*Answer"])
        assert q.is_correct("answer") is False


class TestSingleChoiceGetQuizField:
    def test_contains_choices(self):
        q = make_q(["A", "*B"])
        field = q.get_quiz_field()
        assert QuizField.Choices.value in field
        assert set(field[QuizField.Choices.value]) == {"A", "B"}

    def test_contains_answer(self):
        q = make_q(["A", "*B"])
        field = q.get_quiz_field()
        assert field[QuizField.Answer.value] == "B"

    def test_contains_question(self):
        q = make_q(["*A"], question="テスト問題")
        field = q.get_quiz_field()
        assert field[QuizField.Question.value] == "テスト問題"
