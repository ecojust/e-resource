"""Recompute the two photographic cameras from manually measured pixel coordinates.

Usage: python calibrate_rear.py --output registered-rear.json

Photographs are identified by SHA-256 in research-sources.json. The numerical
calibration is reproducible offline using NumPy and SciPy.
"""
from argparse import ArgumentParser
from pathlib import Path
import json
import math

import numpy as np
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent
SIZES = {"25": (650, 487), "04": (1247, 885)}


def camera_rotation(yaw, pitch, roll):
    yaw, pitch, roll = np.radians([yaw, pitch, roll])
    forward = np.array([math.sin(yaw) * math.cos(pitch),
                        math.cos(yaw) * math.cos(pitch), math.sin(pitch)])
    right = np.array([math.cos(yaw), -math.sin(yaw), 0])
    down = np.cross(forward, right)
    return np.stack((math.cos(roll) * right + math.sin(roll) * down,
                     -math.sin(roll) * right + math.cos(roll) * down, forward))


class PhotographicCamera:
    def __init__(self, key, intrinsic):
        self.key = key
        self.f = float(intrinsic[3])
        self.rotation = camera_rotation(*intrinsic[:3])
        width, height = SIZES[key]
        self.cx, self.cy = (width - 1) / 2, (height - 1) / 2

    def ray(self, uv):
        return np.array([(uv[0] - self.cx) / self.f,
                         (uv[1] - self.cy) / self.f, 1.0]) @ self.rotation

    def wall(self, uv, depth):
        direction = self.ray(uv)
        return self.center + direction * ((depth - self.center[1]) / direction[1])

    def pixel(self, xyz):
        x, y, z = self.rotation @ (xyz - self.center)
        return np.array([self.cx + self.f * x/z, self.cy + self.f * y/z])

    def local_line_direction(self, axis, middle):
        # This form remains finite when the vanishing point is at infinity.
        x, y, z = self.rotation[:, axis]
        direction = np.array([self.f * x + (self.cx - middle[0]) * z,
                              self.f * y + (self.cy - middle[1]) * z])
        return direction / np.linalg.norm(direction)

    def record(self):
        k = np.array([[self.f, 0, self.cx], [0, self.f, self.cy], [0, 0, 1]])
        p = k @ np.column_stack((self.rotation, -self.rotation @ self.center))
        width, height = SIZES[self.key]
        return dict(width=width, height=height, f=self.f, cx=self.cx, cy=self.cy,
                    R=self.rotation.tolist(), C=self.center.tolist(), P=p.tolist())


def scene(params, origin_pixel):
    masa = PhotographicCamera("25", params[:4])
    gao = PhotographicCamera("04", params[5:9])
    distance_to_facade = params[4]
    landing_height = params[12]
    direction = masa.ray(origin_pixel)
    masa.center = np.array([0., 0., landing_height]) - direction * distance_to_facade / direction[1]
    gao.center = params[9:12]
    return masa, gao


def predictions(params, picks, role=None):
    masa, gao = scene(params, picks["scale"]["entrance_center_at_top_landing_25"])
    result = {}
    for name, plane, uv_gao, uv_masa, sigma_masa, use in picks["ties"]:
        if role and use != role:
            continue
        xyz = masa.wall(uv_masa, params[13] if plane == "rail" else 0)
        result[name] = (gao.pixel(xyz) - uv_gao, xyz, sigma_masa, use)
    return result


def residuals(params, picks):
    scale = picks["scale"]
    cameras = scene(params, scale["entrance_center_at_top_landing_25"])
    errors = []
    for camera in cameras:
        sections = picks["lines"][camera.key]
        for direction, segments in sections.items():
            axis = 0 if direction == "x" else 2
            for x, y, k, j in segments:
                vector = np.array([k - x, j - y])
                middle = np.array([(x + k) / 2, (y + j) / 2])
                u = camera.local_line_direction(axis, middle)
                error = vector[0] * u[1] - vector[1] * u[0]
                errors.append(error / (1.6 if camera.key == "25" else 2.5))
    for delta, _, sigma, _ in predictions(params, picks, "fit").values():
        errors.extend(delta / (sigma * 3.0))
    # The SX160 uses a 1/2.3-inch sensor. Published EXIF gives a 5 mm lens.
    # The focal of the cropped historical shot is weakly constrained.
    errors.extend([(params[3] - 526) / 26, (params[8] - 1300) / 570,
                   (params[12] - scale["stair_rise_estimate_m"]) / scale["stair_rise_uncertainty_m"],
                   (params[14] - 1.15) / .55])
    for camera in cameras:
        head, sill = scale["scale_observations"][camera.key]
        height = camera.wall(head, params[14])[2] - camera.wall(sill, params[14])[2]
        errors.append((height - scale["inner_dark_door_leaf_m"]) / .025)
    return np.array(errors)


def calibrate(picks):
    initial = [-18, 13, 0, 526, 14, 8, 1, 0, 1270, -1, -12, 1.65, .84, -.65, 1.15]
    lower = [-58, -6, -10, 410, 5, -40, -10, -10, 480, -18, -32, .7, .32, -2.35, .15]
    upper = [15, 48, 10, 640, 28, 40, 25, 10, 3500, 14, -3, 3.4, 1.3, .15, 3.5]
    fit = least_squares(residuals, initial, args=(picks,), bounds=(lower, upper),
                        loss="soft_l1", f_scale=1.0, x_scale="jac", max_nfev=1300)
    if not fit.success:
        raise RuntimeError(fit.message)
    params = fit.x
    cameras = scene(params, picks["scale"]["entrance_center_at_top_landing_25"])
    observations = {}
    groups = {"fit": [], "check": []}
    for name, (delta, xyz, _, role) in predictions(params, picks).items():
        observations[name] = dict(residual_in_Gao04_pixels=delta.tolist(), xyz=xyz.tolist(), role=role)
        groups[role].append(float(np.linalg.norm(delta)))
    return {"generator": "calibrate_rear.py", "picks": "registration-picks.json", "params": list(params),
            "cameras": {c.key: c.record() for c in cameras}, "wall_y": 0.0,
            "rail_face_y": float(params[13]), "door_y": float(params[14]), "landing_z": float(params[12]),
            "scale": picks["scale"], "observations": observations,
            "summary_gao04_native_pixels": {role: dict(count=len(v), median=float(np.median(v)),
                                                        maximum=max(v)) for role, v in groups.items()}}


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--picks", type=Path, default=HERE / "registration-picks.json")
    parser.add_argument("--output", type=Path, default=HERE / "registered-rear.json")
    args = parser.parse_args()
    result = calibrate(json.loads(args.picks.read_text()))
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result["summary_gao04_native_pixels"], indent=2))
