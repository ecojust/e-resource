"""Estimate the dimensions of the three central bays from an independently matched 16.11 m footprint."""

from pathlib import Path
import numpy as np, json
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

import argparse

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("output", type=Path)
target = parser.parse_args().output
W = 16.111300836022703
# Baseline uses four ashlar corners below the overhanging upper cornice.
ground = np.array([[282, 549], [774, 554], [754, 81], [320, 80]], float)
B = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]])


def run(focal, points):
    def project(p):
        eye = p[:3]
        rot = Rotation.from_rotvec(p[3:6]).as_matrix() @ B
        H = p[6]
        wall = np.array([[-W / 2, 0, 0], [W / 2, 0, 0], [W / 2, 0, H], [-W / 2, 0, H]])
        camera = (wall - eye) @ rot.T
        pixels = camera[:, :2] / camera[:, 2:] * focal + [525, 295.5]
        return pixels, rot

    def residual(p):
        return (project(p)[0] - points).ravel()

    p = least_squares(residual, [0, -26, 1.6, -0.21, 0, 0, 17], loss="linear").x
    pix, R = project(p)

    def recover(u, v):
        dr = R.T @ np.array([(u - 525) / focal, (v - 295.5) / focal, 1])
        q = p[:3] - p[1] / dr[1] * dr
        return list(np.round(q[[0, 2]], 4))

    return p, pix, recover


focal = np.hypot(1050, 591) * 28 / np.hypot(36, 24)
p, pix, unproject = run(focal, ground)
# Windows, masonry and balcony controls. Positions mark inside reveal edges, except named nosings.
features = {
    "central-door": [(487, 420), (564, 420), (486, 547), (563, 548)],
    "ground-left": [(329, 416), (421, 416), (324, 510), (417, 511)],
    "ground-right": [(633, 423), (726, 425), (633, 516), (728, 518)],
    "middle-left": [(344, 244), (431, 244), (338, 336), (428, 337)],
    "middle-centre": [(488, 245), (575, 245), (486, 335), (575, 336)],
    "middle-right": [(632, 245), (721, 246), (632, 340), (723, 341)],
    "upper-left": [(352, 101), (437, 101), (350, 153), (436, 153)],
    "upper-centre": [(491, 101), (577, 101), (491, 152), (577, 153)],
    "upper-right": [(633, 102), (720, 102), (633, 154), (721, 155)],
    "floor-bands": [
        (524, 552),
        (524, 512),
        (524, 416),
        (524, 376),
        (524, 339),
        (524, 244),
        (524, 218),
        (524, 189),
        (524, 174),
        (524, 154),
        (524, 101),
        (524, 81),
        (524, 65),
        (524, 39),
        (524, 25),
        (524, 10),
    ],
}
rec = {k: [unproject(*v) for v in vs] for k, vs in features.items()}
trials = []
for f in [focal * 0.94, focal, focal * 1.06]:
    for dx in [-3, 0, 3]:
        pp, rr, uu = run(f, ground + np.array([[dx, 2], [0, 2], [-dx, -2], [0, -2]]))
        trials.append(
            {
                "focal_px": f,
                "foot_pixel_shift": dx,
                "upper_course_m": pp[6],
                "sill_m": uu(486, 335)[1],
                "crown_top_m": uu(524, 10)[1],
            }
        )
d = dict(
    display=[1050, 591],
    camera="Samsung SM-G9209, 4.3 mm actual; 28 mm equivalent. Full-image diagonal used for focal estimate.",
    focal_px=focal,
    manual_corners=ground.tolist(),
    projected_corners=pix.tolist(),
    corner_rms_px=float(np.sqrt(np.mean((pix - ground) ** 2))),
    matched_width_m=W,
    camera_x_garden_y_z=p[:3].tolist(),
    height_to_ashlar_course_m=p[6],
    pixel_controls=features,
    rectified_xz_m=rec,
    sensitivity=trials,
)
target.write_text(json.dumps(d, indent=1) + "\n")
print("cam", p, "err", d["corner_rms_px"])
print(rec)
print("heights", min(t["crown_top_m"] for t in trials), max(t["crown_top_m"] for t in trials))
