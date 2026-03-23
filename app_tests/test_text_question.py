# =========================
# text_question.py のユニットテスト
# =========================
import pytest
from py_package.question_models.text_question import TextQuestion
from py_package.utils.quiz_field import QuizField


def make_q(question="Q1", answer="A1", explanation=None):
    item = {
        QuizField.Question.value: question,
        QuizField.Answer.value: answer,
    }
    if explanation:
        item[QuizField.Explanation.value] = explanation
    q = TextQuestion(item, "src.json")
    q.set_stats(None)
    return q


class TestTextQuestionInit:
    def test_answer_stripped(self):
        q = make_q(answer="  hello  ")
        assert q.answer == "hello"

    def test_question_stripped(self):
        q = make_q(question="  test  ")
        assert q.question == "test"

    def test_source_file_stored(self):
        q = make_q()
        assert q.source_file == "src.json"

    def test_explanation_stored(self):
        q = make_q(explanation="解説テキスト")
        assert q.explanation == "解説テキスト"

    def test_explanation_none_by_default(self):
        q = make_q()
        assert q.explanation is None


class TestTextQuestionGetType:
    def test_returns_text(self):
        assert make_q().get_type() == "text"


class TestTextQuestionGetCorrectAnswer:
    def test_returns_answer(self):
        q = make_q(answer="correct_answer")
        assert q.get_correct_answer() == "correct_answer"


class TestTextQuestionIsCorrect:
    def test_exact_match(self):
        q = make_q(answer="linux")
        assert q.is_correct("linux") is True

    def test_wrong_answer(self):
        q = make_q(answer="linux")
        assert q.is_correct("LINUX") is False

    def test_case_sensitive(self):
        q = make_q(answer="Linux")
        assert q.is_correct("linux") is False

    def test_empty_string_wrong(self):
        q = make_q(answer="linux")
        assert q.is_correct("") is False

    def test_empty_answer_match(self):
        q = make_q(answer="")
        assert q.is_correct("") is True


class TestTextQuestionGetQuizField:
    def test_contains_answer(self):
        q = make_q(answer="ans")
        assert q.get_quiz_field()[QuizField.Answer.value] == "ans"

    def test_contains_question(self):
        q = make_q(question="問題文")
        assert q.get_quiz_field()[QuizField.Question.value] == "問題文"

    def test_choices_not_in_field(self):
        """記述問題には選択肢フィールドが存在しない。"""
        field = make_q().get_quiz_field()
        assert QuizField.Choices.value not in field
