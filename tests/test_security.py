"""Cross-origin protection and security headers."""
import json

import pytest

from conftest import FRONTEND_ORIGIN, read_json

TUPLE = {"aspect_term": "pasta", "aspect_category": "food quality",
         "sentiment_polarity": "positive", "opinion_term": "excellent"}
BODY = {"name": "annotations", "value": [TUPLE]}
WRITE_REQUESTS = [
    ("/annotations/0", BODY),
    ("/timing/0", {"duration": 1.0, "change": True}),
    ("/auto-add-positions", None),
]


@pytest.fixture
def client(make_client, json_file):
    return make_client(json_file)


@pytest.mark.parametrize("path,body", WRITE_REQUESTS)
@pytest.mark.parametrize("origin", ["https://evil.example", "http://localhost:3001", "null"])
def test_writes_from_foreign_origins_are_rejected(client, json_file, path, body, origin):
    before = read_json(json_file)
    r = client.post(path, json=body, headers={"Origin": origin})
    assert r.status_code == 403
    assert read_json(json_file) == before


def test_simple_text_plain_post_is_rejected(client, json_file):
    # A "simple" request: browsers send it cross-origin without a CORS preflight
    before = read_json(json_file)
    r = client.post("/annotations/0", content=json.dumps(BODY),
                    headers={"Origin": "https://evil.example", "Content-Type": "text/plain"})
    assert r.status_code == 403
    assert read_json(json_file) == before


def test_cross_site_request_without_origin_is_rejected(client):
    assert client.post("/annotations/0", json=BODY, headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403
    assert client.get("/data/0", headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403


def test_reads_from_foreign_origin_are_rejected(client):
    assert client.get("/data/0", headers={"Origin": "https://evil.example"}).status_code == 403


@pytest.mark.parametrize("host", ["rebind.evil.example:8000", "evil.example"])
def test_unknown_host_header_is_rejected(client, host):
    # DNS rebinding: attacker's domain resolves to 127.0.0.1, request is "same-origin" for the browser
    assert client.get("/data/0", headers={"Host": host}).status_code == 403


@pytest.mark.parametrize("host", ["localhost:8000", "127.0.0.1:8000", "[::1]:8000", "192.168.0.10:8000"])
def test_local_and_ip_hosts_are_allowed(client, host):
    assert client.get("/data/0", headers={"Host": host}).status_code == 200


def test_frontend_origin_can_write(client, json_file):
    r = client.post("/annotations/0", json=BODY, headers={"Origin": FRONTEND_ORIGIN})
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == FRONTEND_ORIGIN
    assert read_json(json_file)[0]["label"] == [TUPLE]


def test_non_browser_clients_can_write(client, json_file):
    # Scripts/curl send no Origin and no Sec-Fetch-* headers
    assert client.post("/annotations/0", json=BODY).status_code == 200
    assert client.post("/annotations/1", json=BODY, headers={"Sec-Fetch-Site": "same-origin"}).status_code == 200


def test_preflight_is_only_granted_to_frontend(client):
    headers = {"Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"}
    r = client.options("/annotations/0", headers={**headers, "Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in r.headers
    r = client.options("/annotations/0", headers={**headers, "Origin": FRONTEND_ORIGIN})
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == FRONTEND_ORIGIN
    assert r.headers.get("access-control-allow-credentials") is None


def test_custom_allowed_origins(make_client, json_file):
    client = make_client(json_file, allowed_origins="http://annotate.example.org:3000/")
    origin = "http://annotate.example.org:3000"
    assert client.post("/annotations/0", json=BODY, headers={"Origin": origin}).status_code == 200
    assert client.post("/annotations/0", json=BODY, headers={"Origin": FRONTEND_ORIGIN}).status_code == 403
    assert client.get("/version", headers={"Host": "annotate.example.org:8000"}).status_code == 200


def test_wildcard_origin_is_explicit_opt_in(make_client, json_file):
    client = make_client(json_file, allowed_origins="*")
    assert client.post("/annotations/0", json=BODY, headers={"Origin": "https://evil.example"}).status_code == 200


@pytest.mark.parametrize("path", ["/settings", "/data/0", "/version", "/data/999"])
def test_security_headers(client, path):
    r = client.get(path)
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]
    assert r.headers["referrer-policy"] == "no-referrer"


def test_security_headers_on_rejected_requests(client):
    r = client.post("/annotations/0", json=BODY, headers={"Origin": "https://evil.example"})
    assert r.headers["x-frame-options"] == "DENY"
    assert r.headers["x-content-type-options"] == "nosniff"


def test_legacy_write_endpoint_removed(client):
    assert client.post("/data/0", json={"name": "x", "value": 1}).status_code == 405
