# =========================
# GUI ビュー（表示層）
# =========================
from enum import Enum
import tkinter as tk
import random
from typing import Callable


class ButtonMode(Enum):
    NOTHING = 0
    CHOICE_QUESTION = 1
    TEXT_QUESTION = 2
    FIN_ANSWER = 3
    SELF_JUDGE = 4


class QuizView:
    question_font = ('Arial', 16)
    result_font   = ('Arial', 14, 'bold')
    answer_font   = ('Arial', 14)
    stats_font    = ('Arial', 12)
    info_font     = ('Arial', 10)

    def __init__(self, root: tk.Tk):
        self.root = root

        # 選択肢の状態
        self.selected_choice = tk.StringVar()
        self.choice_buttons: list[tk.Widget] = []
        self.selected_vars: list[tuple[tk.BooleanVar, str]] = []

        # =============================
        # コールバック（コントローラーが設定する）
        # =============================
        self.on_answer:          Callable         = lambda: None
        self.on_next:            Callable         = lambda: None
        self.on_correct:         Callable         = lambda: None
        self.on_incorrect:       Callable         = lambda: None
        self.on_explanation:     Callable         = lambda: None
        self.on_disable_changed: Callable[[bool], None] = lambda _: None
        self.on_settings:        Callable         = lambda: None
        self.on_exit:            Callable         = lambda: None

        self._disabled_var = tk.BooleanVar(value=False)

        self._build()

    # ==========================================
    # ウィジェット構築
    # ==========================================
    def _build(self):
        # ===== コンテンツエリア =====
        self.content_frame = tk.Frame(self.root)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        self.question_label = tk.Label(
            self.content_frame, font=self.question_font,
            wraplength=600, justify='left'
        )
        self.question_label.pack(pady=20)

        self.stats_label = tk.Label(self.content_frame, font=self.stats_font)
        self.stats_label.pack()

        self.source_label = tk.Label(
            self.content_frame, font=self.info_font, fg="gray"
        )
        self.source_label.pack()

        self.result_label = tk.Label(self.content_frame, font=self.result_font)
        self.result_label.pack(pady=5)

        # ===== メモ入力エリア（記述問題用）=====
        self.memo_frame = tk.Frame(self.root)
        self.memo_frame.pack(fill=tk.X, padx=10, pady=5)

        self.memo_entry = tk.Entry(self.memo_frame)
        self.memo_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.memo_frame.pack_forget()   # 初期状態では非表示

        # ===== ボタンエリア =====
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        self.explanation_button = tk.Button(
            self.button_frame, text="解説",
            command=lambda: self.on_explanation(), state=tk.DISABLED
        )
        self.explanation_button.pack(side=tk.LEFT, padx=5)

        self.correct_button = tk.Button(
            self.button_frame, text="正解",
            command=lambda: self.on_correct()
        )
        self.correct_button.pack(side=tk.LEFT, padx=5)

        self.incorrect_button = tk.Button(
            self.button_frame, text="不正解",
            command=lambda: self.on_incorrect()
        )
        self.incorrect_button.pack(side=tk.LEFT, padx=5)

        self.answer_button = tk.Button(
            self.button_frame, text="回答",
            command=lambda: self.on_answer()
        )
        self.answer_button.pack(side=tk.LEFT, padx=5)

        self.next_button = tk.Button(
            self.button_frame, text="次へ",
            command=lambda: self.on_next()
        )
        self.next_button.pack(side=tk.LEFT, padx=5)

        self.disable_check = tk.Checkbutton(
            self.button_frame, text="無効化",
            variable=self._disabled_var,
            command=lambda: self.on_disable_changed(self._disabled_var.get())
        )
        self.disable_check.pack(side=tk.LEFT, padx=5)

        self.settings_button = tk.Button(
            self.button_frame, text="設定",
            command=lambda: self.on_settings()
        )
        self.settings_button.pack(side=tk.LEFT, padx=5)

        self.exit_button = tk.Button(
            self.button_frame, text="終了",
            command=lambda: self.on_exit()
        )
        self.exit_button.pack(side=tk.RIGHT, padx=5)

    # ==========================================
    # 問題・ステータス表示
    # ==========================================
    def show_question(self, question: str, stats_text: str, source_text: str):
        self.question_label.config(text=question)
        self.stats_label.config(text=stats_text)
        self.source_label.config(text=source_text)

    def show_no_questions(self):
        self.question_label.config(text="出題可能な問題がありません。")
        self.stats_label.config(text="")
        self.source_label.config(text="")

    def set_disabled_state(self, is_disabled: bool):
        """現在の問題の無効化チェックボックスの状態を更新する。"""
        self._disabled_var.set(is_disabled)
        self.disable_check.config(state=tk.NORMAL)

    # ==========================================
    # 結果表示
    # ==========================================
    def reset_result(self):
        self.result_label.config(text="", fg="black")

    def set_result(self, is_ok: bool, correct_answer: str | None = None):
        if is_ok:
            self.result_label.config(text="正解", fg="green", font=self.result_font)
        elif correct_answer:
            self.result_label.config(
                text="正解: " + correct_answer, fg="blue", font=self.answer_font
            )
        else:
            self.result_label.config(text="不正解", fg="red", font=self.result_font)

    # ==========================================
    # 選択肢
    # ==========================================
    def set_choices(self, q_type: str, choices: list[str]):
        self._clear_choices()

        if q_type == "single_choice":
            self.selected_choice.set("")
            shuffled = choices.copy()
            random.shuffle(shuffled)
            for choice in shuffled:
                rb = tk.Radiobutton(
                    self.root, text=choice,
                    variable=self.selected_choice, value=choice,
                )
                rb.pack(pady=2)
                self.choice_buttons.append(rb)

        elif q_type == "multi_choice":
            self.selected_vars = []
            shuffled = choices.copy()
            random.shuffle(shuffled)
            for choice in shuffled:
                var = tk.BooleanVar()
                cb = tk.Checkbutton(text=choice, variable=var)
                cb.pack(anchor='center')
                self.choice_buttons.append(cb)
                self.selected_vars.append((var, choice))

    def _clear_choices(self):
        for btn in self.choice_buttons:
            btn.destroy()
        self.choice_buttons.clear()

    def apply_single_choice_colors(self, correct_answer: str, selected: str):
        for rb in self.choice_buttons:
            value = rb.cget("text")
            if value == correct_answer:
                rb.config(disabledforeground="green")
            if value == selected and value != correct_answer:
                rb.config(disabledforeground="red")
            rb.config(state=tk.DISABLED)

    def apply_multi_choice_colors(self, correct_answers: set[str], selected: list[str]):
        for cb in self.choice_buttons:
            text = cb.cget("text")
            if text in correct_answers:
                cb.config(disabledforeground="green")
            if text in selected and text not in correct_answers:
                cb.config(disabledforeground="red")
            cb.config(state=tk.DISABLED)

    # ==========================================
    # メモ欄
    # ==========================================
    def set_memo_visible(self, visible: bool):
        if visible:
            self.memo_entry.delete(0, tk.END)
            self.memo_frame.pack(fill=tk.X, padx=10, pady=5)
        else:
            self.memo_frame.pack_forget()

    # ==========================================
    # 入力値取得
    # ==========================================
    def get_selected_single(self) -> str:
        return self.selected_choice.get()

    def get_selected_multi(self) -> list[str]:
        return [choice for var, choice in self.selected_vars if var.get()]

    def get_memo_text(self) -> str:
        return self.memo_entry.get()

    # ==========================================
    # ボタン有効/無効制御
    # ==========================================
    def set_button_mode(self, mode: ButtonMode):
        _DISABLED = tk.DISABLED
        _NORMAL   = tk.NORMAL

        configs = {
            ButtonMode.TEXT_QUESTION:   dict(correct=_DISABLED, incorrect=_DISABLED, answer=_NORMAL,   next=_DISABLED),
            ButtonMode.CHOICE_QUESTION: dict(correct=_DISABLED, incorrect=_DISABLED, answer=_NORMAL,   next=_DISABLED),
            ButtonMode.FIN_ANSWER:      dict(correct=_DISABLED, incorrect=_DISABLED, answer=_DISABLED, next=_NORMAL),
            ButtonMode.SELF_JUDGE:      dict(correct=_NORMAL,   incorrect=_NORMAL,   answer=_DISABLED, next=_DISABLED),
            ButtonMode.NOTHING:         dict(correct=_DISABLED, incorrect=_DISABLED, answer=_DISABLED, next=_DISABLED),
        }
        s = configs.get(mode, configs[ButtonMode.NOTHING])

        self.correct_button.config(state=s['correct'])
        self.incorrect_button.config(state=s['incorrect'])
        self.answer_button.config(state=s['answer'])
        self.next_button.config(state=s['next'])
        if mode == ButtonMode.NOTHING:
            self.disable_check.config(state=tk.DISABLED)

    def set_button_mode_with_explanation(self, mode: ButtonMode, has_explanation: bool = False):
        _DISABLED = tk.DISABLED
        _NORMAL   = tk.NORMAL
        self.set_button_mode(mode)
        self.explanation_button.config(state=_NORMAL if has_explanation else _DISABLED)

    # ==========================================
    # ポップアップ
    # ==========================================
    def show_explanation_window(self, explanation: str):
        window = tk.Toplevel(self.root)
        window.title("解説")
        text = tk.Text(window, wrap=tk.WORD)
        text.insert(tk.END, explanation)
        text.config(state=tk.DISABLED)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def open_settings_dialog(
        self,
        all_sources: list[str],
        enabled_sources: set[str],
        on_apply: Callable[[set[str]], None],
    ):
        win = tk.Toplevel(self.root)
        win.title("ソース設定")
        win.resizable(False, False)
        win.grab_set()  # モーダル

        tk.Label(
            win, text="出題するソースファイルを選択してください",
            font=('Arial', 11, 'bold')
        ).pack(padx=16, pady=(12, 6))

        frame = tk.Frame(win)
        frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)

        vars_: dict[str, tk.BooleanVar] = {}
        for source in all_sources:
            var = tk.BooleanVar(value=(source in enabled_sources))
            vars_[source] = var
            tk.Checkbutton(frame, text=source, variable=var, anchor='w').pack(fill=tk.X)

        def _apply():
            on_apply({s for s, v in vars_.items() if v.get()})
            win.destroy()

        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=(8, 12))
        tk.Button(btn_frame, text="適用",     width=10, command=_apply).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_frame, text="キャンセル", width=10, command=win.destroy).pack(side=tk.LEFT, padx=6)
