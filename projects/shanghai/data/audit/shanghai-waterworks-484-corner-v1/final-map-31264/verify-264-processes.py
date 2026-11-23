"""Recheck the original closures, failed attempts and published ordinary images."""
from pathlib import Path
import hashlib,json

def verify(audit, order, names):
    assert order==264
    root=Path(audit)
    relative="final-map-31264/"
    index_path=relative+"process-and-failure-index.json"
    digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    read=lambda path:json.loads(path.read_bytes())
    index=read(root/index_path)
    assert index["order"]==264 and index["phases"]==7 and index["images"]==18
    checked=set()
    for key,stamp in index["files"].items():
        f=root/key
        assert key.startswith(relative) and f.stat().st_size==stamp["bytes"] and digest(f)==stamp["sha256"]
        checked.add(key)
    checked.add(index_path)
    assert checked<=set(names)
    directory=root/relative
    assert "has no attribute 'datetime'" in (directory/"attempts/264-host-before-node/reboot-wait.log").read_text()
    branch=directory/"attempts/329-before-raw"
    before=read(branch/"record.json")
    assert "no guest Node" in before["event"] and all(digest(branch/k)==v for k,v in before["sha256"].items())
    branch=directory/"attempts/264-distant-cluster"
    first=read(branch/"main-browser.json")
    assert read(branch/"process.json")["exit_code"]==1 and not first["completed"] and "null" in first["failure"]
    assert not any("map-distant.png" in k for k in checked if k.startswith(relative+"attempts/264-distant-cluster/"))
    observations=read(directory/"visual-review.json")["images"]
    seen=set()
    for phase in ["before","phone","desktop","architecture","mouse","touch","distant"]:
        stage=directory/phase
        closure=read(stage/"closed.json")
        assert closure["node_closed"] and closure["exit_code"]==0 and not closure["remaining_children"] and not closure["remaining_chromium"]
        f=stage/("control-browser.json" if phase=="before" else "main-browser.json")
        report=read(f)
        assert report["completed"] and closure["report_sha256"]==digest(f) and report["scriptSha256"]==closure["source_code_sha256"]==digest(stage/"actual-driver.cjs")
        for picture in report["screenshots"]:
            k=phase+"/"+picture["file"];seen.add(k);assert digest(stage/picture["file"])==observations[k]["sha256"]==picture["sha256"]
        assert read(stage/"real-frames.json")["report_sha256"]==digest(f)
        if phase=="distant":
            groups=[v for v in report["views"] for k,v in v.items() if isinstance(v,dict) and "actualHit" in v and "memberIds" in v]
            assert any(g["actualHit"]=="beacon-group:0-1" and index["id"] in g["memberIds"] for g in groups)
    viewer=read(directory/"standalone/viewer.json")
    assert viewer["passed"] and len(viewer["downloads"])==4 and all(i["saveAsVerified"] for i in viewer["downloads"].values())
    for frame in viewer["views"]:
        k="standalone/"+frame["filename"];seen.add(k);assert digest(directory/k)==observations[k]["sha256"]==frame["sha256"]
    assert set(observations)==seen and len(seen)==18
    return checked
