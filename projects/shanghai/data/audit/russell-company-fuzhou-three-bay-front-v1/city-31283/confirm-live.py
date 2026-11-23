"""Bind each inspected screenshot, browser process and saved download before the next city's handoff."""
import argparse
import hashlib
import json
import os
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("order", type=int, choices=[199, 283])
parser.add_argument("--review", type=Path)
args = parser.parse_args()
order = args.order
work = Path(__file__).parent
stage = 31000 + order
audit_name = {199: "wukang-east-annex-v1", 283: "russell-company-fuzhou-three-bay-front-v1"}[order]
city = Path('/dev/shm/russell283-live/verified-audit/city-31283')
actual = work / "evidence" / str(order)
viewer = work / f"viewer-{stage}"
phases = ["before", "phone", "desktop", "details", "touch", "architecture"]
if order == 283:
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
assert v["passed"] and len(v["views"]) == 6 and len(v["downloads"]) == 4
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
receipt = dict(all_captures_visually_reviewed=True,real_browser_process_exits=receipts,finished=max(finishes),order=order, passed=True, exit=0, code=0, exit_code=0, remaining=[], remaining_chromium=[], final_closed_at=max(finishes), reports=receipts, receipts=receipts, after_real_screenshot_review=True, visual_review_sha256=digest(review_target), views_reviewed=True, screenshots=images, actual_saved_downloads=copies)
target = actual / "slot-released.json" if order == 199 else work / "283-map-slot-released.json"
windows={}
for kind in ('native','viewer'):
    returned=work/f'348-{kind}-returned.json'
    deferred=work/f'348-{kind}-deferred.json'
    chosen=[p for p in (returned,deferred) if p.is_file()]
    assert len(chosen)==1,(kind,chosen)
    guest=load(chosen[0]);assert guest['order']==348 and guest['phase']==kind
    assert digest(Path(guest['host_closed']))==guest['host_closed_sha256']
    if 'actual_receipt' in guest:
        from guest_result import verify
        physical=Path(guest['actual_receipt'])
        assert digest(physical)==guest['sha256']
        state=verify(kind,Path(guest['host_closed']),physical)
        assert (state=='complete')==(chosen[0]==returned)
    else:
        assert guest['deferred'] is True and guest['missing'] and not guest['native_started'] and not guest['viewer_started']
        state='deferred-before-launch'
    windows[kind]=dict(result=state,receipt=str(chosen[0]),sha256=digest(chosen[0]))
receipt['guest_348']=windows
receipt['real_browser_process_exits']={phase:load(Path(r['exit'])) for phase,r in receipts.items()}
stable_write(target, receipt)
stable_write(city / "slot-released.json", receipt)
print(target, digest(target))
