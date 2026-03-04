# =========================
# 複数選択問題
# =========================

from py_package.question_models.question import Question
from py_package.utils.quiz_field import QuizField

class MultiChoiceQuestion(Question):
    def __init__(self, item, source_file):
        choices = item.get(QuizField.Choices.value, [])

        super().__init__(item, source_file)

        self.choices = []
        self.correct_answers = set()

        for choice in choices:
            choice = choice.strip()

            if choice.startswith("*"):
                clean = choice[1:].strip()
                self.correct_answers.add(clean)
                self.choices.append(clean)
            else:
                self.choices.append(choice)

        # 安全対策
        if not self.correct_answers and self.choices:
            self.correct_answers.add(self.choices[0])

    def get_type(self):
        return "multi_choice"

    def get_correct_answer(self):
        return ", ".join(self.correct_answers)

    def is_correct(self, user_input_set):
        return set(user_input_set) == self.correct_answers