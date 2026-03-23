# =========================
# GUI ビュー（表示層）- Kivy版
# =========================
from enum import Enum
import os
import random
from typing import Callable

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.checkbox import CheckBox
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.metrics import dp

# ==========================================
# 日本語フォント設定
# Kivy のデフォルトフォント (Roboto) を日本語対応フォントで上書きする
# ==========================================
_JP_FONT_CANDIDATES = [
    'C:/Windows/Fonts/meiryo.ttc',    # Meiryo (Windows Vista+)
    'C:/Windows/Fonts/msgothic.ttc',  # MS Gothic (Windows XP+)
    'C:/Windows/Fonts/YuGothM.ttc',   # Yu Gothic Medium (Windows 10+)
    'C:/Windows/Fonts/yugothm.ttc',   # Yu Gothic Medium (小文字パス)
]

for _font_path in _JP_FONT_CANDIDATES:
    if os.path.exists(_font_path):
        LabelBase.register('Roboto', fn_regular=_font_path)
        break


class ButtonMode(Enum):
    NOTHING = 0
    CHOICE_QUESTION = 1
    TEXT_QUESTION = 2
    FIN_ANSWER = 3
    SELF_JUDGE = 4


class _CheckItem(BoxLayout):
    """複数選択肢用の行ウィジェット（CheckBox + Label の組み合わせ）"""

    def __init__(self, text: str, **kwargs):
        super().__init__(
            orientation='horizontal',
            size_hint_y=None, height=dp(40),
            **kwargs
        )
        self.choice_text = text

        self.checkbox = CheckBox(size_hint_x=None, width=dp(40))
        self.label    = Label(text=text, halign='left', valign='middle')
        self.label.bind(size=self.label.setter('text_size'))

        self.add_widget(self.checkbox)
        self.add_widget(self.label)

    @property
    def active(self) -> bool:
        return self.checkbox.active

    def disable(self):
        self.checkbox.disabled = True

    def set_color(self, color: tuple):
        self.label.color = color


