from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from app import logging_config
from app.main import app


def test_request_id_is_preserved_or_generated_without_context_leak(
    monkeypatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "requests.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    with TestClient(app) as client:
        first = client.post(
            "/chat",
            headers={"x-request-id": "req-1a2b3c4d"},
            json={
                "user_id": "first-user",
                "session_id": "first-session",
                "feature": "qa",
                "message": "Explain traces",
            },
        )
        second = client.post(
            "/chat",
            headers={"x-request-id": "invalid"},
            json={
                "user_id": "second-user",
                "session_id": "second-session",
                "feature": "summary",
                "message": "Summarize monitoring",
            },
        )

    assert first.status_code == second.status_code == 200
    assert first.headers["x-request-id"] == "req-1a2b3c4d"
    assert re.fullmatch(r"req-[0-9a-f]{8}", second.headers["x-request-id"])
    assert float(first.headers["x-response-time-ms"]) >= 0
    assert float(second.headers["x-response-time-ms"]) >= 0

    records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    api_records = [record for record in records if record.get("service") == "api"]
    first_records = [record for record in api_records if record["session_id"] == "first-session"]
    second_records = [record for record in api_records if record["session_id"] == "second-session"]
    assert {record["correlation_id"] for record in first_records} == {"req-1a2b3c4d"}
    assert {record["correlation_id"] for record in second_records} == {second.headers["x-request-id"]}
    assert all(record["feature"] == "qa" for record in first_records)
    assert all(record["feature"] == "summary" for record in second_records)
