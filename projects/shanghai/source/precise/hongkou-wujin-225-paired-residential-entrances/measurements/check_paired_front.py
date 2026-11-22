"""Read the first triangle on each independently marked courtyard photograph ray."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "xuhui-pathe-records-office/measurements/city-contact"))
from glb_triangles import SerialScene

OBSERVATIONS = HERE / "paired-front-sightlines.json"
CAMERAS = HERE / "paired-entrance-cameras.json"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def check(path):
    observed = json.loads(OBSERVATIONS.read_bytes())
    cameras = json.loads(CAMERAS.read_bytes())
    scene = SerialScene(path)
    views = {}
    hits = total = 0
    for key, view in observed["views"].items():
        camera = np.asarray(cameras[view["camera"]])
        eye = np.linalg.solve(camera[:, :3], -camera[:, 3])
        tests = []
        for group, pixels in view["sightlines"].items():
            expected = observed["groups"][group]["expected"]
            for pixel in pixels:
                direction = np.linalg.solve(camera[:, :3], [*pixel, 1.0])
                first = scene.ray(eye, direction, 40.0)
                material = first["material"] if first else None
                tests.append({
                    "feature": group, "pixel": pixel, "first_material": material,
                    "first_xyz": np.round(first["point_enu_m"], 5).tolist() if first else None,
                    "passed": material in expected,
                })
        success = sum(test["passed"] for test in tests)
        assert len(tests) >= 35
        views[key] = {"photo_sha256": view["sha256"], "total": len(tests), "hits": success, "tests": tests}
        hits += success
        total += len(tests)
    assert set(views) == {"04", "08"}
    return {
        "mesh": path.name, "mesh_sha256": digest(path), "bytes": path.stat().st_size,
        "cameras_sha256": digest(CAMERAS), "sightlines_sha256": digest(OBSERVATIONS),
        "method": "First triangle in the entire mesh along each original photograph pixel ray, with a 40-unit search distance.",
        "features": observed["groups"], "views": views, "hits": hits, "total": total, "passed": hits == total,
    }
