"""Refit visible courtyard pipe axes to Gao 04 and Gao 08 and report residuals."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent


def project_line(camera, axis, slope):
    first = camera @ [*axis, 5.244, 1.0]
    second = camera @ [*(axis + slope), 6.244, 1.0]
    line = np.cross(first, second)
    return line / np.linalg.norm(line[:2])


def refit():
    data_file = HERE / "pipe-centrelines.json"
    data = json.loads(data_file.read_bytes())
    registration = json.loads((HERE / "paired-entrance-cameras.json").read_bytes())
    cameras = [np.asarray(registration[k]) for k in ("camera_P", "camera_close_P")]
    collar = [[74, 1568], [297, 693]]
    equations = np.concatenate([camera[:2] - np.outer(uv, camera[2]) for camera, uv in zip(cameras, collar)])
    xyz = np.linalg.lstsq(equations[:, :3], -equations[:, 3], rcond=None)[0]
    result = {"measured_axes_sha256": hashlib.sha256(data_file.read_bytes()).hexdigest(),
              "west_collar_original_pixels": collar, "west_collar_triangulated_xyz": xyz.tolist()}
    for side, prior in (("west", 12.0), ("east", 9.0)):
        observed = data[side]
        pixels = [np.c_[rows, np.ones(len(rows))] for rows in observed["observed_pixels"]]

        def residual(params):
            axis, slope = params[:2], params[2:]
            return np.concatenate([points @ project_line(p, axis, slope) / scale
                                   for points, p, scale in zip(pixels, cameras, (7.114, 6.14))])

        if side == "west":
            axis = np.round(xyz[:2], 5)
            sol = least_squares(lambda delta: np.r_[residual(np.r_[axis, delta]), prior * delta], [0.0, 0.0])
            params = np.r_[axis, sol.x]
        else:
            sol = least_squares(lambda values: np.r_[residual(values), prior * values[2:]], [5.0, -0.75, 0.0, 0.0])
            params = sol.x
        errors = [points @ project_line(p, params[:2], params[2:]) for p, points in zip(cameras, pixels)]
        recorded = np.r_[observed["axis_at_5.244m"][:2], observed["delta_xy_per_m_z"]]
        result[side] = {"axis_at_z_5_244": params[:2].tolist(), "xy_change_per_z_unit": params[2:].tolist(),
                        "maximum_offset_from_recorded_parameters": float(np.max(abs(params - recorded))),
                        "residual_native_pixels": [row.tolist() for row in errors]}
    result["passed"] = all(result[s]["maximum_offset_from_recorded_parameters"] < 0.001 for s in ("west", "east"))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = refit()
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    raise SystemExit(int(not report["passed"]))
