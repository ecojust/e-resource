"""Check this delivery's incremental records without redecoding historical assets."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

BASELINE = "c59174528765c104f09295ef10132b4bb4f63ce5"
MODEL = "hongkou-general-post-office"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[5])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo.resolve()
    project = root / "projects/shanghai"

    def git(*parts):
        return subprocess.check_output(["git", *parts], cwd=root)

    def old(path):
        return json.loads(git("show", BASELINE + ":projects/shanghai/" + path))

    def current(path):
        return json.loads((project / path).read_text())

    checks = []
    for path, key, expected in [
        ("data/candidate-city-integrations.json", "models", 44),
        ("data/global-models/candidate-inventory.json", "records", 46),
    ]:
        before = {row["id"]: row for row in old(path)[key]}
        rows = current(path)[key]
        after = {row["id"]: row for row in rows}
        assert len(rows) == len(after) == expected, path
        assert set(after) - set(before) == {MODEL}, path
        assert all(after.get(key) == value for key, value in before.items()), path
        checks.append({"file": path, "preserved_records": len(before),
                       "resulting_records": len(after), "new_id": MODEL,
                       "sha256": hashlib.sha256((project / path).read_bytes()).hexdigest()})

    before_queue = old("data/model-todo/queue.json")
    after_queue = current("data/model-todo/queue.json")
    before = before_queue["production_queue"]
    after = after_queue["production_queue"]
    assert after[:37] == before[:37], "Prior completed tasks changed"
    assert after_queue["existing_models"] == before_queue["existing_models"], "Prior inventory tasks changed"
    assert len(after) == 39 and after[37]["order"] == 38
    assert after[37]["id"] == MODEL and after[37]["status"] == "candidate_delivered"
    assert after[38]["order"] == 39 and after[38]["status"] == "identity_review"
    assert len({row["id"] for row in after}) == len(after)

    protected = ["projects/shanghai/assets/", "projects/shanghai/source/precise/",
                 "projects/shanghai/data/audit/"]
    allowed = [f"projects/shanghai/assets/models/candidates/{MODEL}/",
               f"projects/shanghai/source/precise/{MODEL}/",
               "projects/shanghai/data/audit/postal-office-v1/"]
    changes = git("diff", "--no-renames", "--name-status", BASELINE).decode().splitlines()
    for line in changes:
        status, path = line.split("\t", 1)
        assert status != "D", f"Tracked deletion: {path}"
        if any(path.startswith(prefix) for prefix in protected):
            assert any(path.startswith(prefix) for prefix in allowed), path
    for path in ["data/landmarks.json", "data/model-todo/discovered-buildings.json",
                 "data/model-todo/discovered-streets.json", "data/model-todo/named-map-leads.json"]:
        assert (project / path).read_bytes() == git("show", BASELINE + ":projects/shanghai/" + path), path

    report = {"schema": "postal-increment-preservation-v1", "model_id": MODEL,
              "baseline_commit": BASELINE,
              "checked_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "passed": True, "checks": checks, "prior_completed_queue_records_unchanged": 37,
              "prior_inventory_queue_records_unchanged": len(before_queue["existing_models"]),
              "resulting_queue_length": len(after), "next_model_id": after[38]["id"],
              "tracked_deletions": 0, "historical_asset_changes": 0,
              "scope": "Exact old registry/task/source-index comparison and tracked path changes; historical assets were not redecoded."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"passed": True, "preserved_catalog_records": 43,
                      "preserved_manifest_records": 45, "output": str(args.output)}))


if __name__ == "__main__":
    main()
