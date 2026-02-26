# =========================
# 単一選択問題
# =========================

from py_package.question_models.question import Question
from py_package.utils.quiz_field import QuizField

class SingleChoiceQuestion(Question):
    def __init__(self, item, source_file):
        question = item.get(QuizField.Quiz.value).strip()
        choices = item.get(QuizField.Choices.value, [])

        super().__init__(question, source_file)

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

        # 安全対策：*が無かった場合
        if not self.answer and self.choices:
            self.answer = self.choices[0]

    def get_type(self):
        return "single_choice"

    def get_correct_answer(self):
        return self.answer

    def is_correct(self, user_input):
        return user_input == self.answer