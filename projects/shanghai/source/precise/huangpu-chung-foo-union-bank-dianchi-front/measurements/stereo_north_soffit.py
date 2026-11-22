"""Measure the intersections of the longitudinal and transverse soffit beams.

Pass the two original photo paths to repeat the intensity-profile checks. Photos are
read locally. The output contains measurements only. Requires numpy, scipy and Pillow.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "source"))
from photo_plane import CAMERAS, pixel, position

# (s,t) is a rectified address in the original image's pixel units. At reference
# column cx, a transverse moulding crosses row t. At reference transverse row t0,
# a longitudinal joist crosses column s. The actual image position is their intersection.
REFERENCE = {"wide": (249.0, 818.6), "close": (1120.0, 1118.8)}
PICKS = [
    ("front transverse, east joist", (1006., 1118.8), (243., 818.6)),
    ("front transverse, west joist", (1365., 1118.8), (304., 818.6)),
    ("back transverse, east joist", (1008., 1176.8), (246.5, 831.4)),
    ("inner edge of back transverse, east joist", (1008., 1196.8), (249., 835.6)),
]


def source_pixel(view, s, t):
    cam = CAMERAS[view]
    vx = cam[:, 0] / cam[2, 0]
    vy = cam[:, 1] / cam[2, 1]
    cx, t0 = REFERENCE[view]
    s_v = vx[1] + (t0 - vx[1]) * (s - vx[0]) / (cx - vx[0])
    q = np.cross(np.cross([cx, t, 1.0], vx), np.cross([s, s_v, 1.0], vy))
    return q[:2] / q[2]


def intersect(close_uv, wide_uv):
    def error(depth):
        return pixel(position(*close_uv, depth[0], "close"), "wide") - wide_uv
    fit = least_squares(error, [-3.0])
    return position(*close_uv, fit.x[0], "close"), np.linalg.norm(fit.fun)


def profile(photo, view):
    from PIL import Image

    image = np.array(Image.open(photo).convert("L"), dtype=float)
    grad = gaussian_filter(image, (1, 1), order=(1, 0))
    cam = CAMERAS[view]
    vp = cam[:, 0] / cam[2, 0]
    cx, _ = REFERENCE[view]
    if view == "wide":
        xs = np.arange(191, 307)
        rows = [808.8, 818.6, 824.4, 831.4, 835.6]
    else:
        xs = np.arange(730, 1620)
        rows = [1074.5, 1118.8, 1145.2, 1176.8, 1196.8]
    records = []
    for t in rows:
        ys = vp[1] + (t - vp[1]) * (xs - vp[0]) / (cx - vp[0])
        derivative = map_coordinates(grad, [ys, xs], order=1)
        records.append({"reference_v": t, "median_vertical_derivative": float(np.median(derivative))})
    return records


def solve():
    result = []
    for label, close_address, wide_address in PICKS:
        cuv = source_pixel("close", *close_address)
        wuv = source_pixel("wide", *wide_address)
        xyz, residual = intersect(cuv, wuv)
        jitter = [intersect(cuv, wuv + d)[0] for d in [[2, 0], [-2, 0], [0, 1], [0, -1]]]
        result.append({"intersection": label, "close_rectified_st": close_address, "wide_rectified_st": wide_address,
                       "close_original_px": cuv.tolist(), "wide_original_px": wuv.tolist(), "position_m": xyz.tolist(),
                       "triangulation_reprojection_px": residual, "wide_pick_sensitivity_range_xyz_m":np.ptp(jitter, axis=0).tolist()})
    alt = []
    for i, alt_s in [(0, 192.4), (1, 242.6)]:
        beam = PICKS[i]
        xyz, _ = intersect(source_pixel("close", *beam[1]), source_pixel("wide", alt_s, beam[2][1]))
        alt.append(xyz.tolist())
    ceiling_z = float(np.mean([r["position_m"][2] for r in result[:3]]))
    covers = []
    for u, v in [[852,1133], [1188,1124], [1518,1117]]:
        cam = CAMERAS["close"]
        h = cam[:, [0, 1, 3]].copy()
        h[:, 2] += ceiling_z * cam[:, 2]
        p = np.linalg.solve(h, [u, v, 1.0])
        xyz = [p[0]/p[2], p[1]/p[2], ceiling_z]
        covers.append({"close_original_px":[u,v],"at_beam_height_projected_wide_px":pixel(xyz,"wide").tolist(),
                       "independent_wide_centre":False})
    r = [b["position_m"] for b in result]
    return {"axes":"The same west, inward-south and up coordinate frame as two-north-cameras.json.",
            "intersection_method":"Identify actual change of transverse profile at both visible longitudinal joists. Register the first two crossings as a pair, then follow the east joist to the two rear moulding edges.",
            "intersection_picks":result, "mean_first_three_height_m":ceiling_z,
            "transverse_line_horizontal_spacing_m":r[1][0]-r[0][0],
            "transverse_spacing_in_depth_m":r[2][1]-r[0][1],
            "rear_beam_inside_shaft_axis_m":r[2][1]-json.loads((HERE/"north-portico-axes.json").read_bytes())["adopted_axis_y_m"],
            "innermost_traced_edge_inside_shaft_axis_m":r[3][1]-json.loads((HERE/"north-portico-axes.json").read_bytes())["adopted_axis_y_m"],
            "periodic_one_bay_east_alternative_xyz":alt,
            "interpretation":"The alternate repeated pair puts the ceiling below the photographed column capitals. The traced rear beam extends past Y=-1.56 and its inner moulding reaches approximately -0.94. A rear grille at Y=-3.01 would intersect the two visible rear beam traces. Of the two repeated grille assignments, Y about -0.27 is consistent with their order.",
            "unmeasured_relief":"The two exposed transverse joist faces and the inner moulding are at different levels. The independent cabinet or coffer relief is not recovered from their height difference. The centre of the third round cover is occluded by the paired capitals in the oblique view.",
            "close_round_cover_control_projection":covers,
            "precision":"Residuals measure agreement for these selected point pairs. Four independent upper-window controls have RMS reprojection errors of 3.23 px in the oblique view and 4.72 px in the close view; street grade and effective camera intrinsics introduce additional metre-scale uncertainty."}


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--wide", type=Path)
    cli.add_argument("--close", type=Path)
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()
    data = solve()
    if bool(args.wide) != bool(args.close):
        cli.error("Supply both original photos to sample the intensity profiles.")
    if args.wide:
        controls = json.loads((HERE/"north-photo-controls.json").read_bytes())
        data["verified_original_profiles"] = {}
        for view, photo in [("wide", args.wide), ("close", args.close)]:
            with photo.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if digest != controls[view+"_registration"]["photo_sha256"]:
                raise ValueError("Original image SHA mismatch for "+view)
            data["verified_original_profiles"][view] = {"source_sha256":digest,"rows":profile(photo, view)}
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n")
