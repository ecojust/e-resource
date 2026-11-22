"""Bind each inspected screenshot, browser process and saved download before the next city's handoff."""
import argparse
import hashlib
import json
import os
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("order", type=int, choices=[199, 243])
parser.add_argument("--review", type=Path)
args = parser.parse_args()
order = args.order
work = Path(__file__).parent
stage = 31000 + order
audit_name = {199: "wukang-east-annex-v1", 243: "yanan-road-telegraph-exchange-v1"}[order]
city = Path("/workspace/e-resource/projects/shanghai/data/audit") / audit_name / f"city-{stage}"
actual = work / "evidence" / str(order)
viewer = work / f"viewer-{stage}"
phases = ["before", "phone", "desktop", "details", "touch", "architecture"]
if order == 243:
    phases.append("closeups")
phases.append("distant")

def load(path):
    return json.loads(path.read_bytes())

def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

def stable_write(path, data):
    binary = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode()
    if path.exists():
        assert path.read_bytes() == binary, path
        return
    temporary = path.with_suffix(".pending")
    temporary.write_bytes(binary)
    os.replace(temporary, path)

images = {}
receipts = {}
finishes = []
for phase in phases:
    before = phase == "before"
    directory = actual / "before" if before else actual / "separate" / phase
    report = directory / ("control-browser.json" if before else "main-browser.json")
    closed = directory / "closed.json"
    capture = load(report)
    exit_receipt = load(closed)
    assert capture["completed"] and capture["section"] == phase and not capture["errors"] and not capture["failed"], report
    assert exit_receipt["exit"] == 0 and exit_receipt["node_closed"] and exit_receipt["chromium_pids"] and not exit_receipt["remaining"], closed
    assert exit_receipt["report_sha256"] == digest(report), report
    assert digest(city / "sessions" / phase / closed.name) == digest(closed), closed
    receipts[phase] = dict(report=str(report), report_sha256=digest(report), exit=str(closed), exit_sha256=digest(closed))
    finishes.append(exit_receipt["finished"])
    for row in capture["screenshots"]:
        name = row["file"]
        path = directory / name
        assert digest(path) == row["sha256"] == digest(city / name), path
        assert name not in images, name
        images[name] = row["sha256"]
view_report = viewer / "viewer.json"
viewer_closed = viewer / "closed.json"
v = load(view_report)
exit_receipt = load(viewer_closed)
assert v["passed"] and len(v["views"]) == (6 if order == 243 else 4) and len(v["downloads"]) == 4
assert exit_receipt["code"] == 0 and exit_receipt["node_closed"] and exit_receipt["chromium_pids"] and not exit_receipt["remaining_chromium"]
assert exit_receipt["report_sha256"] == digest(view_report)
finishes.append(exit_receipt["closed"])
receipts["standalone"] = dict(report=str(view_report), report_sha256=digest(view_report), exit=str(viewer_closed), exit_sha256=digest(viewer_closed))
for row in v["views"]:
    name = row["filename"]
    assert digest(viewer / name) == row["sha256"] == digest(city / "standalone" / name)
    images["standalone/" + name] = row["sha256"]

if not args.review:
    print(json.dumps({"images": images}, ensure_ascii=False, indent=2))
    raise SystemExit
review = load(args.review)
assert set(review["images"]) == set(images)
for name, sha in images.items():
    observation = review["images"][name]
    assert observation["sha256"] == sha and observation["observation"].strip(), name
assert load(city / "release-evidence.json")["passed"]
copies = {key: dict(sha256=value["sha256"], bytes=value["bytes"]) for key,value in v["downloads"].items()}
review_target = city / "visual-review.json"
stable_write(review_target, review)
receipt = dict(order=order, passed=True, exit=0, code=0, exit_code=0, remaining=[], remaining_chromium=[], final_closed_at=max(finishes), reports=receipts, receipts=receipts, all_captures_visually_reviewed=True, after_real_screenshot_review=True, visual_review_sha256=digest(review_target), views_reviewed=True, screenshots=images, actual_saved_downloads=copies)
target = actual / "slot-released.json" if order == 199 else work / "243-map-slot-released.json"
if order == 243:
    assert hashlib.sha256(Path('/tmp/shanghai-main-243/verify-538-return.py').read_bytes()).hexdigest()=='317bac5df61ca966fc0669774eb345ab53f63f101a08e6b885970f76187f69ea'
    receipt['independent_538_return_sha256']=__import__('runpy').run_path('/tmp/shanghai-main-243/verify-538-return.py')['verify']()
if order == 243:
    for key, path in {
        'guest308_native':Path('/tmp/chi308/native-closed.json'), 'guest308_viewer':Path('/tmp/chi308/viewer-closed.json'),
        'independent409':Path('/tmp/linong409/development-native/243-development-returned.json'),
        'independent560':Path('/dev/shm/root-zheng560/development-native/early-development-returned.json'),
        'independent564':Path('/dev/shm/root-huanlong564/development-native/early-development-returned.json'),
    }.items():
        true_exit = load(path)
        assert true_exit['passed'] and true_exit['exit_code']==0 and not true_exit.get('remaining',true_exit.get('remaining_children'))
        receipt[key+'_sha256']=digest(path)
stable_write(target, receipt)
stable_write(city / "slot-released.json", receipt)
print(target, digest(target))
