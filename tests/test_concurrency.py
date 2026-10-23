"""Several annotators writing to one backend and data file at the same time."""
import json
import threading
import urllib.request

import pandas as pd
import pytest

from conftest import FRONTEND_ORIGIN, read_json
from data_io import check_data_file

N_CLIENTS = 12
PER_CLIENT = 20


def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={
        "Content-Type": "application/json", "Origin": FRONTEND_ORIGIN})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status


@pytest.mark.parametrize("fmt", ["json", "csv"])
def test_concurrent_annotators_do_not_corrupt_or_lose_data(live_server, tmp_path, fmt):
    n_items = N_CLIENTS * PER_CLIENT
    path = tmp_path / f"big.{fmt}"
    texts = [f"text number {i} is good" for i in range(n_items)]
    if fmt == "json":
        path.write_text(json.dumps([{"text": t} for t in texts]))
    else:
        pd.DataFrame({"text": texts, "label": [""] * n_items}).to_csv(path, index=False)
    url = live_server(str(path))
    errors = []

    def annotator(k):
        for j in range(PER_CLIENT):
            idx = k * PER_CLIENT + j
            try:
                assert post(f"{url}/annotations/{idx}", {"name": "a", "value": [{"aspect_term": f"t{idx}"}]}) == 200
                assert post(f"{url}/timing/{idx}", {"duration": 1, "change": True}) == 200
            except Exception as e:  # noqa: BLE001 - collected and asserted below
                errors.append(repr(e))

    threads = [threading.Thread(target=annotator, args=(k,)) for k in range(N_CLIENTS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    assert check_data_file(str(path)) == []
    if fmt == "json":
        data = read_json(str(path))
        labels = [d.get("label") for d in data]
        timings = [d.get("timings", []) for d in data]
    else:
        df = pd.read_csv(path)
        labels = [json.loads(v) for v in df["label"]]
        timings = [json.loads(v) for v in df["timings"]]
    assert labels == [[{"aspect_term": f"t{i}"}] for i in range(n_items)]
    assert all(len(t) == 1 for t in timings)
    assert [p.name for p in tmp_path.iterdir() if p.name.endswith(".tmp")] == []


def test_concurrent_writes_to_same_item_all_succeed(live_server, json_file):
    url = live_server(json_file)
    errors = []

    def timing():
        try:
            for _ in range(10):
                post(f"{url}/timing/0", {"duration": 1, "change": False})
        except Exception as e:  # noqa: BLE001
            errors.append(repr(e))

    threads = [threading.Thread(target=timing) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    assert len(read_json(json_file)[0]["timings"]) == 80
