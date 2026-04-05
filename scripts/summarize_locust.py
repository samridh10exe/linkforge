#!/usr/bin/env python3
import csv
import json
import re
import sys
from pathlib import Path


def _as_float(value):
    if value in ("", None):
        return 0.0
    return float(str(value).replace(",", ""))


def _load_aggregated_row(stats_csv):
    with stats_csv.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("Name") == "Aggregated":
                return row
    raise RuntimeError(f"Aggregated row not found in {stats_csv}")


def _parse_mem_to_mib(value):
    match = re.match(r"([0-9.]+)([KMG]iB)", value.strip())
    if not match:
        return 0.0
    number = float(match.group(1))
    unit = match.group(2)
    if unit == "KiB":
        return number / 1024
    if unit == "GiB":
        return number * 1024
    return number


def _load_docker_stats(stats_path):
    peaks = {}
    if not stats_path.exists():
        return peaks

    for line in stats_path.read_text().splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        name = item["Name"]
        cpu = float(item["CPUPerc"].rstrip("%") or 0.0)
        mem_usage = item["MemUsage"].split("/")[0].strip()
        mem_mib = _parse_mem_to_mib(mem_usage)
        current = peaks.setdefault(
            name,
            {"max_cpu_percent": 0.0, "max_mem_mib": 0.0},
        )
        current["max_cpu_percent"] = max(current["max_cpu_percent"], cpu)
        current["max_mem_mib"] = max(current["max_mem_mib"], mem_mib)
    return peaks


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: summarize_locust.py <csv_prefix>")

    prefix = Path(sys.argv[1])
    stats_csv = Path(f"{prefix}_stats.csv")
    stats_log = Path(f"{prefix}_docker_stats.jsonl")
    summary_path = Path(f"{prefix}_summary.json")

    row = _load_aggregated_row(stats_csv)
    requests = int(_as_float(row["Request Count"]))
    failures = int(_as_float(row["Failure Count"]))
    summary = {
        "requests": requests,
        "failures": failures,
        "error_rate_percent": round((failures / requests * 100) if requests else 0.0, 3),
        "requests_per_second": round(_as_float(row["Requests/s"]), 2),
        "p50_ms": round(_as_float(row.get("50%") or row.get("Median Response Time")), 2),
        "p95_ms": round(_as_float(row["95%"]), 2),
        "docker_peaks": _load_docker_stats(stats_log),
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