class QuizView(BoxLayout):
    """GUI ビュー（Kivy版）- quiz_gui.py と同一インターフェースを提供する"""

    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)

        # 選択肢の状態
        self._single_buttons: list[ToggleButton] = []
        self._check_items:    list[_CheckItem]   = []

        # =============================
        # コールバック（コントローラーが設定する）
        # =============================
        self.on_answer:          Callable                = lambda: None
        self.on_next:            Callable                = lambda: None
        self.on_correct:         Callable                = lambda: None
        self.on_incorrect:       Callable                = lambda: None
        self.on_explanation:     Callable                = lambda: None
        self.on_disable_changed: Callable[[bool], None]  = lambda _: None
        self.on_settings:        Callable                = lambda: None
        self.on_exit:            Callable                = lambda: None

        # ウィンドウ管理
        self._title:        str                     = "学習クイズ"
        self._close_callback: Callable | None       = None
        self._key_bindings: list[tuple]             = []
        self._app:          '_QuizApp | None'       = None

        self._build()

    # ==========================================
    # ウィジェット構築
    # ==========================================
    def _build(self):
        # ===== コンテンツエリア =====
        content = BoxLayout(
            orientation='vertical',
            size_hint_y=1,
            padding=dp(10), spacing=dp(6)
        )

        self.question_label = Label(
            text="", font_size=dp(18),
            size_hint_y=None, height=dp(90),
            halign='left', valign='top'
        )
        self.question_label.bind(
            width=lambda inst, w: setattr(inst, 'text_size', (w, None))
        )
        content.add_widget(self.question_label)

        self.stats_label = Label(
            text="", font_size=dp(13),
            size_hint_y=None, height=dp(24)
        )
        content.add_widget(self.stats_label)

        self.source_label = Label(
            text="", font_size=dp(11),
            color=(0.55, 0.55, 0.55, 1),
            size_hint_y=None, height=dp(20)
        )
        content.add_widget(self.source_label)

        self.result_label = Label(
            text="", font_size=dp(15),
            size_hint_y=None, height=dp(32)
        )
        content.add_widget(self.result_label)

        # ===== 選択肢エリア（スクロール対応）=====
        self._choices_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None, spacing=dp(4)
        )
        self._choices_layout.bind(
            minimum_height=self._choices_layout.setter('height')
        )

        choices_scroll = ScrollView(size_hint_y=1)
        choices_scroll.add_widget(self._choices_layout)
        content.add_widget(choices_scroll)

        self.add_widget(content)

        # ===== メモ入力エリア（記述問題用）=====
        self._memo_box = BoxLayout(
            size_hint_y=None, height=0,
            padding=(dp(6), 0)
        )
        self._memo_box.opacity = 0

        self.memo_entry = TextInput(
            multiline=False,
            hint_text="回答を入力してください"
        )
        self._memo_box.add_widget(self.memo_entry)
        self.add_widget(self._memo_box)

        # ===== ボタンエリア =====
        self.button_frame = BoxLayout(
            size_hint_y=None, height=dp(52),
            spacing=dp(4), padding=(dp(4), dp(4))
        )

        self.explanation_button = Button(text="解説", disabled=True)
        self.explanation_button.bind(on_release=lambda _: self.on_explanation())
        self.button_frame.add_widget(self.explanation_button)

        self.correct_button = Button(text="正解", disabled=True)
        self.correct_button.bind(on_release=lambda _: self.on_correct())
        self.button_frame.add_widget(self.correct_button)

        self.incorrect_button = Button(text="不正解", disabled=True)
        self.incorrect_button.bind(on_release=lambda _: self.on_incorrect())
        self.button_frame.add_widget(self.incorrect_button)

        self.answer_button = Button(text="回答", disabled=True)
        self.answer_button.bind(on_release=lambda _: self.on_answer())
        self.button_frame.add_widget(self.answer_button)

        self.next_button = Button(text="次へ", disabled=True)
        self.next_button.bind(on_release=lambda _: self.on_next())
        self.button_frame.add_widget(self.next_button)

        # 無効化チェックボックス（CheckBox + ラベル）
        disable_box = BoxLayout(size_hint_x=None, width=dp(90))
        self._disable_checkbox = CheckBox(
            active=False, disabled=True, size_hint_x=None, width=dp(30)
        )
        self._disable_checkbox.bind(
            active=lambda _, val: self.on_disable_changed(val)
        )
        disable_box.add_widget(self._disable_checkbox)
        disable_box.add_widget(Label(text="無効化", font_size=dp(12)))
        self.button_frame.add_widget(disable_box)

        self.settings_button = Button(text="設定")
        self.settings_button.bind(on_release=lambda _: self.on_settings())
        self.button_frame.add_widget(self.settings_button)

        self.exit_button = Button(text="終了")
        self.exit_button.bind(on_release=lambda _: self.on_exit())
        self.button_frame.add_widget(self.exit_button)

        self.add_widget(self.button_frame)

    # ==========================================
    # 問題・ステータス表示
    # ==========================================
    def show_question(self, question: str, stats_text: str, source_text: str):
        self.question_label.text = question
        self.stats_label.text    = stats_text
        self.source_label.text   = source_text

    def show_no_questions(self):
        self.question_label.text = "出題可能な問題がありません。"
        self.stats_label.text    = ""
        self.source_label.text   = ""

    def set_disabled_state(self, is_disabled: bool):
        """現在の問題の無効化チェックボックスの状態を更新する。"""
        self._disable_checkbox.active   = is_disabled
        self._disable_checkbox.disabled = False

    # ==========================================
    # 結果表示
    # ==========================================
    def reset_result(self):
        self.result_label.text  = ""
        self.result_label.color = (1, 1, 1, 1)

    def set_result(self, is_ok: bool, correct_answer: str | None = None):
        if is_ok:
            self.result_label.text  = "正解"
            self.result_label.color = (0, 0.8, 0, 1)
        elif correct_answer:
            self.result_label.text  = "正解: " + correct_answer
            self.result_label.color = (0.4, 0.6, 1.0, 1)
        else:
            self.result_label.text  = "不正解"
            self.result_label.color = (1, 0.2, 0.2, 1)

    # ==========================================
    # 選択肢
    # ==========================================
    def set_choices(self, q_type: str, choices: list[str]):
        self._clear_choices()

        if q_type == "single_choice":
            shuffled = choices.copy()
            random.shuffle(shuffled)
            for choice in shuffled:
                btn = ToggleButton(
                    text=choice, group='single_choice',
                    size_hint_y=None, height=dp(44)
                )
                self._choices_layout.add_widget(btn)
                self._single_buttons.append(btn)

        elif q_type == "multi_choice":
            shuffled = choices.copy()
            random.shuffle(shuffled)
            for choice in shuffled:
                item = _CheckItem(choice)
                self._choices_layout.add_widget(item)
                self._check_items.append(item)

    def _clear_choices(self):
        self._choices_layout.clear_widgets()
        self._single_buttons.clear()
        self._check_items.clear()

    def apply_single_choice_colors(self, correct_answer: str, selected: str):
        """正解・不正解の色付けをして全ボタンを無効化する。"""
        for btn in self._single_buttons:
            # デフォルトのグレー disabled テクスチャを除去して background_color のみで描画する
            btn.background_normal          = ''
            btn.background_down            = ''
            btn.background_disabled_normal = ''
            btn.background_disabled_down   = ''
            # disabled 時のテキスト色を明るく保つ
            btn.disabled_color = (1, 1, 1, 1)

            if btn.text == correct_answer:
                btn.background_color = (0.05, 0.75, 0.15, 1)  # 明るい緑
            elif btn.text == selected:
                btn.background_color = (0.85, 0.12, 0.12, 1)  # 明るい赤
            else:
                btn.background_color = (0.35, 0.35, 0.38, 1)  # 中間グレー
            btn.disabled = True

    def apply_multi_choice_colors(self, correct_answers: set[str], selected: list[str]):
        """正解・不正解のラベル色を変えて全チェックボックスを無効化する。"""
        for item in self._check_items:
            if item.choice_text in correct_answers:
                item.set_color((0, 0.8, 0.1, 1))
            elif item.choice_text in selected:
                item.set_color((1, 0.2, 0.2, 1))
            item.disable()

    # ==========================================
    # メモ欄
    # ==========================================
    def set_memo_visible(self, visible: bool):
        if visible:
            self.memo_entry.text    = ""
            self._memo_box.height   = dp(46)
            self._memo_box.opacity  = 1
        else:
            self._memo_box.height   = 0
            self._memo_box.opacity  = 0

    # ==========================================
    # 入力値取得
    # ==========================================
    def get_selected_single(self) -> str:
        for btn in self._single_buttons:
            if btn.state == 'down':
                return btn.text
        return ""

    def get_selected_multi(self) -> list[str]:
        return [item.choice_text for item in self._check_items if item.active]

    def get_memo_text(self) -> str:
        return self.memo_entry.text

    # ==========================================
    # ボタン有効/無効制御
    # ==========================================
    def set_button_mode(self, mode: ButtonMode):
        # True = disabled, False = enabled
        configs = {
            ButtonMode.TEXT_QUESTION:   dict(correct=True,  incorrect=True,  answer=False, next=True),
            ButtonMode.CHOICE_QUESTION: dict(correct=True,  incorrect=True,  answer=False, next=True),
            ButtonMode.FIN_ANSWER:      dict(correct=True,  incorrect=True,  answer=True,  next=False),
            ButtonMode.SELF_JUDGE:      dict(correct=False, incorrect=False, answer=True,  next=True),
            ButtonMode.NOTHING:         dict(correct=True,  incorrect=True,  answer=True,  next=True),
        }
        s = configs.get(mode, configs[ButtonMode.NOTHING])

        self.correct_button.disabled   = s['correct']
        self.incorrect_button.disabled = s['incorrect']
        self.answer_button.disabled    = s['answer']
        self.next_button.disabled      = s['next']
        if mode == ButtonMode.NOTHING:
            self._disable_checkbox.disabled = True

    def set_button_mode_with_explanation(self, mode: ButtonMode, has_explanation: bool = False):
        self.set_button_mode(mode)
        self.explanation_button.disabled = not has_explanation

    # ==========================================
    # ポップアップ
    # ==========================================
    def show_explanation_window(self, explanation: str):
        content = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(8))

        scroll = ScrollView(size_hint_y=1)
        text   = TextInput(
            text=explanation, readonly=True, multiline=True,
            size_hint_y=None
        )
        text.bind(minimum_height=text.setter('height'))
        scroll.add_widget(text)
        content.add_widget(scroll)

        close_btn = Button(text="閉じる", size_hint_y=None, height=dp(44))
        content.add_widget(close_btn)

        popup = Popup(title="解説", content=content, size_hint=(0.85, 0.85))
        close_btn.bind(on_release=popup.dismiss)
        popup.open()

    def open_settings_dialog(
        self,
        all_sources: list[str],
        enabled_sources: set[str],
        rate_filter_enabled: bool,
        rate_filter_threshold: float,
        on_apply: Callable[[set[str], bool, float], None],
    ):
        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))

        content.add_widget(Label(
            text="出題するソースファイルを選択してください",
            size_hint_y=None, height=dp(28), font_size=dp(13)
        ))

        # ===== ソースチェックボックス一覧（スクロール対応）=====
        source_list = BoxLayout(
            orientation='vertical', size_hint_y=None, spacing=dp(2)
        )
        source_list.bind(minimum_height=source_list.setter('height'))

        check_vars: dict[str, CheckBox] = {}
        for source in all_sources:
            row = BoxLayout(size_hint_y=None, height=dp(36))
            cb  = CheckBox(
                active=(source in enabled_sources),
                size_hint_x=None, width=dp(40)
            )
            lbl = Label(text=source, halign='left', valign='middle')
            lbl.bind(size=lbl.setter('text_size'))
            row.add_widget(cb)
            row.add_widget(lbl)
            source_list.add_widget(row)
            check_vars[source] = cb

        scroll = ScrollView(size_hint_y=1)
        scroll.add_widget(source_list)
        content.add_widget(scroll)

        # 全て有効 / 全て無効
        bulk_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        btn_all_on  = Button(text="全て有効")
        btn_all_off = Button(text="全て無効")
        btn_all_on.bind(
            on_release=lambda _: [setattr(cb, 'active', True)  for cb in check_vars.values()]
        )
        btn_all_off.bind(
            on_release=lambda _: [setattr(cb, 'active', False) for cb in check_vars.values()]
        )
        bulk_row.add_widget(btn_all_on)
        bulk_row.add_widget(btn_all_off)
        content.add_widget(bulk_row)

        # ===== セパレーター =====
        content.add_widget(Label(
            text="─" * 40, size_hint_y=None, height=dp(14),
            color=(0.5, 0.5, 0.5, 1)
        ))

        # ===== 正答率フィルター =====
        filter_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(4))
        filter_cb  = CheckBox(
            active=rate_filter_enabled, size_hint_x=None, width=dp(40)
        )
        filter_row.add_widget(filter_cb)
        filter_row.add_widget(Label(text="正答率が", size_hint_x=None, width=dp(72)))
        threshold_input = TextInput(
            text=str(int(rate_filter_threshold * 100)),
            multiline=False, input_filter='int',
            size_hint_x=None, width=dp(54)
        )
        filter_row.add_widget(threshold_input)
        filter_row.add_widget(Label(text="% 以下の問題のみ出題する"))
        content.add_widget(filter_row)

        # ===== 適用 / キャンセル =====
        btn_row    = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        apply_btn  = Button(text="適用")
        cancel_btn = Button(text="キャンセル")
        btn_row.add_widget(apply_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(btn_row)

        popup = Popup(
            title="ソース設定", content=content,
            size_hint=(0.85, 0.9), auto_dismiss=False
        )

        def _apply(_):
            try:
                threshold = max(0, min(100, int(threshold_input.text))) / 100
            except ValueError:
                threshold = rate_filter_threshold
            on_apply(
                {s for s, cb in check_vars.items() if cb.active},
                filter_cb.active,
                threshold,
            )
            popup.dismiss()

        apply_btn.bind(on_release=_apply)
        cancel_btn.bind(on_release=popup.dismiss)
        popup.open()

    # ==========================================
    # ウィンドウ管理
    # ==========================================
    def set_title(self, title: str):
        self._title = title
        Window.set_title(title)

    def set_close_callback(self, callback: Callable):
        self._close_callback = callback
        Window.bind(on_request_close=self._on_window_close)

    def _on_window_close(self, *args):
        if self._close_callback:
            self._close_callback()
        return True  # 自動クローズを抑止（コールバック側で quit() を呼ぶ）

    def bind_key(self, key: str, callback: Callable):
        """tkinter 形式のキー文字列 '<Control-s>' などを受け付ける。"""
        key_code, modifier = self._parse_key_string(key)
        if key_code is not None:
            self._key_bindings.append((key_code, modifier, callback))
            Window.bind(on_key_down=self._on_key_down)

    def _parse_key_string(self, key_str: str) -> tuple[int | None, str | None]:
        """'<Control-s>' → (115, 'ctrl') のように変換する。"""
        stripped = key_str.strip('<>')
        parts    = [p.lower() for p in stripped.split('-')]
        modifier = None
        if 'control' in parts or 'ctrl' in parts:
            modifier = 'ctrl'
        elif 'alt' in parts:
            modifier = 'alt'
        elif 'shift' in parts:
            modifier = 'shift'
        char = parts[-1]
        return (ord(char), modifier) if len(char) == 1 else (None, None)

    def _on_key_down(self, window, key, scancode, codepoint, modifiers):
        for key_code, modifier, callback in self._key_bindings:
            mod_match = (modifier is None) or (modifier in modifiers)
            if key == key_code and mod_match:
                callback(None)

    def quit(self):
        if self._app:
            self._app.stop()

    def mainloop(self):
        self._app = _QuizApp(self, title=self._title)
        self._app.run()


# ==========================================
# Kivy アプリケーション本体（内部クラス）
# ==========================================
class _QuizApp(App):
    def __init__(self, view: QuizView, title: str = "学習クイズ", **kwargs):
        super().__init__(**kwargs)
        self._view = view
        self.title = title

    def build(self) -> QuizView:
        return self._view
