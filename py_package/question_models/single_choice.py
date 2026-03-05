# =========================
# 単一選択問題
# =========================

from py_package.question_models.question import Question
from py_package.utils.quiz_field import QuizField

class SingleChoiceQuestion(Question):
    def __init__(self, item, source_file):
        choices = item.get(QuizField.Choices.value, [])

        super().__init__(item, source_file)

        self.choices = []
        self.answer = None

        for choice in choices:
            choice = choice.strip()

            if choice.startswith("*"):
                clean_choice = choice[1:].strip()
                self.answer = clean_choice
                self.choices.append(clean_choice)
            else:
                self.choices.append(choice)

        assert self.answer, f"{self.question} has no answers."

    def get_type(self):
        return "single_choice"

    def get_correct_answer(self):
        return self.answer

    def is_correct(self, user_input):
        return user_input == self.answer

    def get_quiz_field(self):
        field = super().get_quiz_field()
        field[QuizField.Choices.value] = self.choices
        field[QuizField.Answer.value] = self.answer
        return field
