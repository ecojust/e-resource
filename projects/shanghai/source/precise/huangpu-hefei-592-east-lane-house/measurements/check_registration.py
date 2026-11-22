"""Compare separately read architectural corners through the fitted exterior-plane cameras."""
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "source"))
from hefei_photo_plane import CALIBRATION, on_side, pixel


def build():
    rows = []
    differences = []
    for name, point in CALIBRATION["opening_ties"].items():
        xyz = point["xyz"]
        positions = []
        for camera, uv in point["observed_pixels"].items():
            if uv is None or None in uv:
                continue
            predicted = pixel(xyz, camera)
            side = on_side(*uv, camera=camera)
            rows.append({"feature": name, "camera": camera, "native_px": uv,
                         "measured_xyz_m": side, "predicted_px": predicted,
                         "residual_px": float(np.linalg.norm(np.subtract(predicted, uv)))})
            positions.append((camera, np.array(side)))
        for i, (a, p) in enumerate(positions):
            for b, q in positions[i+1:]:
                differences.append({"feature": name, "pair": [a,b], "distance_m": float(np.linalg.norm(q-p))})
    residuals = [r["residual_px"] for r in rows]
    distances = [r["distance_m"] for r in differences]
    west = np.array(CALIBRATION["cameras"]["2015_west"]["wgs84"])
    oblique = np.array(CALIBRATION["cameras"]["2015_oblique"]["wgs84"])
    baseline = float(np.linalg.norm((west-oblique)*[111320*np.cos(np.deg2rad((west[1]+oblique[1])/2)), 110870]))
    return {"coverage": "West gable plane, upper openings only. Excludes the two corner-u constraints, branch-obscured endpoints and the ground opening used as a later-year check.",
            "interpretation": "Residuals describe agreement of points used for the local fit. They are not an independent survey of elevation or a precision statement for the adjacent lane, roof or street-door plane.",
            "camera_baseline_m": baseline, "projection_residual_median_px": float(np.median(residuals)),
            "projection_residual_max_px": float(np.max(residuals)),
            "same_corner_in_two_camera_plane_solutions_median_m": float(np.median(distances)),
            "same_corner_in_two_camera_plane_solutions_max_m": float(np.max(distances)),
            "observations": rows, "separate_plane_solutions": differences}


if __name__ == "__main__":
    path = HERE / "west-gable-photo-agreement.json"
    result = build()
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    print(len(result["observations"]), len(result["separate_plane_solutions"]),
          result["projection_residual_median_px"], result["projection_residual_max_px"],
          result["same_corner_in_two_camera_plane_solutions_median_m"], result["same_corner_in_two_camera_plane_solutions_max_m"])
