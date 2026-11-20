#!/usr/bin/env python3
"""Bind the recorded browser run to every local HTTP input, including ranged tile responses."""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

AUDIT = Path(__file__).resolve().parent
DEFAULT_PROJECT = AUDIT.parents[2]
REPORT_NAME = "main-map-inputs.json"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git_blob(data):
    header = f"blob {len(data)}".encode() + b"\0"
    return hashlib.sha1(header + data).hexdigest()


def git_entry(project, name, rev):
    rel = "projects/shanghai/" + name
    return subprocess.check_output(["git", "-C", str(project), "rev-parse", rev + ":" + rel],
                                   text=True).strip()


def capture(args):
    report = json.loads(args.browser_report.read_text())
    assert report["completed"]
    start = datetime.fromisoformat(report["started_utc"].replace("Z", "+00:00")).timestamp()
    end = datetime.fromisoformat(report["finished_utc"].replace("Z", "+00:00")).timestamp()
    records = {}
    rows = [json.loads(line) for line in args.server_log.read_text().splitlines()]
    for row in rows:
        if not start <= row["at"] <= end:
            continue
        name = row["path"]
        assert row["status"] in (200, 206)
        in_cache = row["origin"].startswith("git-blob-verified-")
        source = (args.server_log.parent / "objects" if in_cache else args.project) / name
        data = source.read_bytes()
        assert digest(data) == row["sha256"] and len(data) == row["bytes"], name
        blob = git_blob(data)
        if in_cache:
            receipt = json.loads(source.with_name(source.name + ".receipt.json").read_text())
            assert receipt["actual_git_blob"] == receipt["git_blob"] == blob, name
        entry = {"bytes": len(data), "sha256": digest(data), "git_blob": blob}
        assert records.get(name, entry) == entry, name
        records[name] = entry
    for name, expected in report["bindings"].items():
        data = (args.project / name).read_bytes()
        assert digest(data) == expected, name
        entry = {"bytes": len(data), "sha256": expected, "git_blob": git_blob(data)}
        assert records.get(name, entry) == entry, name
        records[name] = entry
    assert {"index.html", "landmarks.html", "data/candidate-city-integrations.json"} <= records.keys()
    for item in report["http_assets"] + report["map_files_seen"]:
        assert records[item["file"]]["sha256"] == item["sha256"], item["file"]
    generation_files = ["data/global-models/additional-placement.json", "data/global-models/candidate-inventory.json",
                        "data/audit/global-model-integration-v1/inventory.json",
                        "data/audit/concert-hall-v1/inventory-increment.json"]
    generation = {}
    for name in generation_files:
        data = (args.project / name).read_bytes()
        generation[name] = {"bytes": len(data), "sha256": digest(data), "git_blob": git_blob(data)}
    output = {"run_sha256": digest(args.browser_report.read_bytes()),
              "catalog_generation_inputs": generation,
              "scope": "All successful GET and range responses from the dedicated same-origin audit server during the recorded run, plus local browser-script bindings. Ranged responses identify the complete resource.",
              "files": dict(sorted(records.items()))}
    args.inventory.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(f"Recorded {len(records)} distinct model, map, directory and runtime resources.")


def verify(args):
    inventory = json.loads(args.inventory.read_text())
    assert inventory["run_sha256"] == digest(args.browser_report.read_bytes())
    for name, rec in (inventory["files"] | inventory["catalog_generation_inputs"]).items():
        file = args.project / name
        if args.revision or not file.is_file():
            assert git_entry(args.project, name, args.revision or "HEAD") == rec["git_blob"], name
        else:
            data = file.read_bytes()
            assert len(data) == rec["bytes"] and digest(data) == rec["sha256"], name
    rev = args.revision or "working tree (absent sparse files verified against HEAD)"
    if args.receipt:
        receipt = {"verified_utc": datetime.now(timezone.utc).isoformat(), "target": rev,
                   "git_base_commit": subprocess.check_output(["git", "-C", str(args.project), "rev-parse",
                                                               args.revision or "HEAD"], text=True).strip(),
                   "browser_report_sha256": inventory["run_sha256"],
                   "input_inventory_sha256": digest(args.inventory.read_bytes()),
                   "verifier_sha256": digest(Path(__file__).read_bytes()),
                   "verified_resources": len(inventory["files"]),
                   "verified_catalog_generation_records": len(inventory["catalog_generation_inputs"]),
                   "passed": True}
        args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"All {len(inventory['files'])} HTTP inputs and {len(inventory['catalog_generation_inputs'])} catalog-generation records match {rev}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["capture", "verify"])
    parser.add_argument("--project", type=Path, default=DEFAULT_PROJECT)
    parser.add_argument("--browser-report", type=Path, default=AUDIT / "main-map-browser.json")
    parser.add_argument("--inventory", type=Path, default=AUDIT / REPORT_NAME)
    parser.add_argument("--server-log", type=Path)
    parser.add_argument("--receipt", type=Path, help="Write the verification receipt after every match.")
    parser.add_argument("--revision", help="Verify every input against this exact Git revision.")
    args = parser.parse_args()
    if args.action == "capture" and args.server_log is None:
        parser.error("--server-log is required for capture")
    (capture if args.action == "capture" else verify)(args)
