import tkinter as tk
import csv
import random
import json
import os
from glob import glob
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum

ALPHA = 0.4
DATA_FOLDER = 'data'
STATS_FOLDER = 'stats'
RECENT_EXCLUDE_COUNT = 10
EMA_DEFAULT = 0.0
WEEK_QUESTION_RATE_LIMIT = 0.4

class Stats(Enum):
    Count = "count"
    Disabled = "disabled"
    ResentResults = "resent_results"
    Interval = "Interval"
    LastViewDate = "last_view_date"

# =========================
# 抽象基底クラス
# =========================

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
        if len(self.resent_results) > RECENT_EXCLUDE_COUNT:
            self.resent_results.pop(0)

        self.interval = (self.interval + 1 if self.is_weak_question() else self.interval * 1.5) if is_correct else 1

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
        next_review = self.last_view_date + timedelta(days=self.interval)
        return max(1.0, (datetime.now() - next_review).total_seconds() / (60 * 60 * 24))
    
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


# =========================
# 記述問題
# =========================
class TextQuestion(Question):
    def __init__(self, item, source_file):
        question = item.get("question").strip()
        answer = item.get("answer").strip()

        super().__init__(question, source_file)
        self.answer = answer

    def get_type(self):
        return "text"

    def get_correct_answer(self):
        return self.answer

    def is_correct(self, user_input):
        return None


# =========================
# 単一選択問題
# =========================
class SingleChoiceQuestion(Question):
    def __init__(self, item, source_file):
        question = item.get("question").strip()
        choices = item.get("choices", [])

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
    

# =========================
# 複数選択問題
# =========================
class MultiChoiceQuestion(Question):
    def __init__(self, item, source_file):
        question = item.get("question").strip()
        choices = item.get("choices", [])

        super().__init__(question, source_file)

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


