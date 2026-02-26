# =========================
# クイズモデル
# =========================

import random

from py_package.data_interface.quiz_data import QuestionDataInterface
from py_package.question_models.question import Question

class QuizModel:
    def __init__(self):
        self.question_data = QuestionDataInterface()
        self.question_list: list[Question] = self.question_data.get_questions()

    def get_num_enable_questions(self) -> list[Question]:
        return len([q for q in self.question_list if q.is_enable() or q.interval == 0])

    def get_random_question(self): # TODO 問題の無効化
        weighted_pool = [q for q in self.question_list if q.is_enable()]

        if not weighted_pool:
            return None

        result = random.choices(
            weighted_pool,
            weights=[q.get_weight() for q in weighted_pool]
        )[0]

        assert not result.disabled
        return result

    def save(self):
        self.question_data.save_stats()