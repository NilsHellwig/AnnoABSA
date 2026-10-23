import importlib
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLES = os.path.join(REPO_ROOT, "examples")
FRONTEND_ORIGIN = "http://localhost:3000"

sys.path.insert(0, REPO_ROOT)


@pytest.fixture
def json_file(tmp_path):
    path = tmp_path / "data.json"
    shutil.copy(os.path.join(EXAMPLES, "restaurant_reviews.json"), path)
    return str(path)


@pytest.fixture
def csv_file(tmp_path):
    path = tmp_path / "data.csv"
    shutil.copy(os.path.join(EXAMPLES, "restaurant_reviews.csv"), path)
    return str(path)


@pytest.fixture
def make_client(monkeypatch):
    """Return a factory that builds a TestClient for a fresh backend on `data_file`."""
    from fastapi.testclient import TestClient

    def factory(data_file, allowed_origins=None, config=None):
        monkeypatch.setenv("ABSA_DATA_PATH", data_file)
        monkeypatch.delenv("ABSA_ALLOWED_HOSTS", raising=False)
        if allowed_origins is None:
            monkeypatch.delenv("ABSA_ALLOWED_ORIGINS", raising=False)
        else:
            monkeypatch.setenv("ABSA_ALLOWED_ORIGINS", allowed_origins)
        if config is None:
            monkeypatch.delenv("ABSA_CONFIG_PATH", raising=False)
        else:
            config_path = os.path.join(os.path.dirname(data_file), "config.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f)
            monkeypatch.setenv("ABSA_CONFIG_PATH", config_path)
        import main
        importlib.reload(main)
        return TestClient(main.app, base_url="http://localhost:8000")

    return factory


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def live_server():
    """Start a real uvicorn backend on a data file; yields a function returning its base URL."""
    processes = []

    def start(data_file):
        port = free_port()
        env = dict(os.environ, ABSA_DATA_PATH=data_file)
        for key in ("ABSA_ALLOWED_ORIGINS", "ABSA_ALLOWED_HOSTS", "ABSA_CONFIG_PATH"):
            env.pop(key, None)
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--port", str(port), "--log-level", "warning"],
            cwd=REPO_ROOT, env=env)
        processes.append(proc)
        url = f"http://127.0.0.1:{port}"
        for _ in range(100):
            try:
                urllib.request.urlopen(url + "/version")
                return url
            except OSError:
                time.sleep(0.1)
        raise RuntimeError("backend did not start")

    yield start
    for proc in processes:
        proc.terminate()
        proc.wait()


def run_cli(*args):
    return subprocess.run([sys.executable, os.path.join(REPO_ROOT, "cli.py"), *args],
                          capture_output=True, text=True, cwd=REPO_ROOT)


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)
