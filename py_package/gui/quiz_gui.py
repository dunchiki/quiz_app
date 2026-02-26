# =========================
# GUI
# =========================
import tkinter as tk
import random

from py_package.question_models.question import Question
from py_package.set_question_models.set_question_model import QuizModel

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
            self.rate_label.config(text="")
            self.source_label.config(text="")
            return

        self.question_label.config(text=question.question)
        self.rate_label.config(
            text=f"直近正答率: {question.get_correct_rate() * 100:.1f} 回答回数: {question.view_count}"
        )
        self.source_label.config(text=f"出典: {question.source_file}, 有効問題数: {self.quiz_model.get_num_enable_questions()}")

        if question.get_type() == "single_choice":
            self.memo_frame.pack_forget()
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
            self.memo_frame.pack_forget()
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

        else: # 記述問題
            self.correct_button.config(state=tk.NORMAL)
            self.incorrect_button.config(state=tk.NORMAL)
            self.answer_button.config(state=tk.DISABLED)

            # メモ欄表示
            self.memo_entry.delete(0, tk.END)
            self.memo_frame.pack(fill=tk.X, padx=10, pady=5)

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