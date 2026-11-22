"""Recover the July arc depths from the recorded pixel triplets and calibrated lens."""

import json, math
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / name).read_bytes())


def relative_depth(points, bearing, pitch, roll, focal):
    b, p, r = np.radians([bearing, pitch, roll])
    right = np.array([math.cos(b), -math.sin(b), 0.0])
    front = np.array([math.sin(b) * math.cos(p), math.cos(b) * math.cos(p), math.sin(p)])
    up = np.cross(right, front)
    right, up = right * math.cos(r) + up * math.sin(r), -right * math.sin(r) + up * math.cos(r)
    plane = []
    for u, v in points:
        ray = front + ((u - 675) / focal) * right - ((v - 450) / focal) * up
        plane.append(ray[:2] / ray[2])
    left, mid, right = plane
    dx, dy = right - left
    ax, ay = mid - left
    return abs(ax * dy - ay * dx) / (dx * dx + dy * dy)


def verify():
    j = load("july-arc-depth.json")
    p = j["parameters"]
    measurements = {}
    for s in j["measurements"]:
        ratio = relative_depth(
            s["photo_pixels"], p["bearing_deg"], p["pitch_deg"], p["roll_deg"], p["focal_px"]
        )
        value = ratio * s["adopted_chord_width_m"]
        assert abs(value - s["sagitta_m"]) < 1e-7
        assert s["sensitivity_m"][0] <= value <= s["sensitivity_m"][1]
        measurements[s["name"]] = value
    c = load("courtyard-facade-fit.json")
    levels = c["photo"]["levels"]
    assert abs(c["width_m"] - 6.48) < 0.01 and 17.0 < levels["gable ball"] < 18.0
    d = load("independent-cameras.json")
    a = d["cameras"]["2"]
    b = d["cameras"]["19"]
    assert len(a["registrations"]) >= 15 and len(b["registrations"]) >= 15
    registered = load("../reference-review.json")["sources"][1]["original"]["sha256"]
    assert (
        j["original_source_sha256"]
        == registered
        == "a0b5665c7a5a24a2208ceb247137dbe8a74ea89a0496aaac9f649b52cdf69553"
    )
    assert len({a["source_sha256"], b["source_sha256"], registered}) == 3
    return measurements


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
