import tkinter as tk
from tkinter import messagebox
import csv
import random
import json
import os
from glob import glob

STATS_FILE = 'stats.json'
ALPHA = 0.3
DATA_FOLDER = 'data'
RECENT_EXCLUDE_COUNT = 10


class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("学習クイズ")
        self.questions = self.load_all_questions()  # (question, answer, filename) を保持
        self.stats = self.load_stats()
        self.recent_history = []
        self.current_question = None
        self.current_answer = None
        self.current_source = None

        if not self.questions:
            messagebox.showerror("エラー", f"{DATA_FOLDER}/ に有効なCSVファイルが見つかりませんでした。")
            root.quit()
            return

        # GUI構築
        self.question_label = tk.Label(
            root, text="問題を表示します", font=('Arial', 16),
            wraplength=600, justify='left'
        )
        self.question_label.pack(pady=20)

        self.rate_label = tk.Label(root, text="", font=('Arial', 12))
        self.rate_label.pack()

        self.source_label = tk.Label(root, text="", font=('Arial', 10), fg="gray")
        self.source_label.pack()

        self.answer_label = tk.Label(
            root, text="", font=('Arial', 14), fg="blue",
            wraplength=600, justify='left'
        )
        self.answer_label.pack(pady=10)

        self.show_answer_button = tk.Button(root, text="解答を表示", command=self.show_answer)
        self.show_answer_button.pack(pady=5)

        self.correct_button = tk.Button(root, text="正解だった", command=lambda: self.mark_answer(True))
        self.correct_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.incorrect_button = tk.Button(root, text="不正解だった", command=lambda: self.mark_answer(False))
        self.incorrect_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.exit_button = tk.Button(root, text="終了", command=root.quit)
        self.exit_button.pack(side=tk.RIGHT, padx=10, pady=10)

        self.next_question()

    def load_all_questions(self):
        question_list = []
        data_path = os.path.join(os.path.dirname(__file__), DATA_FOLDER)
        csv_files = glob(os.path.join(data_path, '*.csv'))

        for file in csv_files:
            try:
                with open(file, newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2:
                            question_list.append((row[0].strip(), row[1].strip(), os.path.basename(file)))
            except Exception as e:
                print(f"読み込みエラー: {file}: {e}")

        return question_list

    def load_stats(self):
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_stats(self):
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)

    def next_question(self):
        self.answer_label.config(text="")

        weighted_pool = []
        for q, a, src in self.questions:
            if q in self.recent_history:
                continue

            stat = self.stats.get(q, {"ema": 0.5, "count": 0})
            ema = stat["ema"]
            count = stat["count"]
            weight = max(1.0 - ema, 0.1) * (1.0 / (count + 1))
            weighted_pool.append(((q, a, src), weight))

        if not weighted_pool:
            self.question_label.config(text="出題条件に合う問題がありません。")
            self.rate_label.config(text="")
            self.source_label.config(text="")
            return

        (self.current_question, self.current_answer, self.current_source), _ = random.choices(
            weighted_pool,
            weights=[w for _, w in weighted_pool]
        )[0]

        stat = self.stats.get(self.current_question, {"ema": 0.5, "count": 0})
        self.question_label.config(text=self.current_question)
        self.rate_label.config(
            text=f"スコア: {stat['ema'] * 100:.1f}% 回答回数: {stat['count']}")
        self.source_label.config(text=f"出典: {self.current_source}")

        self.recent_history.append(self.current_question)
        if len(self.recent_history) > RECENT_EXCLUDE_COUNT:
            self.recent_history.pop(0)

    def show_answer(self):
        self.answer_label.config(text=self.current_answer)

    def mark_answer(self, correct):
        key = self.current_question
        stat = self.stats.get(key, {"ema": 0.5, "count": 0})
        score = 1.0 if correct else 0.0
        stat["ema"] = ALPHA * score + (1 - ALPHA) * stat["ema"]
        stat["count"] += 1
        self.stats[key] = stat
        self.save_stats()
        self.next_question()


if __name__ == "__main__":
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()
