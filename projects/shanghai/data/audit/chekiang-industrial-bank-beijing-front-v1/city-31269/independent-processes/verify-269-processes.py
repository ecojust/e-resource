"""Re-read the bank's ten city stages, the six independent views, downloads and dated guest attempts."""
from pathlib import Path
import hashlib
import json

PREFIX = "city-31269/independent-processes"
STAGES = ("control", "mobile-card", "mobile-pin", "desktop-card", "desktop-pin",
          "street", "roof", "double-fret", "tripartite-windows", "distant")

def read(path):
    return json.loads(path.read_bytes())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify(audit, order, names):
    assert order == 269
    root = Path(audit)
    folder = root / PREFIX
    index = read(folder / "process-index.json")
    assert index["order"] == order
    verified = {f"{PREFIX}/process-index.json", f"{PREFIX}/verify-269-processes.py"}
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
    attempts = folder / "attempts"
    for p in sorted(attempts.glob("334-native-*/334-native-deferred.json")):
        r = read(p)
        assert r["host_receipt_sha256"] == sha(folder/"control/closed.json")
        assert r["attempted"] and r["exit"] != 0 and not r["remaining"] and r["wrapper_closed"]
        for k in ("launch_process","launch_log"):
            assert sha(p.parent/Path(r[k]).name) == r[k+"_sha256"]
    first = attempts/"334-native-first"
    assert "No space left on device" in next(first.glob("native-launch-*.log")).read_text()
    second = attempts/"334-native-second"
    assert "psutil.process_iter" in next(second.glob("native-launch-*.log")).read_text()
    wait=read(attempts/"334-viewer-first/334-viewer-deferred.json")
    assert not wait["started"] and not wait["attempted"] and wait["deferred"]
    assert len(wait["missing"]) == 3 and wait["host_receipt_sha256"] == sha(folder/"mobile-pin/closed.json")
    d = folder / "standalone"
    c = read(d / "closed.json")
    r = read(d / "viewer.json")
    assert c["exit_code"] == 0 and c["node_closed"] and c["chromium_pids"] and not c["remaining_chromium"]
    assert sha(d / "viewer.json") == c["report_sha256"] and r["passed"] and not r["pageErrors"]
    assert len(r["views"]) == 6 and set(r["downloads"]) == {"raw","full","lod","native"}
    for view in r["views"]:
        name = "standalone/" + view["filename"]
        assert observed[name]["sha256"] == sha(d/view["filename"]) == view["sha256"] and observed[name]["observation"]
        seen.add(name)
    for item in r["downloads"].values():
        f=d/item["saved"]
        assert item["saveAsVerified"] and f.stat().st_size == item["bytes"] and sha(f)==item["sha256"]
    assert set(observed)==seen and len(seen)==16
    return verified
