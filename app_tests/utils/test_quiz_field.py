# =========================
# quiz_field.py のユニットテスト
# =========================
import pytest
from py_package.utils.quiz_field import QuizField


class TestQuizField:
    def test_answer_value(self):
        assert QuizField.Answer.value == "answer"

    def test_question_value(self):
        assert QuizField.Question.value == "question"

    def test_choices_value(self):
        assert QuizField.Choices.value == "choices"

    def test_explanation_value(self):
        assert QuizField.Explanation.value == "explanation"

    def test_all_members_exist(self):
        names = {m.name for m in QuizField}
        assert names == {"Answer", "Question", "Choices", "Explanation"}

    def test_lookup_by_value(self):
        assert QuizField("answer") is QuizField.Answer
        assert QuizField("question") is QuizField.Question
        assert QuizField("choices") is QuizField.Choices
        assert QuizField("explanation") is QuizField.Explanation

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            QuizField("invalid_key")
