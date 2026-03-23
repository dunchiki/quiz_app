# =========================
# quiz_data.py のユニットテスト
# =========================
import csv
import json
import os
import pytest

from py_package.data_interface.quiz_data import QuestionDataInterface
from py_package.question_models.single_choice import SingleChoiceQuestion
from py_package.question_models.multi_choice import MultiChoiceQuestion
from py_package.question_models.text_question import TextQuestion
from py_package.utils.quiz_field import QuizField


@pytest.fixture
def interface():
    """__init__ を呼ばずに QuestionDataInterface のインスタンスを作成する。"""
    inst = object.__new__(QuestionDataInterface)
    inst.loaded_files = []
    inst.loaded_question_dict = {}
    return inst


# ==========================================
# load_csv
# ==========================================
class TestLoadCsv:
    def test_loads_valid_rows(self, tmp_path, interface):
        csv_file = tmp_path / "q.csv"
        csv_file.write_text("問題,答え\nQ1,A1\nQ2,A2\n", encoding="utf-8")
        questions = interface.load_csv(str(csv_file))
        assert len(questions) == 2
        assert all(isinstance(q, TextQuestion) for q in questions)

    def test_skips_header_row(self, tmp_path, interface):
        csv_file = tmp_path / "q.csv"
        csv_file.write_text("問題,答え\nQ1,A1\n", encoding="utf-8")
        questions = interface.load_csv(str(csv_file))
        assert len(questions) == 1
        assert questions[0].question == "Q1"

    def test_source_file_is_basename(self, tmp_path, interface):
        csv_file = tmp_path / "myfile.csv"
        csv_file.write_text("問題,答え\nQ1,A1\n", encoding="utf-8")
        questions = interface.load_csv(str(csv_file))
        assert questions[0].source_file == "myfile.csv"

    def test_skips_short_rows(self, tmp_path, interface):
        csv_file = tmp_path / "q.csv"
        csv_file.write_text("問題\nQ1,A1\n", encoding="utf-8")
        # 1列のみの行はスキップ、2列目以降がないため1件
        questions = interface.load_csv(str(csv_file))
        assert len(questions) == 1

    def test_strips_whitespace(self, tmp_path, interface):
        csv_file = tmp_path / "q.csv"
        csv_file.write_text("問題,答え\n  Q1 ,  A1 \n", encoding="utf-8")
        questions = interface.load_csv(str(csv_file))
        assert questions[0].question == "Q1"
        assert questions[0].answer == "A1"


# ==========================================
# load_json
# ==========================================
class TestLoadJson:
    def _write_json(self, tmp_path, data, name="q.json"):
        p = tmp_path / name
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return str(p)

    def test_loads_text_type(self, tmp_path, interface):
        path = self._write_json(tmp_path, [
            {"type": "text", "question": "Q1", "answer": "A1"}
        ])
        questions = interface.load_json(path)
        assert len(questions) == 1
        assert isinstance(questions[0], TextQuestion)

    def test_loads_single_choice_type(self, tmp_path, interface):
        path = self._write_json(tmp_path, [
            {"type": "single_choice", "question": "Q1", "choices": ["*A", "B"]}
        ])
        questions = interface.load_json(path)
        assert isinstance(questions[0], SingleChoiceQuestion)

    def test_loads_multi_choice_type(self, tmp_path, interface):
        path = self._write_json(tmp_path, [
            {"type": "multi_choice", "question": "Q1", "choices": ["*A", "*B", "C"]}
        ])
        questions = interface.load_json(path)
        assert isinstance(questions[0], MultiChoiceQuestion)

    def test_default_type_is_text(self, tmp_path, interface):
        """type フィールドがない場合は TextQuestion になる。"""
        path = self._write_json(tmp_path, [
            {"question": "Q1", "answer": "A1"}
        ])
        questions = interface.load_json(path)
        assert isinstance(questions[0], TextQuestion)

    def test_source_file_is_basename(self, tmp_path, interface):
        path = self._write_json(tmp_path, [
            {"question": "Q1", "answer": "A1"}
        ], name="mydata.json")
        questions = interface.load_json(path)
        assert questions[0].source_file == "mydata.json"

    def test_multiple_questions_loaded(self, tmp_path, interface):
        path = self._write_json(tmp_path, [
            {"question": "Q1", "answer": "A1"},
            {"question": "Q2", "answer": "A2"},
        ])
        questions = interface.load_json(path)
        assert len(questions) == 2


# ==========================================
# get_questions
# ==========================================
class TestGetQuestions:
    def _make_text_q(self, question="Q", answer="A", source="src.json", disabled=False):
        item = {QuizField.Question.value: question, QuizField.Answer.value: answer}
        q = TextQuestion(item, source)
        q.set_stats(None)
        q.disabled = disabled
        return q

    def test_returns_all_when_enabled_sources_is_none(self, interface):
        q1 = self._make_text_q(source="a.json")
        q2 = self._make_text_q(source="b.json")
        interface.loaded_question_dict = {"path/a.json": [q1], "path/b.json": [q2]}
        result = interface.get_questions(None)
        assert len(result) == 2

    def test_filters_by_enabled_sources(self, interface):
        q1 = self._make_text_q(source="a.json")
        q2 = self._make_text_q(source="b.json")
        interface.loaded_question_dict = {"path/a.json": [q1], "path/b.json": [q2]}
        result = interface.get_questions({"a.json"})
        assert len(result) == 1
        assert result[0].source_file == "a.json"

    def test_excludes_disabled_questions(self, interface):
        q1 = self._make_text_q(disabled=True)
        q2 = self._make_text_q()
        interface.loaded_question_dict = {"path/q.json": [q1, q2]}
        result = interface.get_questions(None)
        assert len(result) == 1
        assert result[0].disabled is False

    def test_empty_when_source_not_enabled(self, interface):
        q = self._make_text_q(source="a.json")
        interface.loaded_question_dict = {"path/a.json": [q]}
        result = interface.get_questions({"b.json"})
        assert result == []


# ==========================================
# get_all_source_basenames
# ==========================================
class TestGetAllSourceBasenames:
    def test_returns_basenames(self, interface):
        interface.loaded_question_dict = {
            "c:/data/file1.json": [],
            "c:/data/file2.json": [],
        }
        result = interface.get_all_source_basenames()
        assert set(result) == {"file1.json", "file2.json"}

    def test_empty_when_no_files(self, interface):
        interface.loaded_question_dict = {}
        assert interface.get_all_source_basenames() == []
