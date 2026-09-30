from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from statistics import mean
from typing import Any

LOG_PATH = Path("data/logs.jsonl")
WINDOW_MINUTES = 60
THRESHOLDS = {
    "latency_p95_ms": 3000,
    "traffic_rpm": 1,
    "error_rate_pct": 2,
    "cost_usd": 2.5,
    "tokens": 50000,
    "quality": 0.75,
    "retrieval_success_pct": 90,
}


def _percentile(values: list[float], percentile: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, math.ceil(percentile / 100 * len(ordered)) - 1)
    return ordered[index]


def load_window(path: Path = LOG_PATH, now: datetime | None = None) -> list[dict[str, Any]]:
    now = now or datetime.now(timezone.utc)
    start = now - timedelta(minutes=WINDOW_MINUTES)
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
            timestamp = datetime.fromisoformat(record["ts"].replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            continue
        if start <= timestamp <= now:
            records.append(record)
    return records


def _sparkline(values: list[float], *, color: str = "#4e7cf6") -> str:
    width, height, padding = 320, 48, 3
    if not values:
        values = [0]
    maximum = max(values) or 1
    points = []
    for index, value in enumerate(values):
        x = padding + index * (width - 2 * padding) / max(1, len(values) - 1)
        y = height - padding - (value / maximum) * (height - 2 * padding)
        points.append(f"{x:.1f},{y:.1f}")
    return (
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Trend chart">'
        f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" '
        'stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    )


def _panel(title: str, value: str, unit: str, threshold: str, chart: str, note: str = "") -> str:
    return (
        '<section class="panel"><h2>' + escape(title) + '</h2>'
        '<div class="metric">' + escape(value) + '<span>' + escape(unit) + '</span></div>'
        '<div class="threshold">Ngưỡng: ' + escape(threshold) + '</div>'
        + chart
        + ('<p class="note">' + escape(note) + '</p>' if note else "")
        + "</section>"
    )


def render_dashboard(records: list[dict[str, Any]]) -> str:
    responses = [row for row in records if row.get("event") == "response_sent"]
    requests = [row for row in records if row.get("event") == "request_received"]
    failures = [row for row in records if row.get("event") == "request_failed"]
    latencies = [float(row["latency_ms"]) for row in responses if row.get("latency_ms") is not None]
    ttfts = [float(row["ttft_ms"]) for row in responses if row.get("ttft_ms") is not None]
    costs = [float(row["cost_usd"]) for row in responses if row.get("cost_usd") is not None]
    tokens_in = sum(int(row.get("tokens_in") or 0) for row in responses)
    tokens_out = sum(int(row.get("tokens_out") or 0) for row in responses)
    qualities = [float(row["quality_score"]) for row in responses if row.get("quality_score") is not None]
    tool_events = [row for row in records if row.get("tool_success") is not None]
    tool_successes = sum(row.get("tool_success") is True for row in tool_events)
    error_rate = 100 * len(failures) / max(1, len(requests))
    retrieval_rate = 100 * tool_successes / max(1, len(tool_events))

    minute_counts: Counter[str] = Counter()
    for row in requests:
        try:
            stamp = datetime.fromisoformat(row["ts"].replace("Z", "+00:00"))
            minute_counts[stamp.strftime("%H:%M")] += 1
        except (KeyError, TypeError, ValueError):
            continue
    current_minute = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    window_minutes = [current_minute - timedelta(minutes=offset) for offset in reversed(range(WINDOW_MINUTES))]
    traffic_buckets = [minute_counts[stamp.strftime("%H:%M")] for stamp in window_minutes]
    traffic_rpm = len(requests) / WINDOW_MINUTES
    cost_by_minute: Counter[str] = Counter()
    for row in responses:
        try:
            stamp = datetime.fromisoformat(row["ts"].replace("Z", "+00:00"))
            cost_by_minute[stamp.strftime("%H:%M")] += float(row.get("cost_usd") or 0)
        except (KeyError, TypeError, ValueError):
            continue

    panels = [
        _panel(
            "Latency · P50 / P95 / P99 · TTFT P95",
            f"{_percentile(latencies, 50):.0f} / {_percentile(latencies, 95):.0f} / {_percentile(latencies, 99):.0f} · {_percentile(ttfts, 95):.0f}",
            "ms",
            f"P95 ≤ {THRESHOLDS['latency_p95_ms']} ms",
            _sparkline(latencies[-30:], color="#e09c39"),
            f"{len(latencies)} phản hồi",
        ),
        _panel(
            "Traffic",
            f"{traffic_rpm:.1f}",
            "request/phút (trung bình)",
            f"≥ {THRESHOLDS['traffic_rpm']} request/phút",
            _sparkline(traffic_buckets),
            f"{len(requests)} request trong cửa sổ",
        ),
        _panel(
            "Errors · Retrieval success",
            f"{error_rate:.1f}% · {retrieval_rate:.1f}%",
            "error rate · retrieval thành công",
            f"error ≤ {THRESHOLDS['error_rate_pct']}% · retrieval ≥ {THRESHOLDS['retrieval_success_pct']}%",
            _sparkline([error_rate, retrieval_rate], color="#c85252"),
            f"{len(failures)} lỗi · {tool_successes}/{len(tool_events)} tool events thành công",
        ),
        _panel(
            "Cost",
            f"${sum(costs):.4f}",
            "USD / 60 phút",
            f"≤ ${THRESHOLDS['cost_usd']:.2f}",
            _sparkline([cost_by_minute[stamp.strftime("%H:%M")] for stamp in window_minutes], color="#55a77b"),
            f"{len(costs)} generation",
        ),
        _panel(
            "Tokens",
            f"{tokens_in:,} / {tokens_out:,}",
            "input / output tokens",
            f"tổng ≤ {THRESHOLDS['tokens']:,} tokens",
            _sparkline([tokens_in, tokens_out], color="#8b68bd"),
            f"{len(responses)} response_sent",
        ),
        _panel(
            "Quality proxy",
            f"{mean(qualities) if qualities else 0:.2f}",
            "điểm (0–1)",
            f"≥ {THRESHOLDS['quality']:.2f}",
            _sparkline(qualities[-30:], color="#2e9ea0"),
            f"{len(qualities)} câu trả lời được chấm heuristic",
        ),
    ]
    return """<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta http-equiv="refresh" content="30">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Day 13 Monitoring</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f4f6fa;color:#1d2635;font:15px system-ui,-apple-system,sans-serif}
main{max-width:1200px;margin:auto;padding:32px 24px}header{display:flex;justify-content:space-between;align-items:end;margin-bottom:22px}
h1{margin:0;font-size:25px}header p{margin:7px 0 0;color:#637087}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.panel{background:white;border:1px solid #e2e7ef;border-radius:12px;padding:20px;box-shadow:0 2px 8px #1b2b4510;min-height:190px}
h2{font-size:16px;margin:0 0 17px}.metric{font-size:27px;font-weight:700;line-height:1.3;overflow-wrap:anywhere}.metric span{display:block;font-size:12px;font-weight:500;color:#68758a;margin-top:3px}
.threshold{font-size:12px;color:#637087;margin-top:8px}svg{width:100%;height:48px;margin-top:14px}.note{font-size:12px;color:#637087;margin:5px 0 0}
@media(max-width:700px){.grid{grid-template-columns:1fr}header{display:block}}
</style></head><body><main><header><div><h1>K4-L3B · Monitoring &amp; LLMOps</h1>
<p>Nguồn: data/logs.jsonl · Cửa sổ 60 phút · Tự cập nhật mỗi 30 giây</p></div>
<p>Đơn vị thời gian: UTC</p></header><div class="grid">""" + "".join(panels) + "</div></main></body></html>"


def dashboard_html(path: Path = LOG_PATH) -> str:
    return render_dashboard(load_window(path))
