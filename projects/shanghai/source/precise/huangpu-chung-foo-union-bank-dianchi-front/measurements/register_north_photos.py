"""Re-fit the 103 Dianchi Road facade and evaluate its six portico axes.

Usage: python register_north_photos.py [output-directory]
Requires numpy, scipy and the two JSON inputs beside this file.
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent
CONTROLS = json.loads((HERE / "north-photo-controls.json").read_bytes())
SITE = json.loads((HERE / "north-front-footprint.json").read_bytes())
keys = [f"{r}-{c}" for r in range(4) for c in range(5)]
points = np.array([[CONTROLS[v + "_window_head_centres_px"][k] for v in ("wide", "close")] for k in keys])
hold = CONTROLS["hold_out_indices"]
fitted = np.ones(20, dtype=bool)
fitted[hold] = False
scroll_wide = np.asarray(CONTROLS["wide_scroll_face_centres_px"])
scroll_close = np.asarray(CONTROLS["close_scroll_face_centres_px"][:5])


def normed(v):
    return v / np.linalg.norm(v)


def project(cam, xyz):
    q = np.column_stack((xyz, np.ones(len(xyz)))) @ cam.T
    return q[:, :2] / q[:, 2, None]


def homography(cam, y):
    h = cam[:, [0, 2, 3]].copy()
    h[:, 2] += y * cam[:, 1]
    return h


def inverse(cam, uv, y=0):
    q = np.linalg.solve(homography(cam, y), [*uv, 1])
    return np.array([q[0] / q[2], y, q[1] / q[2]])


def wide_camera(focal=567.0, grade=995.0):
    # The archive photo has nearly upright verticals and a displaced effective horizon.
    c = CONTROLS["wide_registration"]
    vp_x, vp_y = c["horizontal_vp_px"]
    roll = -c["vertical_du_per_dv"]
    k = np.array([[focal, 0, 400], [0, focal, vp_y + (400 - vp_x) * roll], [0, 0, 1.0]])
    dx = -normed(np.linalg.solve(k, [vp_x, vp_y, 1]))
    dz = normed(np.array([roll, -1.0, 0.0]))
    r = np.column_stack((dx, np.cross(dz, dx), dz))
    (u0, v0), (u1, v1) = c["wall_edges_px_at_given_v"]
    far_u = u0 - roll * (grade - v0)
    near_u = u1 - roll * (grade - v1)
    near_u -= roll * (near_u - far_u) * (grade - vp_y) / (far_u - vp_x)
    near_v = vp_y + (grade - vp_y) * (near_u - vp_x) / (far_u - vp_x)
    far = np.linalg.solve(k, [far_u, grade, 1])
    near = np.linalg.solve(k, [near_u, near_v, 1])
    width = round(SITE["north_edge_length_m"], 2)
    t_near, t_far = np.linalg.lstsq(np.column_stack((near, -far)), dx * width, rcond=None)[0]
    return k @ np.column_stack((r, (t_near * near + t_far * far) / 2))


def close_camera(params):
    rot = Rotation.from_rotvec(params[:3]).as_matrix()
    f = np.exp(params[6])
    cx, cy = CONTROLS["close_registration"]["principal_point_assumed"]
    k = np.array([[f, 0, cx], [0, f, cy], [0, 0, 1]])
    return k @ np.column_stack((rot, params[3:6]))


def feature_positions(params):
    xs, zs = params[7:12], params[12:16]
    windows = np.array([[x, 0, z] for z in zs for x in xs])
    columns = np.column_stack((params[18:24], np.repeat(params[16], 6), np.repeat(params[17], 6)))
    return windows, columns


def fit(focal=567., grade=995.):
    wide = wide_camera(focal, grade)
    seeds = np.array([inverse(wide, uv) for uv in points[:, 0]]).reshape(4, 5, 3)
    start_rot = Rotation.from_matrix([[1, 0, 0], [0, .5, -.8660254], [0, .8660254, .5]])
    start = [*start_rot.as_rotvec(), 0, 7, 11, np.log(1250)]
    initial = least_squares(lambda p: (project(close_camera(p), seeds.reshape(-1, 3)) - points[:, 1]).ravel(), start)
    init = np.r_[initial.x, seeds[:, :, 0].mean(0), seeds[:, :, 2].mean(1), -4.6, 7.2,
                 [inverse(wide, uv, -4.6)[0] for uv in scroll_wide]]

    def residual(params):
        close = close_camera(params)
        windows, cols = feature_positions(params)
        return np.r_[((project(wide, windows) - points[:, 0])[fitted] / [2.3, 2.0]).ravel(),
                     ((project(close, windows) - points[:, 1])[fitted] / [5, 3]).ravel(),
                     ((project(wide, cols) - scroll_wide) / [2, 2]).ravel(),
                     ((project(close, cols[:5]) - scroll_close) / [5, 5]).ravel()]

    p = least_squares(residual, init, loss="soft_l1").x
    return p, wide, close_camera(p)


def edge_distance(cam, uv, xy):
    a = inverse(cam, uv)[:2]
    d = inverse(cam, uv, 1)[:2] - a
    return abs(d[0] * (xy[1] - a[1]) - d[1] * (xy[0] - a[0])) / np.linalg.norm(d)


def solve_axes(wide, close):
    we = CONTROLS["wide_shaft_edges_u_at_v900"]
    ce = CONTROLS["close_shaft_edges_u_at_v1240"]
    wm = [np.mean(pair) for pair in we]
    cm = [np.mean(pair) if pair else None for pair in ce]
    depths = []
    for u, v in zip(wm, cm):
        if v is None:
            continue
        def delta(y):
            return inverse(wide, [u, 900], y)[0] - inverse(close, [v, 1240], y)[0]
        depths.append(-delta(0) / (delta(1) - delta(0)))
    y = float(np.median(depths))
    axes = []
    for i, u in enumerate(wm):
        wide_x = inverse(wide, [u, 900], y)[0]
        x = (wide_x + inverse(close, [cm[i], 1240], y)[0]) / 2 if cm[i] is not None else wide_x
        radii = {"wide": np.mean([edge_distance(wide, [k, 900], [x, y]) for k in we[i]])}
        if ce[i] is not None:
            radii["close"] = np.mean([edge_distance(close, [k, 1240], [x, y]) for k in ce[i]])
        z_marks = {}
        for name, key in [("base", "wide_shaft_base_v"), ("neck", "wide_neck_v"), ("top", "wide_abacus_top_v")]:
            v = CONTROLS[key][i]
            uv = [u - .012 * (v - 900), v]
            z = inverse(wide, uv, y)[2]
            pred_wide = project(wide, [[x, y, z]])[0]
            pred_close = project(close, [[x, y, z]])[0]
            z_marks[name] = {"z_m": z, "wide_pick_px": uv, "wide_reprojection_px": pred_wide.tolist(),
                             "close_reprojection_px": pred_close.tolist(),
                             "close_in_frame": bool(0 <= pred_close[0] < 2041 and 0 <= pred_close[1] < 1363)}
        axes.append({"index_east_to_west": i + 1, "x_m": x, "y_m": y, "radius_m_by_view": radii,
                     "shaft_axis_survey": "two photo silhouettes" if ce[i] else "single wide silhouette at pooled row depth",
                     "z_and_pixels": z_marks})
    return depths, axes


def audit():
    p, wide, close = fit()
    windows, _ = feature_positions(p)
    depths, axes = solve_axes(wide, close)
    geometry = {}
    for i, (name, cam) in enumerate([("wide", wide), ("close", close)]):
        err = np.linalg.norm(project(cam, windows) - points[:, i], axis=1)
        geometry[name] = {"size": CONTROLS[name + "_registration"]["size"], "camera_3x4": cam.tolist(),
                          "eye_m": (-np.linalg.solve(cam[:, :3], cam[:, 3])).tolist(),
                          "K_effective_3x3": ([[567.,0.,400.],[0.,567.,975.8],[0.,0.,1.]] if name=="wide" else [[float(np.exp(p[6])),0.,1020.],[0.,float(np.exp(p[6])),681.],[0.,0.,1.]]),
                          "wall_homography_xz_to_px": homography(cam, 0).tolist(),
                          "shaft_plane_homography_xz_to_px": homography(cam, axes[0]["y_m"]).tolist(),
                          "fit_16_rms_px": np.sqrt(np.mean(err[fitted] ** 2)),
                          "holdout_4_px": {keys[j]: err[j] for j in hold},
                          "holdout_4_rms_px": np.sqrt(np.mean(err[hold] ** 2))}
    result = {"coordinate_frame": {"x": "west / viewer's right", "y": "positive into building; upper wall Y=0",
                                   "z": "up; approximate street datum"}, **geometry}
    ring = np.array(SITE["ring_wgs84"])
    east_north = (ring - ring[3]) * [111319.49 * np.cos(np.deg2rad(ring[3, 1])), 110860]
    edge = normed(east_north[4])
    offsets = east_north @ np.array([edge[1], -edge[0]])
    projection_study = []
    for focal, grade in [(510, 995), (624, 995), (567, 990), (567, 1000)]:
        _, cw, cc = fit(focal, grade)
        _, ax = solve_axes(cw, cc)
        projection_study.append({"effective_focal_px": focal, "east_street_datum_v": grade,
                                 "axis_y": ax[0]["y_m"], "east_abacus_z": ax[0]["z_and_pixels"]["top"]["z_m"],
                                 "west_axis_x": ax[-1]["x_m"]})
    candidates = {}
    close_jambs = CONTROLS["rear_grille"]["close_upper_left_jamb_px"]
    for key in ("wide_left_set_px", "wide_right_set_px"):
        observed = np.asarray(CONTROLS["rear_grille"][key])
        def measure(y):
            return project(wide, [inverse(close, uv, y[0]) for uv in close_jambs]) - observed
        r = least_squares(lambda y: measure(y).ravel(), [-2])
        candidates[key] = {"y_m": r.x[0], "three_point_rms_px": np.sqrt(np.mean(np.sum(measure(r.x) ** 2, axis=1))),
                           "distance_from_shaft_axis_m": r.x[0] - axes[0]["y_m"]}
    detail = {"scope": "Six distinguishable portico shafts at 103 Dianchi. All metric dimensions are estimates.",
              "north_edge_source": SITE["owner"], "north_edge_width_m": SITE["north_edge_length_m"],
              "north_edge_end_to_end_bearing_deg": SITE["outward_azimuth_deg"] + 90,
              "ring_vertices_inward_offsets_m": offsets.tolist(), "full_north_south_coordinate_extent_m":np.ptp(east_north[:, 1]),
              "source_ring_maximum_depth_normal_to_front_m": max(offsets),
              "width_basis_assumption": "Photo side walls treated as ends of the 28.2463 m mapped north edge. The photographs do not survey the lot or rear.",
              "front_window_axis_x_m": p[7:12].tolist(), "front_window_head_z_m": p[12:16].tolist(),
              "wide_camera_assumptions": "17mm full-frame EXIF, upright verticals, assumed east ground at v=995; strongly shifted effective principal point.",
              "photo_dates": "Wide original EXIF 2017:04:15 13:54:52. Close is the original uploaded by Fayhoo on 2015-01-19; its exposure date is unavailable.",
              "level_sources": "Historic municipal listing describes six storeys. OSM v3 is tagged eight. The two images show four rows of windows above the portico.",
              "scroll_face_y_m":p[16],"scroll_centre_z_m":p[17],
              "five_individual_shaft_depths_m": depths,"adopted_axis_y_m": axes[0]["y_m"],
              "axes": axes,"sensitivity_assumptions_not_confidence_intervals":projection_study,
              "rear_grille_repeated_bay_candidates": candidates,
              "rear_and_side_depth_limits":"The repeated transoms admit two bay correspondences. The right low side doorway is outside the close photo; its depth cannot be triangulated. Full depth and back elevations are unobserved.",
              "visibility":"Near image cuts all six bases and the far west shaft; an extra fluted return at the east wall is partly occluded. Two outer wall returns are recorded separately from the six axes.",
              "front_shaft_foot":"Base denotes the foot of the visible shaft on the masonry podium, not street grade. The first base is partly blocked by an umbrella; the second pair is partly blocked by people."}
    return result, detail


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE
    target.mkdir(parents=True, exist_ok=True)
    for filename, data in zip(["two-north-cameras.json", "north-portico-axes.json"], audit()):
        (target / filename).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
