import tkinter as tk
import csv
import random
import json
import os
from glob import glob
from abc import ABC, abstractmethod

ALPHA = 0.3
DATA_FOLDER = 'data'
STATS_FOLDER = 'stats'
RECENT_EXCLUDE_COUNT = 5
EMA_DEFAULT = 0.0


# =========================
# 抽象基底クラス
# =========================
class Question(ABC):
    def __init__(self, question, source_file):
        self.question = question
        self.source_file = source_file
        self.score_ema = 0.0
        self.answer_count = 0
        self.weight = 1.0

    def set_stats(self, score, count):
        self.score_ema = score
        self.answer_count = count
        self._update_weight()

    def update_stats(self, is_ok: bool):
        self.answer_count += 1
        score = 1.0 if is_ok else 0.0
        self.score_ema = ALPHA * score + (1 - ALPHA) * self.score_ema
        self._update_weight()

    def _update_weight(self):
        self.weight = max(1.0 - self.score_ema, 0.1) * (1.0 / (self.answer_count + 1))

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
    def __init__(self, question, answer, source_file):
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
    def __init__(self, question, answer, choices, source_file):
        super().__init__(question, source_file)
        self.answer = answer
        self.choices = choices
        print(f"0000000000000 {choices}")

    def get_type(self):
        return "single_choice"

    def get_correct_answer(self):
        return self.answer

    def is_correct(self, user_input):
        return user_input == self.answer


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

        self.loaded_question_dict = {}

        for file_path in self.loaded_files:
            if file_path.endswith(".csv"):
                questions = self.load_csv(file_path)
            elif file_path.endswith(".json"):
                questions = self.load_json(file_path)
            else:
                continue

            self.loaded_question_dict[file_path] = questions
            self.load_stats(file_path)

    def get_questions(self):
        result = []
        for q_list in self.loaded_question_dict.values():
            result.extend(q_list)
        return result

    def load_csv(self, csv_file):
        questions = []
        with open(csv_file, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2 and row[0] != "問題":
                    q = row[0].strip()
                    a = row[1].strip()
                    choices = [c.strip() for c in row[2:] if c.strip()]

                    if len(choices) >= 2:
                        questions.append(
                            SingleChoiceQuestion(
                                q, a, choices, os.path.basename(csv_file)
                            )
                        )
                    else:
                        questions.append(
                            TextQuestion(
                                q, a, os.path.basename(csv_file)
                            )
                        )
        return questions

    def load_json(self, json_file):
        questions = []
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for item in data:
            q = item.get("question")
            a = item.get("answer")
            q_type = item.get("type", "text")
            choices = item.get("choices", [])

            if not q or not a:
                continue

            if q_type == "single_choice":
                questions.append(
                    SingleChoiceQuestion(
                        q.strip(),
                        a.strip(),
                        choices,
                        os.path.basename(json_file)
                    )
                )
            else:
                questions.append(
                    TextQuestion(
                        q.strip(),
                        a.strip(),
                        os.path.basename(json_file)
                    )
                )
        return questions

    def load_stats(self, file_path):
        stat_file = self.__file_to_stat_file(file_path)
        questions = self.loaded_question_dict[file_path]

        if os.path.exists(stat_file):
            with open(stat_file, 'r', encoding='utf-8') as f:
                stat_dict = json.load(f)
        else:
            stat_dict = {}

        for q in questions:
            stats = stat_dict.get(
                q.question,
                {"ema": EMA_DEFAULT, "count": 0}
            )
            q.set_stats(float(stats["ema"]), int(stats["count"]))

    def save_stats(self):
        for file_path, questions in self.loaded_question_dict.items():
            stat_file = self.__file_to_stat_file(file_path)

            stat = {
                q.question: {
                    "ema": q.score_ema,
                    "count": q.answer_count
                }
                for q in questions
            }

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
        self.question_list = self.question_data.get_questions()
        self.recent_history = []

    def get_random_question(self):
        weighted_pool = [
            q for q in self.question_list
            if q.question not in self.recent_history
        ]

        if not weighted_pool:
            return None

        result = random.choices(
            weighted_pool,
            weights=[q.weight for q in weighted_pool]
        )[0]

        self.recent_history.append(result.question)
        if len(self.recent_history) > RECENT_EXCLUDE_COUNT:
            self.recent_history.pop(0)

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
        self.current_question = None

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

        self.exit_button = tk.Button(
            self.button_frame, text="終了",
            command=self.on_exit
        )
        self.exit_button.pack(side=tk.RIGHT, padx=5)

    def clear_choices(self):
        for btn in self.choice_buttons:
            btn.destroy()
        self.choice_buttons.clear()

    def next_question(self):
        question = self.quiz_model.get_random_question()
        self.set_new_question(question)

    def set_new_question(self, question):
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
            text=f"正答率: {question.score_ema * 100:.1f}% 回答回数: {question.answer_count}"
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
                rb.pack(anchor='w')
                self.choice_buttons.append(rb)

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
        if not self.current_question:
            return
        if self.current_question.get_type() != "single_choice":
            return

        selected = self.selected_choice.get()
        if not selected:
            return

        is_ok = self.current_question.is_correct(selected)
        correct_answer = self.current_question.get_correct_answer()

        for rb in self.choice_buttons:
            value = rb.cget("value")

            if value == correct_answer:
                rb.config(fg="green")

            if value == selected and not is_ok:
                rb.config(fg="red")

            rb.config(state=tk.DISABLED)

        if is_ok:
            self.result_label.config(text="正解です！", fg="green")
        else:
            self.result_label.config(
                text=f"不正解です。正解は: {correct_answer}",
                fg="red"
            )

        self.current_question.update_stats(is_ok)

        self.answer_button.config(state=tk.DISABLED)
        self.next_button.config(state=tk.NORMAL)

    def on_exit(self):
        self.quiz_model.save()
        self.root.quit()

    def start(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = QuizApp()
    app.start()