# =========================
# データロード
# =========================
class QuestionDataInterface:
    def __init__(self):
        os.makedirs(STATS_FOLDER, exist_ok=True)

        data_path = os.path.join(os.path.dirname(__file__), DATA_FOLDER)
        self.loaded_files = (
            glob(os.path.join(data_path, '*.csv')) +
            glob(os.path.join(data_path, '*.json'))
        )

        self.loaded_question_dict: dict[str, list[Question]] = {}

        for file_path in self.loaded_files:
            if file_path.endswith(".csv"):
                questions = self.load_csv(file_path)
            elif file_path.endswith(".json"):
                questions = self.load_json(file_path)
            else:
                continue

            self.loaded_question_dict[file_path] = questions
            self.load_stats(file_path)

    def get_questions(self) -> list[Question]:
        result: list[Question] = []
        for q_list in self.loaded_question_dict.values():
            result.extend(q_list)
        result = [q for q in result if not q.disabled]
        return result

    # 文章題専用
    def load_csv(self, csv_file):
        questions = []
        with open(csv_file, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2 and row[0] != "問題":
                    q = row[0].strip()
                    a = row[1].strip()
                    questions.append(
                        TextQuestion(
                            q, a, os.path.basename(csv_file)
                        )
                    )
        return questions

    def load_json(self, json_file):
        questions = []
        source_file = os.path.basename(json_file)

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for item in data:
            q_type = item.get("type", "text")

            if q_type == "multi_choice":
                questions.append(MultiChoiceQuestion(item, source_file))
            elif q_type == "single_choice":
                questions.append(SingleChoiceQuestion(item, source_file))
            else:
                # 記述問題
                questions.append(TextQuestion(item, source_file))

        return questions

    def load_stats(self, file_path):
        stat_file = self.__file_to_stat_file(file_path)
        questions: list[Question] = self.loaded_question_dict[file_path]

        if os.path.exists(stat_file):
            with open(stat_file, 'r', encoding='utf-8') as f:
                stat_dict = json.load(f)
        else:
            stat_dict = {}

        for q in questions:
            stats = stat_dict.get(q.question, None)
            q.set_stats(stats)

    def save_stats(self):
        for file_path, questions in self.loaded_question_dict.items():
            stat_file = self.__file_to_stat_file(file_path)

            score_sum = 0
            c = 0
            for q in questions:
                if not q.disabled:
                    score_sum += q.get_correct_rate()
                    c += 1
            
            stat = {
                q.question: q.get_stats() for q in questions
            }
            if c > 0:
                score_avg = score_sum / c
                stat["score_avg"] = score_avg
                print(f"{questions[0].source_file} : {score_avg * 100:.1f}")

            with open(stat_file, 'w', encoding='utf-8') as f:
                json.dump(stat, f, ensure_ascii=False, indent=2)

    def __file_to_stat_file(self, file_path):
        base = os.path.splitext(os.path.basename(file_path))[0]
        return os.path.join(STATS_FOLDER, f"{base}.json")


# =========================
# クイズモデル
# =========================
class QuizModel:
    def __init__(self):
        self.question_data = QuestionDataInterface()
        self.question_list: list[Question] = self.question_data.get_questions()

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


# =========================
# GUI
# =========================
class QuizApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("学習クイズ")

        self.quiz_model = QuizModel()
        self.current_question: Question = None

        self.selected_choice = tk.StringVar()
        self.choice_buttons = []

        self.construct_gui()
        self.next_question()

    def construct_gui(self):

        # ===== コンテンツエリア =====
        self.content_frame = tk.Frame(self.root)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        self.question_label = tk.Label(
            self.content_frame, font=('Arial', 16),
            wraplength=600, justify='left'
        )
        self.question_label.pack(pady=20)

        self.rate_label = tk.Label(self.content_frame, font=('Arial', 12))
        self.rate_label.pack()

        self.source_label = tk.Label(
            self.content_frame,
            font=('Arial', 10),
            fg="gray"
        )
        self.source_label.pack()

        self.answer_label = tk.Label(
            self.content_frame,
            font=('Arial', 14),
            fg="blue",
            wraplength=600,
            justify='left'
        )
        self.answer_label.pack(pady=10)

        self.result_label = tk.Label(
            self.content_frame,
            font=('Arial', 14, 'bold')
        )
        self.result_label.pack(pady=5)

        # ===== ボタンエリア =====
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        self.show_answer_button = tk.Button(
            self.button_frame, text="解答表示",
            command=self.show_answer
        )
        self.show_answer_button.pack(side=tk.LEFT, padx=5)

        self.correct_button = tk.Button(
            self.button_frame, text="正解",
            command=lambda: self.manual_answer(True)
        )
        self.correct_button.pack(side=tk.LEFT, padx=5)

        self.incorrect_button = tk.Button(
            self.button_frame, text="不正解",
            command=lambda: self.manual_answer(False)
        )
        self.incorrect_button.pack(side=tk.LEFT, padx=5)

        self.answer_button = tk.Button(
            self.button_frame, text="回答する",
            command=self.check_answer
        )
        self.answer_button.pack(side=tk.LEFT, padx=5)

        self.next_button = tk.Button(
            self.button_frame, text="次へ",
            command=self.next_question
        )
        self.next_button.pack(side=tk.LEFT, padx=5)
        self.next_button.config(state=tk.DISABLED)

        self.disable_button = tk.Button(
            self.button_frame, text="無効化",
            command=self.on_click_disable_button
        )
        self.disable_button.pack(side=tk.LEFT, padx=5)

        self.exit_button = tk.Button(
            self.button_frame, text="終了",
            command=self.on_exit
        )
        self.exit_button.pack(side=tk.RIGHT, padx=5)

    def clear_choices(self):
        for btn in self.choice_buttons:
            btn.destroy()
        self.choice_buttons.clear()

    def on_click_disable_button(self):
        self.current_question.disabled = True

    def next_question(self):
        question = self.quiz_model.get_random_question()
        self.set_new_question(question)

    def set_new_question(self, question: Question):
        self.current_question = question
        self.answer_label.config(text="")
        self.result_label.config(text="", fg="black")
        self.clear_choices()
        self.next_button.config(state=tk.DISABLED)

        if not question:
            self.question_label.config(text="出題可能な問題がありません。")
            return

        self.question_label.config(text=question.question)
        self.rate_label.config(
            text=f"直近正答率: {question.get_correct_rate() * 100:.1f} 回答回数: {question.view_count}"
        )
        self.source_label.config(text=f"出典: {question.source_file}")

        if question.get_type() == "single_choice":
            self.correct_button.config(state=tk.DISABLED)
            self.incorrect_button.config(state=tk.DISABLED)
            self.answer_button.config(state=tk.DISABLED)

            choices = question.choices.copy()
            random.shuffle(choices)
            self.selected_choice.set("")

            def enable_answer():
                self.answer_button.config(state=tk.NORMAL)

            for choice in question.choices:
                rb = tk.Radiobutton(
                    self.root,
                    text=choice,
                    variable=self.selected_choice,
                    value=choice,
                    command=enable_answer
                )
                rb.pack(pady=2)
                self.choice_buttons.append(rb)

        elif question.get_type() == "multi_choice":
            self.correct_button.config(state=tk.DISABLED)
            self.incorrect_button.config(state=tk.DISABLED)
            self.answer_button.config(state=tk.NORMAL)

            self.selected_vars = []
            choices = question.choices.copy()
            random.shuffle(choices)

            for choice in choices:
                var = tk.BooleanVar()
                cb = tk.Checkbutton(
                    text=choice,
                    variable=var
                )
                cb.pack(anchor='center')
                self.choice_buttons.append(cb)
                self.selected_vars.append((var, choice))

        else:
            self.correct_button.config(state=tk.NORMAL)
            self.incorrect_button.config(state=tk.NORMAL)
            self.answer_button.config(state=tk.DISABLED)

    def show_answer(self):
        if self.current_question:
            self.answer_label.config(
                text=self.current_question.get_correct_answer()
            )

    def manual_answer(self, is_ok):
        if not self.current_question:
            return
        if self.current_question.get_type() != "text":
            return

        self.current_question.update_stats(is_ok)
        self.next_question()

    def check_answer(self):
        assert self.current_question

        q_type = self.current_question.get_type()
        # assert q_type == "text" # 記述問題はここに来ない

        # =========================
        # 単一選択問題
        # =========================
        if q_type == "single_choice":

            selected = self.selected_choice.get()
            assert selected

            is_ok = self.current_question.is_correct(selected)
            correct_answer = self.current_question.get_correct_answer()

            for rb in self.choice_buttons:
                value = rb.cget("text")

                if value == correct_answer:
                    rb.config(fg="green")

                if value == selected and not is_ok:
                    rb.config(fg="red")

                rb.config(state=tk.DISABLED)

            self.current_question.update_stats(is_ok)

            self.answer_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.NORMAL)

        # =========================
        # 複数選択問題
        # =========================
        if q_type == "multi_choice":

            selected = [
                choice for var, choice in self.selected_vars
                if var.get()
            ]

            is_ok = self.current_question.is_correct(selected)
            correct_answers = self.current_question.correct_answers

            for cb in self.choice_buttons:
                text = cb.cget("text")

                if text in correct_answers:
                    cb.config(fg="green")

                if text in selected and text not in correct_answers:
                    cb.config(fg="red")

                cb.config(state=tk.DISABLED)
            
            correct_answer = ', '.join(correct_answers)

            self.current_question.update_stats(is_ok)

            self.answer_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.NORMAL)

        if is_ok:
            self.result_label.config(text="正解", fg="green")
        else:
            self.result_label.config(
                text=f"不正解\n正解: {correct_answer}",
                fg="red"
            )

    def on_exit(self):
        self.quiz_model.save()
        self.root.quit()

    def start(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = QuizApp()
    app.start()