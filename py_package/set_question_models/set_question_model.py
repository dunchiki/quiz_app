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
        self._current_question: Question = None

    def get_num_enable_questions(self) -> list[Question]:
        return len([q for q in self.question_list if q.is_enable() or q.interval == 0])

    def set_random_question(self):
        self._current_question = self._get_random_question()

    def save(self):
        self.question_data.save_stats()

    @property
    def cq_quiz_field(self) -> dict: return self._current_question.get_quiz_field()
    @property
    def cq_stats(self) -> dict: return self._current_question.get_stats()
    @property
    def cq_type(self) -> str: return self._current_question.get_type()
    @property
    def is_cq_set(self) -> bool: return not self._current_question is None
    
    def _get_random_question(self):
        not_answered_questions = [q for q in self.question_list if q.interval == 0]
        if not_answered_questions:
            weighted_pool = not_answered_questions
        else:
            weighted_pool = [q for q in self.question_list if q.is_enable()]

        if not weighted_pool:
            return None

        result = random.choices(
            weighted_pool,
            weights=[q.get_weight() for q in weighted_pool]
        )[0]

        assert not result.disabled
        return result
