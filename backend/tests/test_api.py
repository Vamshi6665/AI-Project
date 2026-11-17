"""API tests in mock mode (no network). Run from backend/:  pytest -q"""
import json
import os
from pathlib import Path

import pytest

os.environ["LLM_PROVIDER"] = "mock"
os.environ["JWT_SECRET"] = "test-secret-that-is-at-least-32-bytes-long"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.services.extractor import parse_model_json  # noqa: E402

SAMPLES = Path(__file__).resolve().parents[2] / "samples"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        c.app.state.llm.latency_seconds = 0
        yield c


@pytest.fixture(scope="module")
def token(client):
    r = client.post("/api/auth/login", json={"username": "demo", "password": "demo123"})
    assert r.status_code == 200
    return r.json()["data"]["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True and body["data"]["provider"] == "mock"
    assert r.headers["X-Request-ID"] == body["request_id"]


def test_login_wrong_password(client):
    r = client.post("/api/auth/login", json={"username": "demo", "password": "nope"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHORIZED"


def test_extract_requires_token(client):
    r = client.post("/api/extract", files={"file": ("a.pdf", b"%PDF-1.4", "application/pdf")})
    assert r.status_code == 401


def test_extract_rejects_bad_token(client):
    r = client.post("/api/extract", headers={"Authorization": "Bearer abc.def.ghi"},
                    files={"file": ("a.pdf", b"%PDF-1.4", "application/pdf")})
    assert r.status_code == 401 and r.json()["error"]["message"] == "Invalid token"


def test_extract_rejects_non_pdf(client, token):
    r = client.post("/api/extract", headers=auth(token), files={"file": ("notes.txt", b"hello", "text/plain")})
    assert r.status_code == 415 and r.json()["error"]["code"] == "INVALID_FILE"


def test_extract_rejects_fake_pdf(client, token):
    r = client.post("/api/extract", headers=auth(token),
                    files={"file": ("fake.pdf", b"not really a pdf", "application/pdf")})
    assert r.status_code == 415


def test_extract_discharge_summary(client, token):
    pdf = (SAMPLES / "01_discharge_summary.pdf").read_bytes()
    r = client.post("/api/extract", headers=auth(token),
                    files={"file": ("01_discharge_summary.pdf", pdf, "application/pdf")})
    assert r.status_code == 200, r.text
    rec = r.json()["data"]
    assert rec["data"]["patient"]["name"] == "Maria Delgado"
    assert rec["data"]["patient"]["mrn"] == "RGH-0048213"
    assert len(rec["data"]["medications"]) == 4
    assert {lab["flag"] for lab in rec["data"]["lab_results"]} >= {"high", "low", "normal"}
    assert len(rec["data"]["social_history"]) == 3
    assert any("smoker" in s for s in rec["data"]["social_history"])
    assert rec["document"]["pages"] >= 1 and rec["inference"]["attempts"] == 1

    # It shows up in history and can be fetched by id.
    hist = client.get("/api/extractions", headers=auth(token)).json()["data"]
    assert hist[0]["id"] == rec["id"]
    one = client.get(f"/api/extractions/{rec['id']}", headers=auth(token))
    assert one.status_code == 200


def test_unknown_extraction_404(client, token):
    r = client.get("/api/extractions/doesnotexist", headers=auth(token))
    assert r.status_code == 404 and r.json()["error"]["code"] == "NOT_FOUND"


def test_parse_model_json_handles_fences_and_chatter():
    raw = 'Sure! Here it is:\n```json\n{"patient": {"name": "A"}, "diagnoses": []}\n```'
    assert parse_model_json(raw).patient.name == "A"


def test_parse_model_json_rejects_wrong_types():
    with pytest.raises(ValueError):
        parse_model_json(json.dumps({"diagnoses": "not a list"}))


class _FlakyLLM:
    """First answer is invalid, second is valid -> the repair retry must kick in."""
    provider, model = "fake", "fake"

    def __init__(self):
        self.calls = 0

    async def complete(self, messages):
        from app.services.llm.base import LLMResult
        self.calls += 1
        return LLMResult(text="oops not json" if self.calls == 1 else '{"patient": {"name": "B"}}')


def test_repair_retry(client, token):
    original = client.app.state.llm
    client.app.state.llm = _FlakyLLM()
    try:
        pdf = (SAMPLES / "02_lab_report.pdf").read_bytes()
        r = client.post("/api/extract", headers=auth(token),
                        files={"file": ("02_lab_report.pdf", pdf, "application/pdf")})
        assert r.status_code == 200
        assert r.json()["data"]["inference"]["attempts"] == 2
    finally:
        client.app.state.llm = original
