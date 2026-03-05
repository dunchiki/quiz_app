# =========================
# GUI
# =========================
import tkinter as tk
import random

from py_package.question_models.question import Question
from py_package.set_question_models.set_question_model import QuizModel
from py_package.utils.quiz_field import QuizField
from py_package.utils.stats import Stats

class QuizApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("学習クイズ")
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

        self.quiz_model = QuizModel()

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

        # ===== メモ入力エリア（記述問題用）=====
        self.memo_frame = tk.Frame(self.root)
        self.memo_frame.pack(fill=tk.X, padx=10, pady=5)

        self.memo_label = tk.Label(self.memo_frame, text="メモ:")
        self.memo_label.pack(side=tk.LEFT)

        self.memo_entry = tk.Entry(self.memo_frame)
        self.memo_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 初期状態では非表示
        self.memo_frame.pack_forget()

        # ===== ボタンエリア =====
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        self.show_answer_button = tk.Button(
            self.button_frame, text="解答表示",
            command=self.show_answer
        )
        self.show_answer_button.pack(side=tk.LEFT, padx=5)

        self.explanation_button = tk.Button(
            self.button_frame,
            text="解説",
            command=self.show_explanation,
            state=tk.DISABLED
        )
        self.explanation_button.pack(side=tk.LEFT, padx=5)

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
        self.quiz_model.set_cq_disabled(True)

    def next_question(self):
        self.set_new_question()

    def set_new_question(self):
        self.quiz_model.set_random_question()
        quiz_field = self.quiz_model.cq_quiz_field
        current_question = quiz_field[QuizField.Question.value]
        choices = quiz_field.get(QuizField.Choices.value)
        explanation = quiz_field[QuizField.Explanation.value]

        stats = self.quiz_model.cq_stats
        count = stats[Stats.Count.value]

        self.answer_label.config(text="")
        self.result_label.config(text="", fg="black")
        self.clear_choices()
        self.next_button.config(state=tk.DISABLED)

        if not self.quiz_model.is_cq_set:
            self.question_label.config(text="出題可能な問題がありません。")
            self.rate_label.config(text="")
            self.source_label.config(text="")
            self.explanation_button.config(state=tk.DISABLED)
            return

        self.question_label.config(text=current_question)
        self.rate_label.config(
            text=f"直近正答率: {self.quiz_model.cq_correct_rate * 100:.1f} 回答回数: {count}"
        )
        
        self.source_label.config(text=f"出典: {self.quiz_model.cq_source_file}, 有効問題数: {self.quiz_model.get_num_enable_questions()}, 本日回答数: {self.quiz_model.get_num_today_answer_questions()}")

        if self.quiz_model.cq_type == "single_choice":
            self.memo_frame.pack_forget()
            self.correct_button.config(state=tk.DISABLED)
            self.incorrect_button.config(state=tk.DISABLED)
            self.answer_button.config(state=tk.DISABLED)

            choices = choices.copy()
            random.shuffle(choices)
            self.selected_choice.set("")

            def enable_answer():
                self.answer_button.config(state=tk.NORMAL)

            for choice in choices:
                rb = tk.Radiobutton(
                    self.root,
                    text=choice,
                    variable=self.selected_choice,
                    value=choice,
                    command=enable_answer
                )
                rb.pack(pady=2)
                self.choice_buttons.append(rb)

        elif self.quiz_model.cq_type == "multi_choice":
            self.memo_frame.pack_forget()
            self.correct_button.config(state=tk.DISABLED)
            self.incorrect_button.config(state=tk.DISABLED)
            self.answer_button.config(state=tk.NORMAL)

            self.selected_vars = []
            choices = choices.copy()
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

        else: # 記述問題
            self.correct_button.config(state=tk.NORMAL)
            self.incorrect_button.config(state=tk.NORMAL)
            self.answer_button.config(state=tk.DISABLED)

            # メモ欄表示
            self.memo_entry.delete(0, tk.END)
            self.memo_frame.pack(fill=tk.X, padx=10, pady=5)

        # 解説ボタン制御
        if explanation:
            self.explanation_button.config(state=tk.NORMAL)
        else:
            self.explanation_button.config(state=tk.DISABLED)

    def show_answer(self):
        if self.quiz_model.is_cq_set:
            self.answer_label.config(
                text=self.quiz_model.cq_quiz_field[QuizField.Answer.value]
            )

    def manual_answer(self, is_ok):
        if not self.quiz_model.is_cq_set:
            return
        if self.quiz_model.cq_type != "text":
            return

        self.quiz_model.update_cq_stats(is_ok)
        self.next_question()

    def show_explanation(self):
        if not self.quiz_model.is_cq_set:
            return

        explanation = self.quiz_model.cq_quiz_field[QuizField.Explanation.value]
        if not explanation:
            return

        window = tk.Toplevel(self.root)
        window.title("解説")

        text = tk.Text(window, wrap=tk.WORD)
        text.insert(tk.END, explanation)
        text.config(state=tk.DISABLED)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def check_answer(self):
        assert self.quiz_model.is_cq_set

        q_type = self.quiz_model.cq_type
        # assert q_type == "text" # 記述問題はここに来ない

        # =========================
        # 単一選択問題
        # =========================
        if q_type == "single_choice":

            selected = self.selected_choice.get()
            assert selected

            is_ok = self.quiz_model.is_correct_answer(selected)
            correct_answer = self.quiz_model.cq_quiz_field[QuizField.Answer.value]

            for rb in self.choice_buttons:
                value = rb.cget("text")

                if value == correct_answer:
                    rb.config(disabledforeground="green")

                if value == selected and not is_ok:
                    rb.config(disabledforeground="red")

                rb.config(state=tk.DISABLED)

            self.quiz_model.update_cq_stats(is_ok)

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

            is_ok = self.quiz_model.is_correct_answer(selected)
            correct_answers = self.quiz_model.cq_quiz_field[QuizField.Answer.value]

            for cb in self.choice_buttons:
                text = cb.cget("text")

                if text in correct_answers:
                    cb.config(disabledforeground="green")

                if text in selected and text not in correct_answers:
                    cb.config(disabledforeground="red")

                cb.config(state=tk.DISABLED)
            
            correct_answer = ', '.join(correct_answers)

            self.quiz_model.update_cq_stats(is_ok)

            self.answer_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.NORMAL)

        if is_ok:
            self.result_label.config(text="正解", fg="green")
        else:
            self.result_label.config(
                text=f"不正解\n正解: {correct_answer}" if q_type == "text" else "不正解",
                fg="red"
            )

    def on_exit(self):
        self.quiz_model.save()
        self.root.quit()

    def start(self):
        self.root.mainloop()