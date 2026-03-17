# =========================
# クイズモデル
# =========================

from datetime import datetime
import random

from py_package.data_interface.quiz_data import QuestionDataInterface
from py_package.question_models.question import Question
from py_package.utils.source_config import load_source_config, save_source_config

class QuizModel:
    def __init__(self):
        self.question_data = QuestionDataInterface()

        # ソース設定を読み込み、有効なソースファイルを決定する
        # 設定ファイルが無い、またはそのキーが無い場合はデフォルト有効
        all_sources = self.question_data.get_all_source_basenames()
        config = load_source_config()
        self._enabled_sources: set[str] = {
            s for s in all_sources if config.get(s, True)
        }

        self.question_list: list[Question] = self.question_data.get_questions(self._enabled_sources)
        self._current_question: Question = None

    def get_num_enable_questions(self) -> int:
        return len([q for q in self.question_list if q.is_enable() or q.interval == 0])
    
    def get_num_today_answer_questions(self) -> int:
        return len([q for q in self.question_list if q.last_view_date.date() == datetime.now().date() and (q.interval != 0)])
    
    def get_num_not_answered_questions(self) -> int:
        return len([q for q in self.question_list if q.interval == 0])

    def set_random_question(self):
        not_answered_questions = [q for q in self.question_list if q.interval == 0]
        if not_answered_questions:
            weighted_pool = not_answered_questions
        else:
            weighted_pool = [q for q in self.question_list if q.is_enable()]

        if not weighted_pool:
            self._current_question = None
            return None

        result = random.choices(
            weighted_pool,
            weights=[q.get_weight() for q in weighted_pool]
        )[0]

        assert not result.disabled
        self._current_question = result

    def get_all_source_files(self) -> list[str]:
        """dataフォルダの全ソースファイル名一覧。"""
        return self.question_data.get_all_source_basenames()

    def get_enabled_sources(self) -> set[str]:
        """現在有効なソースファイル名のセット。"""
        return set(self._enabled_sources)

    def reload_questions(self, enabled_sources: set[str]):
        """指定ソースに制限して問題リストを再構築する。現在の問題もリセット。"""
        self._enabled_sources = set(enabled_sources)
        self.question_list = self.question_data.get_questions(self._enabled_sources)
        self._current_question = None

    def save(self):
        self.question_data.save_stats()
        # ソース有効無効設定を保存
        all_sources = self.question_data.get_all_source_basenames()
        enabled_map = {s: (s in self._enabled_sources) for s in all_sources}
        save_source_config(enabled_map)

    ### current_question 操作
    def is_correct_answer(self, answer) -> bool:
        return self._current_question.is_correct(answer)

    def set_cq_disabled(self, is_disabled = True):
        self._current_question.disabled = is_disabled

    def update_cq_stats(self, is_ok: bool):
        self._current_question.update_stats(is_ok)

    @property
    def cq_correct_rate(self) -> float: return self._current_question.get_correct_rate()
    @property
    def cq_quiz_field(self) -> dict: return self._current_question.get_quiz_field()
    @property
    def cq_source_file(self) -> str: return self._current_question.source_file
    @property
    def cq_stats(self) -> dict: return self._current_question.get_stats()
    @property
    def cq_type(self) -> str: return self._current_question.get_type()
    @property
    def is_cq_set(self) -> bool: return not self._current_question is None
