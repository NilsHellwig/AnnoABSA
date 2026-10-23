"""Input validation, atomic writes and spreadsheet-safe export."""
import csv
import json
import os

import pytest

from conftest import read_json
from data_io import (DataFileError, check_data_file, export_csv, read_data, spreadsheet_safe,
                     write_data)


def write(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return str(path)


@pytest.mark.parametrize("content,message", [
    ('[{"text": "a"},\n {"text": "b",}]', "not valid JSON (line 2"),
    ('', "not valid JSON"),
    ('{"text": "a"}', "must contain a JSON list"),
    ('["a", "b"]', "entry 0 must be a JSON object"),
    ('[{"label": []}]', "entry 0: missing or non-string 'text'"),
    ('[{"text": 5}]', "entry 0: missing or non-string 'text'"),
    ('[{"text": "a", "label": "x"}]', "entry 0: 'label' must be a list"),
    ('[{"text": "a", "label": [1]}]', "tuple 0 in 'label' must be an object"),
])
def test_malformed_json_is_reported(tmp_path, content, message):
    problems = check_data_file(write(tmp_path, "bad.json", content))
    assert problems and message in problems[0]


@pytest.mark.parametrize("content,message", [
    ("", "is empty"),
    ("sentence,label\na,\n", "no 'text' column"),
    ('text,label\na,"[{broken"\n', "row 2: 'label' is not valid JSON"),
    ('text,label\na,"{""a"": 1}"\n', "'label' must be a list"),
    ('text,label\n"unterminated,\n', "not a valid CSV file"),
])
def test_malformed_csv_is_reported(tmp_path, content, message):
    problems = check_data_file(write(tmp_path, "bad.csv", content))
    assert problems and message in problems[0]


def test_non_utf8_file_is_reported(tmp_path):
    path = tmp_path / "latin1.csv"
    path.write_bytes("text\nCaf\xe9\n".encode("latin-1"))
    assert "not UTF-8 encoded" in check_data_file(str(path))[0]


def test_missing_file_is_reported(tmp_path):
    assert "not found" in check_data_file(str(tmp_path / "nope.json"))[0]


def test_valid_examples_pass(json_file, csv_file):
    assert check_data_file(json_file) == []
    assert check_data_file(csv_file) == []


def test_problem_list_is_capped(tmp_path):
    path = write(tmp_path, "many.json", json.dumps([{"label": "x"}] * 50))
    assert len(check_data_file(path)) == 10


@pytest.mark.parametrize("name,content", [("bad.json", "[1"), ("bad.csv", "")])
def test_malformed_file_returns_422_with_message(make_client, tmp_path, name, content):
    client = make_client(write(tmp_path, name, content))
    for r in (client.get("/settings"), client.get("/data/0"),
              client.post("/annotations/0", json={"name": "a", "value": []})):
        assert r.status_code == 422
        assert r.json()["detail"].startswith("Invalid data file:")


def test_write_is_atomic_and_keeps_permissions(tmp_path):
    path = write(tmp_path, "d.json", "[]")
    os.chmod(path, 0o640)
    write_data(path, "json", [{"text": "ä"}])
    assert read_json(path) == [{"text": "ä"}]
    assert os.stat(path).st_mode & 0o777 == 0o640
    assert [p for p in os.listdir(tmp_path) if p.endswith(".tmp")] == []


def test_failed_write_leaves_original_intact(tmp_path):
    path = write(tmp_path, "d.json", '[{"text": "old"}]')
    with pytest.raises(TypeError):
        write_data(path, "json", [{"text": object()}])
    assert read_json(path) == [{"text": "old"}]
    assert [p for p in os.listdir(tmp_path) if p.endswith(".tmp")] == []


@pytest.mark.parametrize("value,expected", [
    ("=1+1", "'=1+1"), ("+49 123", "'+49 123"), ("-2 bad", "'-2 bad"), ("@SUM(A1)", "'@SUM(A1)"),
    ("\t=1", "'\t=1"), ("\r=1", "'\r=1"), ("fine", "fine"), ("a=b", "a=b"), ("", ""), (5, 5), (None, None),
])
def test_spreadsheet_safe(value, expected):
    assert spreadsheet_safe(value) == expected


def test_export_neutralises_formulas_in_all_columns(tmp_path):
    src = write(tmp_path, "f.json", json.dumps([
        {"text": '=HYPERLINK("http://x","click")', "note": "@cmd", "label": [{"aspect_term": "=x"}]},
        {"text": "normal", "label": []},
    ]))
    out = str(tmp_path / "out.csv")
    assert export_csv(src, out) == 2
    with open(out, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["text"] == "'=HYPERLINK(\"http://x\",\"click\")"
    assert rows[0]["note"] == "'@cmd"
    assert json.loads(rows[0]["label"]) == [{"aspect_term": "=x"}]  # JSON cell starts with "["
    assert rows[1]["text"] == "normal"
    assert all(not v.startswith(("=", "+", "-", "@")) for row in rows for v in row.values())
    assert read_json(src)[0]["text"].startswith("=HYPERLINK")  # source untouched


def test_export_refuses_to_overwrite_source(csv_file):
    with pytest.raises(DataFileError):
        export_csv(csv_file, csv_file)


def test_read_data_adds_missing_label_column(tmp_path):
    df = read_data(write(tmp_path, "x.csv", "text\na\n"), "csv")
    assert list(df.columns) == ["text", "label"]
