"""Inspect the street and lane sides, inset names, post returns and working gaps in decoded GLBs."""
import argparse
import json
import math
from pathlib import Path
import runpy
import numpy as np

HERE = Path(__file__).resolve().parent
inspect = runpy.run_path(str(HERE.parent / "central-reserve-bank-changshu-front-v1/verify-export.py"))["inspect"]


def probes():
    checks = []

    def ray(label, eye, direction, length, allowed=None, limits=None):
        checks.append(dict(name=label, origin=list(eye), direction=list(direction), length=length,
                           allowed=allowed and [allowed], range_m=limits))

    def front(label, x, z, material=None, limits=None, length=1.43):
        ray(label, (x, -0.60, z), (0, 1, 0), length, material, limits)

    for x in (-1.14, -0.86, -0.51, -0.16, 0.0):
        for z in (0.08, 0.44, 1.22, 2.05, 2.96, 3.86, 4.12):
            ray("Walk in " + str((x, z)), (x, -0.38, z), (0, 1, 0), 2.9)
            ray("Walk out " + str((x, z)), (x, 2.52, z), (0, -1, 0), 2.9)
    for x in (-1.02, -0.24, 0.47, 1.05):
        for depth in (0.09, 1.49, 2.17):
            ray("Open sky between posts " + str((x, depth)), (x, depth, 3.05), (0, 0, 1), 2.8)
    for x in (-1.835, 1.835):
        side = "west" if x < 0 else "east"
        for height in (0.10, 0.34, 0.58):
            front(side + " stone pedestal " + str(height), x, height, "Grey plinth stone", (0.56, 0.59))
        for h in (1.2, 1.79, 2.37, 3.02, 3.45):
            for u in (-0.342, 0.342):
                front(side + " outer name border " + str((h, u)), x + u, h, "Light grey rubbed stone", (0.597, 0.603))
            ray(side + " back of stone " + str(h), (x, 1.18, h), (0, -1, 0), 0.62,
                "Light grey rubbed stone", (0.514, 0.526))
        for dx in (-0.085, 0, 0.085):
            ray(side + " terminal cap " + str(dx), (x + dx, 0.34, 4.35), (0, 0, -1),
                0.61, "Weathered capstone", (0.445, 0.456))
        front(side + " free air just above cap", x, 3.94)
    for x in (-4.68, -3.84, -3.20, -2.58):
        for z in (0.21, 0.44):
            front("112 wall base " + str((x, z)), x, z, "Grey plinth stone", (0.69, 0.70))
        for z in (0.83, 1.49, 1.88):
            front("112 continuous render " + str((x, z)), x, z, "Grey courtyard render", (0.737, 0.743))
        front("112 wall lower projecting moulding " + str(x), x, 2.051, "Lighter grey wall coping", (0.704, 0.71))
        front("112 wall cap " + str(x), x, 2.382, "Lighter grey wall coping", (0.676, 0.689))
        front("Between stone cap and timber " + str(x), x, 2.56)
        front("Above the pergola front " + str(x), x, 3.62)
        for k in (0, 2, 4, 6, 8):
            pitch = (3.56 - 2.71) / 9
            front("Timber batten " + str((x, k)), x, 2.71 + (k + 0.35) * pitch,
                  "Brown horizontal screen", (0.876, 0.885))
            front("Daylight through timber " + str((x, k)), x, 2.71 + (k + 0.86) * pitch)
    for side, angle in ((-1, 83), (1, 20)):
        yaw = math.radians(angle)
        sign = -side
        along = np.array((sign * math.cos(yaw), math.sin(yaw), 0))
        normal = np.array((-along[1] * sign, along[0] * sign, 0))
        hinge = np.array((side * 1.435, 0.44, 0.0))
        width = 1.42
        n = 9
        for i in (1, 2, 7, 8):
            for offset, mat in ((0, "Iron edge catching light"), (0.48, None)):
                target = hinge + along * (i + offset) * width / n + np.array([0, 0, 2.13])
                ray("Ironwork or opening " + str((side, i, offset)), target - normal * 0.12,
                    normal, 0.23, mat, (0.104, 0.114) if mat else None)
            for z in (0.65, 1.15):
                target = hinge + along * (i + 0.48) * width / n + np.array([0, 0, z])
                ray("Opaque lower iron sheet " + str((side, i, z)), target - normal * 0.14,
                    normal, 0.24, "Dark iron door panels", (0.145, 0.155))
    for x in (-5.48, 2.32):
        for z in (0.16, 1.08, 2.31, 3.15):
            front("Beside end of model " + str((x, z)), x, z)
    # Select features by pixel in the independently rendered west-name view.
    # Translating both camera and target exercises the matching inscription on the east.
    strokes = {"上": [(230, 147), (230, 179), (252, 185)],
               "海": [(207, 320), (228, 279), (254, 315)],
               "別": [(209, 424), (230, 447), (258, 458)],
               "墅": [(205, 567), (247, 580), (232, 604)]}
    grey = [(222, 566), (232, 216), (231, 262), (231, 357), (230, 499), (231, 628)]
    for x in (-1.835, 1.835):
        eye = np.array([x - 0.005, -6.3, 2.3])
        target = np.array([x, 0.02, 2.18])
        aim = target - eye
        focus = 465 * np.linalg.norm(aim) / 2.05
        aim /= np.linalg.norm(aim)
        right = np.cross(aim, [0, 0, 1]); right /= np.linalg.norm(right)
        up = np.cross(right, aim)
        for name, pixels in {**strokes, "between letters": grey}.items():
            for u, v in pixels:
                direction = aim + right * (u + .5 - 232.5) / focus + up * (372 - v - .5) / focus
                mat = "Blue-grey inset stone" if name == "between letters" else "Dark infill in name strokes"
                ray("Name field " + str((x, name, u, v)), eye, direction, 6.9, mat, (6.34, 6.57))
    return checks


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for key in ("raw", "full", "lod", "output"):
        parser.add_argument(key, type=Path)
    args = parser.parse_args()
    result = {tier: inspect(getattr(args, tier), probes()) for tier in ("raw", "full", "lod")}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n")
    failed = [(key, r["name"], r["first_hit"]) for key, v in result.items() for r in v["cases"] if not r["passed"]]
    print([(k, len(v["cases"]), v["passed"]) for k, v in result.items()])
    for item in failed[:50]: print(item)
    raise SystemExit(bool(failed))
