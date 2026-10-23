"""Regular API behaviour for JSON and CSV data files."""
import json

import pandas as pd
import pytest

from conftest import read_json
from version import __version__

TUPLE = {"aspect_term": "Pasta", "aspect_category": "food quality",
         "sentiment_polarity": "positive", "opinion_term": "ausgezeichnet", "at_start": 0, "at_end": 4}


@pytest.fixture(params=["json", "csv"])
def data_file(request, json_file, csv_file):
    return json_file if request.param == "json" else csv_file


def stored_labels(path):
    if path.endswith(".json"):
        return [item.get("label") for item in read_json(path)]
    df = pd.read_csv(path)
    return [json.loads(v) if isinstance(v, str) and v else None for v in df["label"]]


def test_version_endpoint(make_client, json_file):
    client = make_client(json_file)
    assert client.get("/version").json() == {"version": __version__}
    assert client.get("/settings").json()["version"] == __version__


def n_items(path):
    return len(read_json(path)) if path.endswith(".json") else len(pd.read_csv(path))


def test_settings_and_data(make_client, data_file):
    client = make_client(data_file)
    settings = client.get("/settings").json()
    assert settings["total_count"] == n_items(data_file)
    item = client.get("/data/0").json()
    expected = read_json(data_file)[0]["text"] if data_file.endswith(".json") else pd.read_csv(data_file)["text"][0]
    assert item["text"] == expected
    assert item["aspect_category_list"]


def test_save_annotations_round_trip(make_client, data_file):
    client = make_client(data_file)
    assert client.post("/annotations/2", json={"name": "a", "value": [TUPLE]}).status_code == 200
    assert stored_labels(data_file)[2] == [TUPLE]
    assert json.loads(client.get("/data/2").json()["label"]) == [TUPLE]


def test_save_empty_list_marks_item_as_done(make_client, json_file):
    client = make_client(json_file)
    data = read_json(json_file)
    for item in data:
        item.pop("label", None)
    with open(json_file, "w") as f:
        json.dump(data, f)
    assert client.get("/settings").json()["current_index"] == 0
    client.post("/annotations/0", json={"name": "a", "value": []})
    assert read_json(json_file)[0]["label"] == []
    assert client.get("/settings").json()["current_index"] == 1


@pytest.mark.parametrize("offset", [-1, 0, 999])
def test_out_of_range_index(make_client, data_file, offset):
    client = make_client(data_file)
    idx = -1 if offset == -1 else n_items(data_file) + offset
    assert client.get(f"/data/{idx}").status_code == 404
    assert client.post(f"/annotations/{idx}", json={"name": "a", "value": []}).status_code == 404
    assert client.post(f"/timing/{idx}", json={"duration": 1}).status_code == 404


@pytest.mark.parametrize("value", [[1], ["text"], [None], [[]]])
def test_annotation_tuples_must_be_objects(make_client, json_file, value):
    client = make_client(json_file)
    before = read_json(json_file)
    assert client.post("/annotations/0", json={"name": "a", "value": value}).status_code == 422
    assert read_json(json_file) == before


@pytest.mark.parametrize("body", [{"name": "a"}, {"value": "notalist", "name": "a"}, {}])
def test_annotation_payload_validation(make_client, json_file, body):
    client = make_client(json_file)
    assert client.post("/annotations/0", json=body).status_code == 422


def test_timing_and_average(make_client, data_file):
    client = make_client(data_file)
    assert client.post("/timing/0", json={"duration": 2.5, "change": True}).status_code == 200
    assert client.post("/timing/0", json={"duration": 0.5, "change": False}).status_code == 200
    assert client.post("/timing/7", json={"duration": 3.0}).status_code == 200
    avg = client.get("/avg-annotation-time").json()
    assert avg == {"avg_annotation_time": 2.0, "total_entries": 3, "total_duration": 6.0}


@pytest.mark.parametrize("duration", ["5", None, True, [1]])
def test_timing_duration_must_be_number(make_client, json_file, duration):
    client = make_client(json_file)
    assert client.post("/timing/0", json={"duration": duration}).status_code == 422


def test_csv_without_label_column(make_client, tmp_path):
    path = tmp_path / "nolabel.csv"
    path.write_text("text\nGreat food\nBad service\n", encoding="utf-8")
    client = make_client(str(path))
    assert client.get("/settings").json()["current_index"] == 0
    assert client.post("/annotations/1", json={"name": "a", "value": [TUPLE]}).status_code == 200
    assert stored_labels(str(path)) == [None, [TUPLE]]


def test_unicode_is_preserved(make_client, data_file):
    client = make_client(data_file)
    t = dict(TUPLE, aspect_term="Atmosphäre 🍝")
    client.post("/annotations/1", json={"name": "a", "value": [t]})
    assert stored_labels(data_file)[1] == [t]


def test_auto_positions(make_client, tmp_path):
    path = tmp_path / "pos.json"
    path.write_text(json.dumps([{"text": "The pasta was excellent.",
                                 "label": [{"aspect_term": "pasta", "opinion_term": "excellent"}]}]))
    client = make_client(str(path), config={"auto_positions": True})
    assert client.post("/auto-add-positions").status_code == 200
    assert read_json(str(path))[0]["label"][0] == {
        "aspect_term": "pasta", "opinion_term": "excellent",
        "at_start": 4, "at_end": 8, "ot_start": 14, "ot_end": 22}
