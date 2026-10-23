"""
Reading, validating and writing AnnoABSA data files.

All writes go through `data_lock` + `write_data`, so concurrent requests (several
annotators on one backend) cannot interleave and the file on disk is always
either the old or the new complete version.
"""
import json
import os
import tempfile
import threading
from contextlib import contextmanager

import pandas as pd

try:
    import fcntl  # POSIX only; used to also serialise writes across processes
except ImportError:  # pragma: no cover - Windows
    fcntl = None


class DataFileError(ValueError):
    """Raised when a data file cannot be read or has an invalid structure."""


def file_type_for(path: str) -> str:
    return "json" if path.endswith('.json') else "csv"


# ---------------------------------------------------------------------------
# Reading & validation
# ---------------------------------------------------------------------------

def read_data(path: str, file_type: str):
    """Load the data file and check its basic structure.

    Raises FileNotFoundError if the file does not exist and DataFileError with a
    human-readable message if it is malformed.
    """
    if file_type == "json":
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise DataFileError(
                f"{path} is not valid JSON (line {e.lineno}, column {e.colno}): {e.msg}") from e
        except UnicodeDecodeError as e:
            raise DataFileError(f"{path} is not UTF-8 encoded: {e}") from e
        if not isinstance(data, list):
            raise DataFileError(
                f"{path} must contain a JSON list of objects, found {type(data).__name__}")
        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                raise DataFileError(
                    f"{path}: entry {idx} must be a JSON object, found {type(item).__name__}")
        return data

    try:
        df = pd.read_csv(path, encoding='utf-8')
    except pd.errors.EmptyDataError as e:
        raise DataFileError(f"{path} is empty") from e
    except pd.errors.ParserError as e:
        raise DataFileError(f"{path} is not a valid CSV file: {e}") from e
    except UnicodeDecodeError as e:
        raise DataFileError(f"{path} is not UTF-8 encoded: {e}") from e
    if 'text' not in df.columns:
        raise DataFileError(
            f"{path} has no 'text' column (found columns: {', '.join(map(str, df.columns))})")
    if 'label' not in df.columns:
        df['label'] = ""
    df['label'] = df['label'].astype(object)
    return df


def validate_data(data, file_type: str, max_problems: int = 10) -> list:
    """Return a list of problems found in already loaded data (empty if valid)."""
    problems = []

    def check_label(idx, label):
        if not isinstance(label, list):
            problems.append(f"entry {idx}: 'label' must be a list, found {type(label).__name__}")
            return
        for t_idx, t in enumerate(label):
            if not isinstance(t, dict):
                problems.append(f"entry {idx}: tuple {t_idx} in 'label' must be an object")

    if file_type == "json":
        for idx, item in enumerate(data):
            if not isinstance(item.get('text'), str):
                problems.append(f"entry {idx}: missing or non-string 'text'")
            if 'label' in item:
                check_label(idx, item['label'])
            if len(problems) >= max_problems:
                break
    else:
        for idx, label in enumerate(data['label']):
            if pd.isna(label) or label == "":
                continue
            try:
                parsed = json.loads(label)
            except (json.JSONDecodeError, TypeError):
                problems.append(f"row {idx + 2}: 'label' is not valid JSON: {str(label)[:60]!r}")
            else:
                check_label(idx, parsed)
            if len(problems) >= max_problems:
                break
    return problems[:max_problems]


def check_data_file(path: str) -> list:
    """Read and fully validate a data file; return a list of problems."""
    try:
        data = read_data(path, file_type_for(path))
    except FileNotFoundError:
        return [f"{path} not found"]
    except DataFileError as e:
        return [str(e)]
    return validate_data(data, file_type_for(path))


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------

_thread_locks = {}
_thread_locks_guard = threading.Lock()


@contextmanager
def data_lock(path: str):
    """Serialise read-modify-write cycles on `path` (threads and, on POSIX, processes)."""
    key = os.path.abspath(path)
    with _thread_locks_guard:
        lock = _thread_locks.setdefault(key, threading.Lock())
    with lock:
        if fcntl is None:
            yield
            return
        with open(key + ".lock", 'a') as lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file, fcntl.LOCK_UN)


def write_data(path: str, file_type: str, data) -> None:
    """Atomically replace `path` with `data` (UTF-8)."""
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp_path = tempfile.mkstemp(
        dir=directory, prefix=f".{os.path.basename(path)}.", suffix=".tmp")
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as f:
            if file_type == "json":
                json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                df = pd.DataFrame(data) if isinstance(data, list) else data
                df.to_csv(f, index=False)
            f.flush()
            os.fsync(f.fileno())
        if os.path.exists(path):
            os.chmod(tmp_path, os.stat(path).st_mode & 0o777)
        os.replace(tmp_path, path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


# ---------------------------------------------------------------------------
# Spreadsheet-safe export
# ---------------------------------------------------------------------------

FORMULA_PREFIXES = ('=', '+', '-', '@', '\t', '\r')


def spreadsheet_safe(value):
    """Prefix values that a spreadsheet program would interpret as a formula."""
    if isinstance(value, str) and value.startswith(FORMULA_PREFIXES):
        return "'" + value
    return value


def export_csv(src_path: str, dst_path: str) -> int:
    """Export a data file to a CSV that is safe to open in spreadsheet programs.

    The working data file is left untouched (changing its text would invalidate
    the stored phrase positions). Returns the number of exported rows.
    """
    if os.path.abspath(src_path) == os.path.abspath(dst_path):
        raise DataFileError("Export path must differ from the data file path")
    file_type = file_type_for(src_path)
    data = read_data(src_path, file_type)
    if file_type == "json":
        rows = [{k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
                 for k, v in item.items()} for item in data]
        df = pd.DataFrame(rows, columns=list(dict.fromkeys(
            ["text", "label"] + [k for item in data for k in item])))
    else:
        df = data
    df = df.map(spreadsheet_safe)
    write_data(dst_path, "csv", df)
    return len(df)
