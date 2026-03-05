# =========================
# 記述問題
# =========================

from py_package.question_models.question import Question
from py_package.utils.quiz_field import QuizField

class TextQuestion(Question):
    def __init__(self, item, source_file):
        answer = item.get(QuizField.Answer.value).strip()

        super().__init__(item, source_file)
        self.answer = answer

    def get_type(self):
        return "text"

    def get_correct_answer(self):
        return self.answer

    def is_correct(self, user_input):
        return user_input == self.answer

    def get_quiz_field(self):
        field = super().get_quiz_field()
        field[QuizField.Answer.value] = self.answer
        return field
