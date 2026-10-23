"""Command-line interface."""
import csv

import pytest

from cli import default_allowed_origins
from conftest import run_cli
from data_io import file_type_for, read_data
from version import __version__


def test_version_flag():
    r = run_cli("--version")
    assert r.returncode == 0
    assert r.stdout.strip() == f"annoabsa {__version__}"


@pytest.mark.parametrize("content,message", [
    ("[1", "not valid JSON"),
    ('[{"text": "a", "label": "x"}]', "'label' must be a list"),
])
def test_malformed_file_is_refused_before_start(tmp_path, content, message):
    path = tmp_path / "bad.json"
    path.write_text(content)
    r = run_cli(str(path), "--backend")
    assert r.returncode == 1
    assert "is malformed" in r.stdout and message in r.stdout


def test_missing_and_unsupported_files(tmp_path):
    assert "not found" in run_cli(str(tmp_path / "x.json")).stdout
    txt = tmp_path / "x.txt"
    txt.write_text("a")
    assert "Unsupported file format" in run_cli(str(txt)).stdout


@pytest.mark.parametrize("src_fixture", ["json_file", "csv_file"])
def test_export(request, tmp_path, src_fixture):
    src = request.getfixturevalue(src_fixture)
    out = tmp_path / "export.csv"
    r = run_cli(src, "--export", str(out))
    assert r.returncode == 0, r.stdout + r.stderr
    n = len(read_data(src, file_type_for(src)))
    assert f"Exported {n} rows" in r.stdout
    with open(out, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == n and "text" in rows[0] and "label" in rows[0]


def test_export_neutralises_formulas(tmp_path):
    src = tmp_path / "f.csv"
    src.write_text('text,label\n"=1+1",\n"-ok",\nplain,\n', encoding="utf-8")
    out = tmp_path / "out.csv"
    assert run_cli(str(src), "--export", str(out)).returncode == 0
    with open(out, newline="", encoding="utf-8") as f:
        assert [row["text"] for row in csv.DictReader(f)] == ["'=1+1", "'-ok", "plain"]
    assert src.read_text(encoding="utf-8").startswith('text,label\n"=1+1"')


def test_default_allowed_origins():
    assert default_allowed_origins("localhost", 3000, "localhost", 8000) == [
        "http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "http://127.0.0.1:8000"]
    assert default_allowed_origins("annotate.example.org", 3000, "0.0.0.0", 8000) == [
        "http://annotate.example.org:3000", "http://localhost:8000", "http://127.0.0.1:8000"]
