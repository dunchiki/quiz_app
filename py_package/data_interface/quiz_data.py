# =========================
# データロード
# =========================
import csv
from glob import glob
import json
import os

from py_package.utils.app_paths import get_data_dir, get_stats_dir
from py_package.utils.quiz_field import QuizField
from py_package.question_models.multi_choice import MultiChoiceQuestion
from py_package.question_models.question import Question
from py_package.question_models.single_choice import SingleChoiceQuestion
from py_package.question_models.text_question import TextQuestion

class QuestionDataInterface:
    def __init__(self):
        stats_dir = get_stats_dir()
        os.makedirs(stats_dir, exist_ok=True)

        data_path = get_data_dir()
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

    def get_all_source_basenames(self) -> list[str]:
        """ロード済みファイルのベース名一覧を返す。"""
        return [os.path.basename(fp) for fp in self.loaded_question_dict.keys()]

    def get_questions(self, enabled_sources: set[str] | None = None) -> list[Question]:
        """
        enabled_sources が None の場合は全ファイルを対象とする。
        指定した場合はそのファイル名（basename）に含まれるものだけを返す。
        """
        result: list[Question] = []
        for file_path, q_list in self.loaded_question_dict.items():
            if enabled_sources is not None and os.path.basename(file_path) not in enabled_sources:
                continue
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
                    item = {
                        QuizField.Question.value: q,
                        QuizField.Answer.value: a,
                    }
                    questions.append(TextQuestion(item, os.path.basename(csv_file)))
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
            score_min = 1.0
            count_answer = 0
            c = 0
            for q in questions:
                if not q.disabled:
                    score_sum += q.get_correct_rate()
                    if q.get_correct_rate() < score_min:
                        score_min = q.get_correct_rate()
                    count_answer += q.view_count
                    c += 1
            
            stat = {
                q.question: q.get_stats() for q in questions
            }
            if c > 0:
                score_avg = score_sum / c
                stat["score_avg"] = score_avg
                print(f"平均正答率 {score_avg * 100:5.1f}, 最低正答率 {score_min * 100:5.1f}, 平均回答数 {count_answer / c:4.1f}, {questions[0].source_file}")

            with open(stat_file, 'w', encoding='utf-8') as f:
                json.dump(stat, f, ensure_ascii=False, indent=2)

    def __file_to_stat_file(self, file_path):
        base = os.path.splitext(os.path.basename(file_path))[0]
        return os.path.join(get_stats_dir(), f"{base}.json")
