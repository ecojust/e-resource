"""Verify this postal-office delivery's registrations and generated metadata.

This bounded check reuses the separately verified asset inventory. It does not
decode historical models or claim native-file, GPU or browser acceptance.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import parse_qs, urlsplit


ID = "hongkou-general-post-office"
BASELINE = "c59174528765c104f09295ef10132b4bb4f63ce5"
PROJECT_PATH = "projects/shanghai/"
CACHE_TOKEN = "postal-office-v1"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[5])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    project = repo / PROJECT_PATH
    output = args.output or project / "data/audit/postal-office-v1/metadata-checks.json"

    def load(path):
        return json.loads((repo / path).read_text())

    def old(path):
        return json.loads(subprocess.check_output(["git", "show", f"{BASELINE}:{path}"], cwd=repo))

    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    tools = [
        ["build_candidate_city_integrations.py", "--catalog-only", "--check"],
        ["update_global_model_metadata.py", "--check"],
        ["build_model_todo.py", "--check"],
        ["build_landmark_directory.py", "--check"],
        ["restoration_progress.py", "--check"],
        ["sync_readme_districts.py", "--check"],
    ]
    commands = [["python", "-B", PROJECT_PATH + "tools/" + row[0], *row[1:]] for row in tools]
    commands += [
        ["node", "--test", PROJECT_PATH + "tests/landmark-navigation.test.mjs", PROJECT_PATH + "tests/landmark-directory.test.mjs"],
        ["node", "--test", PROJECT_PATH + "tests/building-beacons.test.mjs", PROJECT_PATH + "tests/candidate-overview-camera.test.mjs"],
        ["git", "diff", "--check"],
    ]
    checks = []
    for command in commands:
        result = subprocess.run(command, cwd=repo, text=True, capture_output=True)
        checks.append({"command": command, "exit_code": result.returncode,
                       "stdout": result.stdout, "stderr": result.stderr,
                       "passed": result.returncode == 0})

    assertions = []

    def require(label, condition):
        assertions.append({"check": label, "passed": bool(condition)})

    catalog_path = PROJECT_PATH + "data/candidate-city-integrations.json"
    catalog = load(catalog_path)
    old_catalog = old(catalog_path)
    rows = catalog["models"]
    by_id = {row["id"]: row for row in rows}
    old_by_id = {row["id"]: row for row in old_catalog["models"]}
    require("Exactly one new candidate ID", set(by_id) - set(old_by_id) == {ID})
    require("All prior 43 candidate records unchanged", all(by_id.get(k) == v for k, v in old_by_id.items()))
    require("Candidate counts are 44 and total destinations 84", len(rows) == len(by_id) == 44 and catalog["resulting_city_count"] == 84)
    base_path = PROJECT_PATH + "data/landmarks.json"
    base = load(base_path)
    require("All 40 legacy landmarks unchanged", base == old(base_path) and len(base) == 40)
    district_counts = Counter(str(row["districtId"]) for row in base + rows)
    require("Hongkou has five destinations", district_counts["310109"] == 5)
    model = by_id.get(ID, {})
    require("Postal ID links to its own auxiliary page", model.get("individual_page") == "postal-office.html")
    require("Postal exterior remains overview-only", model.get("navigation", {}).get("listed") is False)

    queue_path = PROJECT_PATH + "data/model-todo/queue.json"
    queue = load(queue_path)
    old_queue = old(queue_path)
    jobs = {job["id"]: job for job in queue["production_queue"]}
    preceding = [job for job in old_queue["production_queue"] if job["order"] < 38]
    require("Preceding 37 task records unchanged", all(jobs.get(job["id"]) == job for job in preceding) and len(preceding) == 37)
    require("Original 46 inventory task records unchanged", queue["existing_models"] == old_queue["existing_models"] and len(queue["existing_models"]) == 46)
    require("Postal queue item delivered with evidence", jobs.get(ID, {}).get("status") in ("candidate_delivered", "accepted") and bool(jobs.get(ID, {}).get("manifest")) and bool(jobs.get(ID, {}).get("evidence")))

    inventory_path = PROJECT_PATH + "data/global-models/candidate-inventory.json"
    inventory = load(inventory_path)
    old_inventory = old(inventory_path)
    inventory_by_id = {row["id"]: row for row in inventory["records"]}
    require("Previous 45 manifest records preserved", all(inventory_by_id.get(row["id"]) == row for row in old_inventory["records"]) and len(old_inventory["records"]) == 45)
    require("Inventory has 46 manifests and 184 assets", len(inventory["records"]) == 46 and inventory["verification"]["files"] == 184)

    placement_path = PROJECT_PATH + "data/global-models/additional-placement.json"
    placements, old_placements = load(placement_path), old(placement_path)
    placement_by_id = {row["id"]: row for row in placements["records"]}
    require("Previous additional placements preserved", all(placement_by_id.get(row["id"]) == row for row in old_placements["records"]))
    require("Previous footprint-report bindings preserved", placements["source_contracts"][:-1] == old_placements["source_contracts"])
    footprint_relative = "data/audit/postal-office-v1/footprint-review.json"
    footprint_path = project / footprint_relative
    footprint = json.loads(footprint_path.read_text())
    require("Postal placement equals final mapping contract", placement_by_id.get(ID) == footprint["proposed_placement_contract"])
    require("Final mapping report binding matches bytes", placements["source_contracts"][-1] == {
        "file": footprint_relative, "bytes": footprint_path.stat().st_size,
        "sha256": digest(footprint_path), "record": "proposed_placement_contract"})

    all_ids = {row["id"] for row in base + rows}
    for path in [repo / "README.md", project / "README.md"]:
        text = path.read_text()
        directory = text.split("## 按区查看主要建筑\n", 1)[1]
        directory = re.split(r"\n## (?!#)", directory, maxsplit=1)[0]
        urls = re.findall(r"\[查看网页\]\(([^)]+)\)", directory)
        linked_ids = []
        for url in urls:
            parsed = urlsplit(url)
            params = parse_qs(parsed.fragment)
            require(f"Main-map route in {path.relative_to(repo)}: {params.get('landmark', ['?'])[0]}", parsed.path == "/ecojust/e-resource/master/projects/shanghai/index.html" and params.get("mode", [None])[0] in ("overview", "walk"))
            linked_ids.extend(params.get("landmark", []))
        require(f"All 84 destination IDs appear once in {path.relative_to(repo)}", len(linked_ids) == len(set(linked_ids)) == 84 and set(linked_ids) == all_ids)
        require(f"Hongkou heading in {path.relative_to(repo)}", "### 虹口区（5处）" in directory)

    for path in ["index.html", "src/app.js", "src/map-scene.js"]:
        text = (project / path).read_text()
        require(f"Current cache token in {path}", CACHE_TOKEN in text and "great-world-v1" not in text)
    require("Index loads this release app", f'src/app.js?v={CACHE_TOKEN}' in (project / "index.html").read_text())
    require("Auxiliary page identifies postal model", ID in (project / "postal-office.html").read_text() and "window.postalOfficeViewer" in (project / "src/postal-office.js").read_text())

    files = ["README.md"] + [PROJECT_PATH + p for p in [
        "README.md", "CURRENT_STATE.md", "index.html", "landmarks.html", "postal-office.html",
        "src/app.js", "src/map-scene.js", "src/candidate-city-integrations.js", "src/postal-office.js",
        "data/candidate-city-integrations.json", "data/global-models/additional-placement.json",
        "data/global-models/candidate-inventory.json", "data/model-viewers.json", "data/model-todo/queue.json",
        "data/model-todo/completed-model-scope-review.json", f"assets/models/candidates/{ID}/manifest.json",
    ]]
    report = {"model_id": ID, "baseline_commit": BASELINE,
              "verification_script_sha256": digest(Path(__file__).resolve()),
              "checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "checks": checks, "assertions": assertions,
              "counts": {"legacy_destinations": len(base), "new_city_candidates": len(rows),
                         "all_destinations": len(base) + len(rows), "hongkou": district_counts["310109"],
                         "candidate_manifests": len(inventory["records"]), "cumulative_asset_files": inventory["verification"]["files"]},
              "bindings": [{"file": p, "bytes": (repo / p).stat().st_size, "sha256": digest(repo / p)} for p in files],
              "scope": "Generated metadata, route registrations, prior structured-record preservation and existing navigation/beacon tests. Historical GLBs not redecoded; native, GPU, browser and public HTTP checks are separate.",
              "passed": all(item["passed"] for item in checks + assertions)}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "commands": len(checks), "assertions": len(assertions),
                      "counts": report["counts"], "failed": [item.get("check", item.get("command")) for item in checks + assertions if not item["passed"]]}, ensure_ascii=False))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
