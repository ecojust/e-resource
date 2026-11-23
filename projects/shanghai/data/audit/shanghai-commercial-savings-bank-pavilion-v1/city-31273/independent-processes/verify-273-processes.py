"""Re-read the bank's ten city stages, the new and original independent views, downloads and dated guest attempts."""
from pathlib import Path
import hashlib
import json

PREFIX = "city-31273/independent-processes"
STAGES = ("control", "mobile-card", "mobile-pin", "desktop-card", "desktop-pin",
          "street", "roof", "timber-screens", "glazed-eaves", "distant")

def read(path):
    return json.loads(path.read_bytes())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify(audit, order, names):
    assert order == 273
    root = Path(audit)
    folder = root / PREFIX
    index = read(folder / "process-index.json")
    assert index["order"] == order
    verified = {f"{PREFIX}/process-index.json", f"{PREFIX}/verify-273-processes.py"}
    for name, row in index["files"].items():
        assert name.startswith(PREFIX + "/") and ".." not in Path(name).parts
        p = root / name
        assert p.stat().st_size == row["bytes"] and sha(p) == row["sha256"], name
        verified.add(name)
    assert verified <= set(names)
    observed = read(folder / "visual-review.json")["images"]
    seen = set()
    for phase in STAGES:
        d = folder / phase
        c = read(d / "closed.json")
        report_file = d / ("control-browser.json" if phase == "control" else "main-browser.json")
        r = read(report_file)
        assert c["exit_code"] == 0 and c["node_closed"] and c["cdp_closed"] and c["chromium_pids"]
        assert not c["remaining"] and not c["remaining_chromium"]
        assert sha(report_file) == c["report_sha256"]
        assert sha(d / "actual-driver.cjs") == r["scriptSha256"] == r["source_code_sha256"] == c["source_code_sha256"]
        assert r["completed"] and not r["errors"] and not r["failed"] and r["phase"] == phase
        calibration = r["viewportCalibration"]
        assert sha(d / calibration["image"]) == calibration["sha256"]
        for v in r["views"]:
            assert v["glError"] == 0 and not v["contextLost"]
            assert all(g["found"] == g["expected"] for g in v.get("ground", []))
        if phase in ("mobile-pin","desktop-pin"):
            assert any(p["pointer"]["trusted"] and p["pointer"]["on_canvas"] and p["landed"] == r["id"] for p in r["realBeaconInputs"])
        assert len(r["screenshots"]) == len(r["webglCaptures"]) == len(r["displayCaptures"]) == 1
        for k in ("screenshots","webglCaptures"):
            for image in r[k]:
                p = d / image["file"]
                assert sha(p) == image["sha256"] and p.stat().st_size == image["bytes"]
                if k == "screenshots":
                    seen.add(p.name)
                    assert observed[p.name]["sha256"] == image["sha256"] and observed[p.name]["observation"]
        for image in r["displayCaptures"]:
            assert sha(d / image["displayImage"]) == image["displayImageSha256"]
    failure=folder/'attempts/street-collision-return-before-fix/first-failed-session'
    failed=read(failure/'failed-exit.json')
    assert failed['phase']=='street' and failed['exit_code']==1 and failed['cdp_closed'] and failed['node_closed'] and not failed['remaining']
    assert failed['report_sha256']==sha(failure/'main-browser.json') and failed['source_code_sha256']==sha(failure/'actual-driver.cjs')
    assert "null !== 'open'" in (failure/'node.log').read_text()
    missed=read(folder/'attempts/first-wait-338-viewer/338-viewer-deferred.json')
    assert missed['deferred'] and not missed['started'] and not missed['attempted'] and len(missed['missing'])==2
    assert missed['source_sha256']==sha(folder/'mobile-pin/closed.json') and missed['host_report_sha256']==sha(folder/'mobile-pin/main-browser.json')
    for phase,t in [('control','native'),('mobile-pin','viewer')]:
        closed=read(folder/'guest'/(t+'-closed.json'))
        assert closed['exit']==0 and closed['all_processes_closed'] and not closed['remaining'] and closed['host_receipt_sha256']==sha(folder/phase/'closed.json')
    current=folder/'standalone'
    ticket=read(current/'closed.json')
    report=read(current/'viewer.json')
    assert ticket['exit_code']==0 and ticket['chromium'] and not ticket['remaining'] and ticket['passed']
    assert ticket['report_sha256']==sha(current/'viewer.json') and ticket['driver_sha256']==report['scriptSHA256']==sha(current/'formal-viewer.cjs')
    assert ticket['prior_sha256']==sha(folder/'distant/closed.json') and len(report['views'])==4
    for v in report['views']:
        name='standalone/'+v['filename']
        assert observed[name]['sha256']==v['sha256']==sha(current/v['filename']) and observed[name]['observation']
        seen.add(name)
    original=folder/'original-standalone'
    original_review=read(original/'earlier-six-review.json')
    earlier=read(original/'viewer.json')
    closed=read(original/'closed.json')
    assert sha(original/'viewer.json')==original_review['original_report_sha256']==closed['report_sha256']
    assert closed['exit']==0 and closed['node_closed'] and closed['chromium_pids'] and not closed['remaining']
    assert len(earlier['views'])==len(original_review['images'])==6
    for v in earlier['views']:
        p=original/v['filename']
        assert sha(p)==v['sha256']==original_review['images'][p.name]['sha256'] and original_review['images'][p.name]['observation']
    assert len(report['downloads'])==4 and report['downloads'].keys()==earlier['downloads'].keys()
    for role,item in report['downloads'].items():
        p=current/'saved'/item['file']
        assert p.stat().st_size==item['bytes'] and sha(p)==item['sha256']==earlier['downloads'][role]['sha256'] and item['saveAsVerified']
    assert set(observed)==seen and len(seen)==14
    return verified
