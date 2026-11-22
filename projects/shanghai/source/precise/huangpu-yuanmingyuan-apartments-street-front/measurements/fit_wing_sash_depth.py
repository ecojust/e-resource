"""Triangulate eight shared thin-rail intersections on the east frontage."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "source"))
from east_photo_plane import on_wall, pixel
from wing_casements import openings

# Upper-left origin of each 182 by 200 rectangle on the front masonry plane.
# Values mark the meeting stile where the single lower narrow bar meets it.
SAMPLES = {
    "near-upper-1": [[78, 155], [120, 162]],
    "near-upper-2": [[70, 159], [111, 165]],
    "near-lower-1": [[71, 142], [125, 147]],
    "near-lower-2": [[64, 143], [113, 147]],
    "far-upper-1": [[47, 154], [81, 162]],
    "far-upper-2": [[47, 151], [82, 161]],
    "far-lower-1": [[32, 140], [73, 148]],
    "far-lower-2": [[33, 136], [70, 142]],
}
VIEWS = ["2014_oblique", "2016_front"]


def fit(row, observations):
    measured = [np.asarray(observations[view], dtype=float) for view in VIEWS]
    pixels_sigma = [2.6, 1.1]
    def residual(xyz):
        return np.concatenate([(pixel(xyz, v) - p) / s for v, p, s
                               in zip(VIEWS, measured, pixels_sigma)])
    seed = on_wall(*measured[0], y=0.3, camera=VIEWS[0])
    result = least_squares(residual, seed)
    return {
        "window": row["label"],
        "feature": "centre of the meeting stile at the thin lower glazing bar",
        "pixels": dict(zip(VIEWS, [p.round(3).tolist() for p in measured])),
        "xyz_m": result.x.round(4).tolist(),
        "reprojection_error_px": {
            view: round(float(np.linalg.norm(pixel(result.x, view) - p)), 3)
            for view, p in zip(VIEWS, measured)
        },
        "partially_occluded_in_2016": row["label"] in ("near-lower-1", "far-lower-1"),
    }


if __name__ == "__main__":
    source = json.loads((HERE / "wing-sash-correspondences.json").read_bytes())
    immutable = source["fixed_native_px"]
    rows = [fit(row, immutable[row["label"]]) for row in openings() if row["label"] in immutable]
    keep = [r["xyz_m"][1] for r in rows if not r["partially_occluded_in_2016"]]
    raw = {
        "camera_sha256": hashlib.sha256((HERE / "east-front-cameras.json").read_bytes()).hexdigest(),
        "observed_native_pixels_sha256": hashlib.sha256((HERE / "wing-sash-correspondences.json").read_bytes()).hexdigest(),
        "views": VIEWS, "front_rectification_px": [182, 200], "observations": SAMPLES,
        "triangulated": rows, "clear_samples": len(keep),
        "median_clear_recess_m": float(np.median(keep)),
        "range_clear_recess_m": [min(keep), max(keep)],
        "basis": "Eight intersections read in the two photographs. Six are fully visible. The two lower meetings partly concealed by flags or figures are listed separately. Recess is relative to the white masonry front. Sash depths vary locally and the camera poses inherit the uncertainty of the elevation scale.",
    }
    target = HERE / "wing-sash-depth.json"
    target.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n")
    print(raw["median_clear_recess_m"], raw["range_clear_recess_m"])
    print([(r["window"], r["xyz_m"][1], r["reprojection_error_px"]) for r in rows])
