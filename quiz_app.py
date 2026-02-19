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
STATS_FOLDER = 'stats'
RECENT_EXCLUDE_COUNT = 10
EMA_DEFAULT = 0.0

class NormalQuestionModel:
    question: str = None
    answer: str = None
    source_file: str = None
    score_ema: float = 0
    answer_count: int = 0
    weight: float = 0

    def __init__(self, q, a, s):
        self.question = q
        self.answer = a
        self.source_file = s
        pass

    def set_stats(self, score, count):
        self.score_ema = score
        self.answer_count = count
        self.__update_waight()

    def update_stats(self, is_ok: bool):
        self.answer_count += 1
        score: float = 1.0 if is_ok else 0.0
        self.score_ema = ALPHA * score + (1 - ALPHA) * self.score_ema
        self.__update_waight()

    def __update_waight(self):
        self.weight = max(1.0 - self.score_ema, 0.1) * (1.0 / (self.answer_count + 1))

class QuestionList:
    question_dict: dict[str, list[NormalQuestionModel]] = None
    csv_files: list[str] = None

    def __init__(self):
        data_path = os.path.join(os.path.dirname(__file__), DATA_FOLDER)
        self.csv_files = glob(os.path.join(data_path, '*.csv'))

        self.question_dict = {}
        for csv_file in self.csv_files:
            # csv 読み込み
            q = self.__load_csv(csv_file)

            # stat 読み込み
            stat_file = self.__csv_to_stat_file(csv_file)
            self.question_dict[csv_file] = self.__load_stat(stat_file, q)
        pass

    def get_questions(self):
        r = []
        for q_list in self.question_dict.values():
            r.extend(q_list)
        return r
    
    def save_stats(self):
        for f in self.question_dict.keys():
            self.__save_stats_impl(f)

    def __csv_to_stat_file(self, csv: str) -> str:
        return os.path.join(STATS_FOLDER, f"{os.path.splitext(csv)[0]}.json") # TODO パスが stats/ ではなく data/ になるバグ

    def __load_csv(self, csv_file: str) -> list[NormalQuestionModel]:
        question: list[NormalQuestionModel] = []
        with open(csv_file, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2 and not(row[0] == "問題"):
                    question.append(NormalQuestionModel(row[0].strip(), row[1].strip(), os.path.basename(csv_file)))
        return question

    def __load_stat(self, stat_file: str, question: list[NormalQuestionModel]) -> list[NormalQuestionModel]:
        if os.path.exists(stat_file):
            with open(stat_file, 'r', encoding='utf-8') as f:
                stat_dict = json.load(f)
        else:
            stat_dict = {}

        for q in question:
            question_stats = stat_dict.get(q.question, {"ema": EMA_DEFAULT, "count": 0})
            q.set_stats(float(question_stats["ema"]), int(question_stats["count"]))
        return question
    
    def __save_stats_impl(self, csv_file: str):
        stat_file = self.__csv_to_stat_file(csv_file)
        q_list: list[NormalQuestionModel] = self.question_dict[csv_file]
        stat = {q.question: {"ema": q.score_ema, "count": q.answer_count} for q in q_list}
        print(f"save stat to {stat_file}")
        with open(stat_file, 'w', encoding='utf-8') as f:
            json.dump(stat, f, ensure_ascii=False, indent=2)
        

def load_all_questions() -> list[NormalQuestionModel]:
    question_list = []
    data_path = os.path.join(os.path.dirname(__file__), DATA_FOLDER)
    csv_files = glob(os.path.join(data_path, '*.csv'))

    for file in csv_files:
        try:
            with open(file, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2 and not(row[0] == "問題"):
                        question_list.append(NormalQuestionModel(row[0].strip(), row[1].strip(), os.path.basename(file)))
        except Exception as e:
            print(f"読み込みエラー: {file}: {e}")

    return question_list

def load_stats(data_file, questions: list[NormalQuestionModel]):
    def load_stats_impl(file):
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    stats = os.path.join(STATS_FOLDER, f"{os.path.splitext(data_file)[0]}.json")
    r = load_stats_impl(stats)
    for q in questions:
        question_stats = r[q.question]
        q.set_stats(float(question_stats["ema"]), int(question_stats["count"]))
    return questions

class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("学習クイズ")
        self.all_quesstion_list = QuestionList()
        self.questions = self.all_quesstion_list.get_questions()
        self.recent_history = []
        self.current_question: NormalQuestionModel = None

        if not self.questions:
            messagebox.showerror("エラー", f"{DATA_FOLDER}/ に有効なCSVファイルが見つかりませんでした。")
            root.quit()
            return

        self.construct_gui()

        self.next_question()

    def construct_gui(self):
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

        self.correct_button = tk.Button(root, text="正解", command=lambda: self.mark_answer(True))
        self.correct_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.incorrect_button = tk.Button(root, text="不正解", command=lambda: self.mark_answer(False))
        self.incorrect_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.exit_button = tk.Button(root, text="終了", command=self.on_fin)
        self.exit_button.pack(side=tk.RIGHT, padx=10, pady=10)

    def on_fin(self):
        self.all_quesstion_list.save_stats()
        print("stat saved")
        self.root.quit()

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

    def next_question(self):
        question = self.get_random_question()
        self.set_new_question(question)

        self.recent_history.append(self.current_question.question)
        if len(self.recent_history) > RECENT_EXCLUDE_COUNT:
            self.recent_history.pop(0)

    def show_answer(self):
        self.answer_label.config(text=self.current_question.answer)

    def mark_answer(self, is_ok):
        self.current_question.update_stats(is_ok)
        self.next_question()

    def set_new_question(self, question: NormalQuestionModel):
        self.current_question = question

        self.answer_label.config(text="")
        if not self.current_question:
            self.question_label.config(text="出題条件に合う問題がありません。")
            self.rate_label.config(text="")
            self.source_label.config(text="")
            return

        self.question_label.config(text=self.current_question.question)
        self.rate_label.config(
            text=f"スコア: {self.current_question.score_ema * 100:.1f}% 回答回数: {self.current_question.answer_count}")
        self.source_label.config(text=f"出典: {self.current_question.source_file}")

    def get_random_question(self):
        weighted_pool: list[NormalQuestionModel] = []
        for question_info in self.questions:
            if question_info.question in self.recent_history:
                continue
            weighted_pool.append(question_info)

        if not weighted_pool:
            return None

        return random.choices(
            weighted_pool,
            weights=[q.weight for q in weighted_pool]
        )[0]

if __name__ == "__main__":
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()
