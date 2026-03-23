# =========================
# GUI アプリケーション（制御層）
# =========================
from quiz_config import GUI_BACKEND
from py_package.set_question_models.set_question_model import QuizModel
from py_package.utils.quiz_field import QuizField
from py_package.utils.stats import Stats

if GUI_BACKEND == 'kivy':
    from py_package.gui.quiz_view_kivy import ButtonMode, QuizView
else:
    from py_package.gui.quiz_view import ButtonMode, QuizView

class QuizApp:
    def __init__(self):
        self.quiz_model = QuizModel()
        self.view = QuizView()

        self.view.set_close_callback(self.on_exit)

        # コールバックをビューに登録
        self.view.on_answer      = self.check_answer
        self.view.on_next        = self.next_question
        self.view.on_correct     = lambda: self.manual_answer(True)
        self.view.on_incorrect   = lambda: self.manual_answer(False)
        self.view.on_explanation = self.show_explanation
        self.view.on_disable_changed = lambda val: self.quiz_model.set_cq_disabled(val)
        self.view.on_settings    = self.open_settings
        self.view.on_exit        = self.on_exit

        self.view.bind_key("<Control-s>", lambda event: self.quiz_model.save())
        self.next_question()

    def next_question(self):
        self.quiz_model.set_random_question()
        self.view.reset_result()

        if not self.quiz_model.is_cq_set:
            self.view.show_no_questions()
            self.view.set_button_mode(ButtonMode.NOTHING)
            return

        quiz_field    = self.quiz_model.cq_quiz_field
        q_type        = self.quiz_model.cq_type
        choices       = quiz_field.get(QuizField.Choices.value) or []
        has_exp       = bool(quiz_field[QuizField.Explanation.value])
        stats         = self.quiz_model.cq_stats
        num_not_ans   = self.quiz_model.get_num_not_answered_questions()
        num_enable    = self.quiz_model.get_num_enable_questions_with_rate_filter()
        num_enable_str         = f"{num_enable}" if num_not_ans == 0 else f"{num_enable}({num_not_ans})"

        self.view.show_question(
            question    = quiz_field[QuizField.Question.value],
            stats_text  = f"直近正答率: {self.quiz_model.cq_correct_rate * 100:.1f}  回答回数: {stats[Stats.Count.value]}",
            source_text = f"出典: {self.quiz_model.cq_source_file},  有効問題数: {num_enable_str},  本日回答数: {self.quiz_model.get_num_today_answer_questions()}"
        )
        self.view.set_choices(q_type, choices)
        self.view.set_memo_visible(q_type == "text")
        self.view.set_disabled_state(self.quiz_model.cq_disabled)

        if q_type == "text":
            self.view.set_button_mode_with_explanation(ButtonMode.TEXT_QUESTION, has_exp)
        else:
            self.view.set_button_mode_with_explanation(ButtonMode.CHOICE_QUESTION, has_exp)

    def open_settings(self):
        enabled, threshold = self.quiz_model.get_rate_filter()

        def on_apply(new_enabled: set[str], rate_enabled: bool, rate_threshold: float):
            self.quiz_model.reload_questions(new_enabled)
            self.quiz_model.set_rate_filter(rate_enabled, rate_threshold)
            self.next_question()

        self.view.open_settings_dialog(
            all_sources           = self.quiz_model.get_all_source_files(),
            enabled_sources       = self.quiz_model.get_enabled_sources(),
            rate_filter_enabled   = enabled,
            rate_filter_threshold = threshold,
            on_apply              = on_apply,
        )

    def manual_answer(self, is_ok):
        if not self.quiz_model.is_cq_set:
            return

        self.quiz_model.update_cq_stats(is_ok)
        self.next_question()

    def show_explanation(self):
        if not self.quiz_model.is_cq_set:
            return
        explanation = self.quiz_model.cq_quiz_field[QuizField.Explanation.value]
        if not explanation:
            return
        self.view.show_explanation_window(explanation)

    def check_answer(self):
        assert self.quiz_model.is_cq_set

        q_type = self.quiz_model.cq_type

        # =========================
        # 単一選択問題
        # =========================
        if q_type == "single_choice":
            selected       = self.view.get_selected_single()
            is_ok          = bool(selected) and self.quiz_model.is_correct_answer(selected)
            correct_answer = self.quiz_model.cq_quiz_field[QuizField.Answer.value]
            self.view.apply_single_choice_colors(correct_answer, selected)
            self.quiz_model.update_cq_stats(is_ok)
            self.view.set_button_mode(ButtonMode.FIN_ANSWER)
            self.view.set_result(is_ok, None if is_ok else correct_answer)

        # =========================
        # 複数選択問題
        # =========================
        elif q_type == "multi_choice":
            selected        = self.view.get_selected_multi()
            is_ok           = self.quiz_model.is_correct_answer(selected)
            correct_answers = self.quiz_model.cq_quiz_field[QuizField.Answer.value]
            self.view.apply_multi_choice_colors(correct_answers, selected)
            self.quiz_model.update_cq_stats(is_ok)
            self.view.set_button_mode(ButtonMode.FIN_ANSWER)
            self.view.set_result(is_ok, None if is_ok else ', '.join(correct_answers))

        # =========================
        # 記述問題
        # =========================
        elif q_type == "text":
            answer = self.view.get_memo_text()
            is_ok  = self.quiz_model.is_correct_answer(answer)
            if is_ok:
                self.quiz_model.update_cq_stats(True)
                self.view.set_button_mode(ButtonMode.FIN_ANSWER)
                self.view.set_result(True)
            else:
                correct_answer = self.quiz_model.cq_quiz_field[QuizField.Answer.value]
                self.view.set_button_mode(ButtonMode.SELF_JUDGE)
                self.view.set_result(False, correct_answer)

    def on_exit(self):
        self.quiz_model.save()
        self.view.quit()

    def start(self):
        self.view.mainloop()
