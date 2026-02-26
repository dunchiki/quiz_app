# =========================
# 抽象基底クラス
# =========================

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum

from quiz_config import RECENT_ANSWER_COUNT, WEEK_QUESTION_RATE_LIMIT

class Stats(Enum):
    Count = "count"
    Disabled = "disabled"
    ResentResults = "resent_results"
    Interval = "Interval"
    LastViewDate = "last_view_date"

# 問題固有の処理はできるだけこれを継承したクラス内に実装する
class Question(ABC):
    view_count = 0
    disabled = False
    resent_results = []
    interval = 0
    last_view_date: datetime = None

    def __init__(self, question, source_file):
        self.question = question
        self.source_file = source_file

    def set_stats(self, stats):
        if not stats: stats = {}
        default_stats: dict = {
            Stats.Count.value: 0,
            Stats.Disabled.value: False,
            Stats.ResentResults.value: [False, False, False, False, False],
            Stats.Interval.value: 0,
            Stats.LastViewDate.value: datetime.now()
        }
        self.view_count = int(stats[Stats.Count.value]) if Stats.Count.value in stats else default_stats[Stats.Count.value]
        self.disabled = bool(stats[Stats.Disabled.value]) if Stats.Disabled.value in stats else default_stats[Stats.Disabled.value]
        self.resent_results = list[bool](stats[Stats.ResentResults.value]) if Stats.ResentResults.value in stats else default_stats[Stats.ResentResults.value]
        self.interval = int(stats[Stats.Interval.value]) if Stats.Interval.value in stats else default_stats[Stats.Interval.value]
        self.last_view_date = datetime.fromisoformat(stats[Stats.LastViewDate.value]) if Stats.LastViewDate.value in stats else default_stats[Stats.LastViewDate.value]

    def update_stats(self, is_correct: bool):
        self.last_view_date = datetime.now()
        self.view_count += 1

        self.resent_results.append(is_correct)
        if len(self.resent_results) > RECENT_ANSWER_COUNT:
            self.resent_results.pop(0)

        self.interval = (self.interval + 1 if self.is_weak_question() else max(1.0, self.interval * 1.5)) if is_correct else 1

    def get_stats(self):
        return {
            Stats.Count.value: self.view_count,
            Stats.Disabled.value: self.disabled,
            Stats.ResentResults.value: self.resent_results,
            Stats.Interval.value: self.interval,
            Stats.LastViewDate.value: self.last_view_date.isoformat(timespec="seconds")
        }

    def get_correct_rate(self) -> float:
        if len(self.resent_results) == 0:
            return 0.0
        correct_count = len([b for b in self.resent_results if b])
        wrong_count = len([b for b in self.resent_results if not b])
        return correct_count / (correct_count + wrong_count)
    
    def get_weight(self) -> float:
        elapsed_day = (datetime.now() - self.last_view_date).total_seconds() / (60 * 60 * 24)
        return elapsed_day / self.interval if (self.interval > 0) else 5.0
    
    def is_enable(self):
        next_review = self.last_view_date + timedelta(days=self.interval)
        return (not self.disabled) and (datetime.now() > next_review)

    def is_weak_question(self) -> bool: return self.get_correct_rate() < WEEK_QUESTION_RATE_LIMIT

    @abstractmethod
    def get_type(self):
        pass

    @abstractmethod
    def get_correct_answer(self):
        pass

    @abstractmethod
    def is_correct(self, user_input):
        pass
