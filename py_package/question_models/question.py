# =========================
# 抽象基底クラス
# =========================

from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from quiz_config import RECENT_ANSWER_COUNT, WEEK_QUESTION_RATE_LIMIT
from py_package.utils.quiz_field import QuizField
from py_package.utils.stats import Stats

# 問題固有の処理はできるだけこれを継承したクラス内に実装する
class Question(ABC):
    view_count = 0
    disabled = False
    resent_results = []
    interval = 0
    last_view_date: datetime = None

    question = None
    explanation = None

    def __init__(self, item, source_file):
        self.question = item.get(QuizField.Question.value).strip()
        exp = item.get(QuizField.Explanation.value)
        if exp: self.explanation = exp.strip()
        self.source_file = source_file

    def set_stats(self, stats):
        if not stats: stats = {}
        default_stats: dict = {
            Stats.Count.value: 0,
            Stats.Disabled.value: False,
            Stats.ResentResults.value: [],
            Stats.Interval.value: 0,
            Stats.LastViewDate.value: datetime.now()
        }
        self.view_count = int(stats[Stats.Count.value]) if Stats.Count.value in stats else default_stats[Stats.Count.value]
        self.disabled = bool(stats[Stats.Disabled.value]) if Stats.Disabled.value in stats else default_stats[Stats.Disabled.value]
        self.resent_results = list(stats[Stats.ResentResults.value]) if Stats.ResentResults.value in stats else default_stats[Stats.ResentResults.value]
        self.interval = float(stats[Stats.Interval.value]) if Stats.Interval.value in stats else default_stats[Stats.Interval.value]
        self.last_view_date = datetime.fromisoformat(stats[Stats.LastViewDate.value]) if Stats.LastViewDate.value in stats else default_stats[Stats.LastViewDate.value]

    def update_stats(self, is_correct: bool):
        self.last_view_date = datetime.now()
        self.view_count += 1

        self.resent_results.append(is_correct)
        if len(self.resent_results) > RECENT_ANSWER_COUNT:
            self.resent_results.pop(0)

        old_interval = self.interval
        if is_correct:
            interval_a = self.interval + 1
            interval_b = self.interval * 1.5
            interval = min(interval_a, interval_b) if self.is_weak_question() else max(interval_a, interval_b)
            self.interval = max(interval, 1.5)
        else:
            if len(self.resent_results) >= 2 and (not self.resent_results[-1] and not self.resent_results[-2]):
                self.interval = 1.0
            else:
                self.interval = max(self.interval / 2, 1.0)
        print(f"rate: {int(self.get_correct_rate() * 100)}%, interval: {old_interval:.1f} → {self.interval:.1f}, Q: {self.question}")

    def get_stats(self):
        return {
            Stats.Count.value: self.view_count,
            Stats.Disabled.value: self.disabled,
            Stats.ResentResults.value: self.resent_results,
            Stats.Interval.value: self.interval,
            Stats.LastViewDate.value: self.last_view_date.isoformat(timespec="seconds")
        }

    def get_quiz_field(self):
        return {
            QuizField.Question.value: self.question,
            QuizField.Explanation.value: self.explanation,
        }

    def get_correct_rate(self) -> float:
        if len(self.resent_results) == 0:
            return 0.0
        correct_count = len([b for b in self.resent_results if b])
        wrong_count = len([b for b in self.resent_results if not b])
        return correct_count / (correct_count + wrong_count)
    
    def get_weight(self) -> float:
        elapsed_day = (datetime.now() - self.last_view_date).total_seconds() / (60 * 60 * 24)
        weight_with_time = elapsed_day / self.interval if (self.interval > 0) else 5.0

        weight_with_correct_rate = 1 / (self.get_correct_rate() + 1.0)
        return weight_with_time * weight_with_correct_rate
    
    def is_enable(self):
        return (not self.disabled) and self.is_interval_ready()

    def is_interval_ready(self) -> bool:
        """disabled フラグを無視して、インターバル条件のみを判定する。"""
        next_review = self.last_view_date + timedelta(days=self.interval)
        return datetime.now() > next_review

    def is_weak_question(self) -> bool: return (self.get_correct_rate() < WEEK_QUESTION_RATE_LIMIT) or (self.view_count <= 2)

    @abstractmethod
    def get_type(self):
        pass

    @abstractmethod
    def get_correct_answer(self):
        pass

    @abstractmethod
    def is_correct(self, user_input):
        pass
