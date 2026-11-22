"""Fit the courtyard colonnade in three photographs using the 22.36 m width of its host facade."""

from pathlib import Path
import json, sys
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

width = 22.359219696947143
views = [
    dict(
        name="Earlier front photograph, reproduced in 2024",
        size=[700, 467],
        focal=510,
        foot=[(124, 420), (271, 427), (435, 426), (583, 417)],
        capital=[(183, 153), (292, 152), (409, 151), (519, 151)],
        arch=[(251, 315), (354, 313), (455, 314)],
        threshold=[(247, 410), (354, 412), (455, 409)],
    ),
    dict(
        name="Shuishi garden oblique",
        size=[1150, 539],
        focal=850,
        foot=[(359, 432), (489, 426), (595, 418), (678, 413)],
        capital=[(357, 106), (487, 137), (596, 164), (681, 184)],
        arch=[(378, 304), (460, 307), (553, 315)],
        threshold=[(376, 418), (459, 412), (551, 407)],
        east=[(770, 401)],
    ),
    dict(
        name="Shuishi view across the lawn",
        size=[1150, 539],
        focal=1100,
        foot=[(512, 402), (563, 400), (617, 397), (668, 396)],
        arch=[(551, 352), (596, 353), (646, 350)],
        threshold=[(550, 401), (596, 398), (646, 397)],
        west=[(400, 405)],
        east=[(794, 396)],
    ),
]
basis = np.array([[1.0, 0, 0], [0, 0, -1], [0, 1, 0]])


def controls(view, dims):
    pitch, height, depth, crown, doors, wing = dims
    stations = np.array([-1.5, -0.5, 0.5, 1.5]) * pitch
    locations = {
        "foot": [(x, 0, 0.22) for x in stations],
        "capital": [(x, 0, height) for x in stations],
        "arch": [(x, depth, crown) for x in [-doors, 0, doors]],
        "threshold": [(x, depth, 0.22) for x in [-doors, 0, doors]],
        "west": [(-width / 2, wing, 0)],
        "east": [(width / 2, wing, 0)],
    }
    sigma = {
        "foot": [3, 2, 2, 3],
        "capital": [5, 3, 3, 4],
        "arch": [5, 3, 4],
        "threshold": [5, 3, 4],
        "west": [11],
        "east": [7],
    }
    return [
        (key, p, t, s)
        for key, rows in locations.items()
        if key in view
        for p, t, s in zip(rows, view[key], sigma[key])
    ]


def project(world, cam, view):
    eye = cam[:3]
    R = Rotation.from_rotvec(cam[3:6]).as_matrix() @ basis
    v = (world - eye) @ R.T
    return v[:, :2] / v[:, 2:] * np.exp(cam[6]) + [view["size"][0] / 2, cam[7]]


def measure(x, describe=False):
    dims = x[:6]
    out = []
    stats = []
    for i, view in enumerate(views):
        cam = x[6 + 8 * i : 14 + 8 * i]
        rows = controls(view, dims)
        xyz = np.array([r[1] for r in rows])
        observed = np.array([r[2] for r in rows])
        error = project(xyz, cam, view) - observed
        out.extend((error / np.array([r[3] for r in rows])[:, None]).ravel())
        stats.append(
            dict(
                name=view["name"],
                count=len(rows),
                rms_px=float(np.sqrt(np.mean(np.sum(error**2, axis=1)))),
                max_px=float(np.linalg.norm(error, axis=1).max()),
                camera_eye_m=cam[:3].tolist(),
                focal_px=float(np.exp(cam[6])),
                principal_y_px=float(cam[7]),
                errors=[[r[0], *np.round(e, 2)] for r, e in zip(rows, error)],
            )
        )
        out.extend(
            [
                (cam[2] - 1.6) / 0.45,
                (cam[6] - np.log(view["focal"])) / 0.28,
                (cam[7] - view["size"][1] / 2) / (view["size"][1] * 0.22),
            ]
        )
    out.extend([(dims[2] - 3) / 1.5, (dims[5] - 1) / 1.2])
    return stats if describe else out


seed = [2.9, 7.35, 3.1, 3.50, 2.85, 1.1]
for view, (x, y, z, pitch, yaw) in zip(
    views, [(0, -10, 1.2, -0.30, 0), (-9, -15, 1.45, 0, -0.40), (-2, -57, 1.5, 0, -0.04)]
):
    seed.extend([x, y, z, pitch, yaw, 0, np.log(view["focal"]), view["size"][1] / 2])
lower = [1.8, 4.6, 1.4, 2.3, 1.8, -0.5]
upper = [5, 12, 6.8, 5.8, 4.9, 4.0]
for j in views:
    lower.extend(
        [-55, -125, 0.3, -1.0, -1.35, -0.32, np.log(j["focal"] * 0.4), -j["size"][1] * 0.12]
    )
    upper.extend([55, -3, 3.4, 1.0, 1.35, 0.32, np.log(j["focal"] * 2.9), j["size"][1] * 1.2])
linear = least_squares(measure, seed, bounds=(lower, upper), x_scale="jac", max_nfev=400)
fit = least_squares(
    measure,
    linear.x,
    bounds=(lower, upper),
    x_scale="jac",
    loss="soft_l1",
    f_scale=1.2,
    max_nfev=550,
)
assert fit.success, fit.message
stats = measure(fit.x, True)
dims = dict(
    zip(
        [
            "column_pitch",
            "volute_axis_height",
            "column_to_doors",
            "arch_crown_height",
            "door_pitch",
            "wing_setback",
        ],
        fit.x[:6].tolist(),
    )
)
Path(sys.argv[1]).write_text(
    json.dumps(
        dict(width_m=width, parameters=dims, controls=views, checks=stats, fit=fit.x.tolist()),
        ensure_ascii=False,
        indent=2,
    )
    + "\n"
)
print(dims, [round(v["rms_px"], 2) for v in stats], flush=True)
