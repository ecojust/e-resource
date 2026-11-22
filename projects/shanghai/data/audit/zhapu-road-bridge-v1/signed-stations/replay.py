"""Replay bridge crossings with the archived street inputs and a matching Shanghai site."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from urllib.parse import urljoin
from urllib.request import urlopen


def read(path):
    return json.loads(path.read_bytes())


def fetch(site, key, expected):
    with urlopen(urljoin(site, key), timeout=60) as response:
        body = response.read()
    if hashlib.sha256(body).hexdigest() != expected:
        raise ValueError(f"版本不匹配 {key}")
    return body


def replay(site):
    archive = Path(__file__).resolve().parent
    summary = read(archive / "summary.json")
    sources = read(archive / "actual-sources.json")
    for key, digest in summary["evidence"].items():
        if hashlib.sha256((archive / key).read_bytes()).hexdigest() != digest:
            raise ValueError(f"验收附件已改变 {key}")
    fetch(site, "data/candidate-city-integrations.json", summary["catalog_sha256"])

    with tempfile.TemporaryDirectory() as scratch:
        work = Path(scratch)
        tests = work / "tests"
        records = work / "evidence"
        tests.mkdir()
        records.mkdir()
        for row in sources["runtimes"]:
            key = row["path"]
            if key.startswith(("src/", "vendor/")):
                path = work / key
                path.parent.mkdir(exist_ok=True)
                path.write_bytes(fetch(site, key, row["sha256"]))
        (work / "package.json").write_text('{"type":"module"}\n')
        orders = [221, 223, 230]
        config = dict(url=site, catalog_sha256=summary["catalog_sha256"], orders=orders)
        (tests / "input-binding.json").write_text(json.dumps(config))
        for n in orders:
            shutil.copyfile(archive / f"{n}-input.json", records / f"{n}-input.json")
        for script in ["real-walk.mjs", "shared-segments.mjs"]:
            shutil.copyfile(archive / script, tests / script)
            subprocess.run(["node", tests / script], check=True, env={**os.environ, "BRIDGE_LIVE": "1"})

        walk = read(records / "walk.json")
        shared = read(records / "shared-sidewalk-id.json")
        assert walk["passed"] and shared["passed"]
        assert walk["reports"] == read(archive / "walk.json")["reports"]
        assert shared == read(archive / "shared-sidewalk-id.json")
        print("三桥36次通行、162处桥面采样和576项道路归属复验通过。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site", help="当前验收版本的 projects/shanghai/ HTTP(S) 根网址")
    replay(parser.parse_args().site.rstrip("/") + "/")
