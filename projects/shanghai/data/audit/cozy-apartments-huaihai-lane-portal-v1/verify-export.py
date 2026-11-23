"""Trace independent solid, passage, grille, lettering, pane and masonry controls through the exported geometry."""

import argparse
import json
import math
from pathlib import Path
import runpy
import numpy as np

HERE = Path(__file__).resolve().parent
inspect = runpy.run_path(
    str(HERE.parent / "central-reserve-bank-changshu-front-v1/verify-export.py")
)["inspect"]
stone = ["Buff-grey cut stone", "Cool grey alternate stone", "Pale stone with ochre cast"]
iron = ["Blackened iron gate"]
field = ["Grey-green inset inscription field"]
brick = ["Weathered red face brick", "Brown red face brick", "Muted terracotta face brick"]


def probes():
    cases = []

    def ray(label, origin, direction, length, material=None, span=None):
        cases.append(
            dict(
                name=label,
                origin=list(origin),
                direction=list(direction),
                length=length,
                allowed=material,
                range_m=span,
            )
        )

    def front(label, x, z, material, span):
        ray(label, (x, -0.7, z), (0, 1, 0), 1.6, material, span)

    for x in (-0.74, -0.37, 0, 0.38, 0.72):
        for z in (0.18, 0.82, 1.58, 2.26, 2.82, 3.10):
            ray("Street to inner lane " + str((x, z)), (x, -0.3, z), (0, 1, 0), 4.46)
            ray("Return to street " + str((x, z)), (x, 4.14, z), (0, -1, 0), 4.44)
    for x in (-2.55, 2.15):
        for z in (0.15, 0.48, 0.79, 1.13, 1.46, 1.79, 2.10, 2.43, 2.77, 3.06):
            front("Continuous dressed jamb " + str((x, z)), x, z, stone, (0.719, 0.743))
        front("Negative space beside jamb", x + (-0.23 if x < 0 else 0.34), 1.52, None, None)
    for x in (-1.5, -0.5, 0, 0.6, 1.54):
        front("Continuous lintel " + str(x), x, 3.38, ["Dressed stone coping"], (0.66, 0.69))
        front("Upper rail " + str(x), x, 4.82, stone, (0.64, 0.68))
        front("Cap edge " + str(x), x, 4.956, stone, (0.60, 0.65))
    for z, mat in ((0.51, ["Charcoal green passage dado"]), (1.78, ["Off-white passage plaster"])):
        for y in (2.85, 3.90):
            for side in (-1, 1):
                ray(
                    "Passage side " + str((side, y, z)),
                    (side * 1.45, y, z),
                    (side, 0, 0),
                    0.50,
                    mat,
                    (0.34, 0.37),
                )
    for y in (0.51, 1.85, 2.35, 3.23, 4.10):
        ray(
            "Threshold paving " + str(y),
            (0.22, y, 0.63),
            (0, 0, -1),
            0.72,
            ["Grey concrete walking surface"],
            (0.59, 0.62),
        )
        ray(
            "Passage soffit " + str(y),
            (-0.12, y, 2.81),
            (0, 0, 1),
            0.55,
            ["Light grey passage ceiling"],
            (0.35, 0.45),
        )
    for y in (1.782, 3.262):
        ray(
            "Under cross beam " + str(y),
            (0.51, y, 2.95),
            (0, 0, 1),
            0.4,
            ["Light grey passage ceiling"],
            (0.20, 0.23),
        )
    for side, yaw in ((-1, 74), (1, 60)):
        theta = math.radians(yaw)
        into = np.array([-side * math.cos(theta), math.sin(theta), 0.0])
        normal = np.array([side * math.sin(theta), math.cos(theta), 0.0])
        hinge = np.array([side * 1.757, 0.47, 1.13])
        pitch = 1.75 / 13
        for k in (2, 4, 6, 8, 10, 12):
            for frac, mat in ((0, iron), (0.5, None)):
                target = hinge + into * (k + frac) * pitch
                ray(
                    "Gate bar or space " + str((side, k, frac)),
                    target - normal * 0.11,
                    normal,
                    0.21,
                    mat,
                    (0.095, 0.11) if mat else None,
                )
    for x in (-0.92, 0.772):
        for sign in (-1, 1):
            for z in (5.18, 5.73, 6.27):
                front(
                    "Upper casement glazing " + str((x, sign, z)),
                    x + sign * 0.21,
                    z,
                    ["Dark sage window reflections"],
                    (1.10, 1.13),
                )
            front(
                "Upper transom glazing " + str((x, sign)),
                x + sign * 0.21,
                6.66,
                ["Upper window shaded glass"],
                (1.10, 1.13),
            )
        for z in (5.44, 6.13):
            front("Casement meeting rail " + str((x, z)), x, z, ["Dark grey joinery"], (1.06, 1.09))
        front("Lower frame " + str(x), x + 0.103, 5.065, ["Dark grey joinery"], (1.045, 1.065))
        front(
            "Stone head " + str(x),
            x - 0.09,
            6.91,
            ["Weathered dark stone window sill"],
            (0.918, 0.95),
        )
    for x in (-0.105, -0.020):
        for z in (5.15, 5.96, 6.61):
            front(
                "Pipes between windows " + str((x, z)),
                x,
                z,
                ["Dull galvanized pipe"],
                (0.931, 0.95),
            )
    for x, z in (
        (-2.27, 5.25),
        (-2.02, 5.69),
        (-1.72, 6.64),
        (1.95, 5.89),
        (1.85, 6.33),
        (1.75, 7.12),
        (0.17, 6.12),
    ):
        front("Bonded brick face " + str((x, z)), x, z, brick, (0.99, 1.015))
    for x in (-2.6, -1.55, -0.51, 0.48, 1.64, 2.32):
        front("Above limit of observed wall " + str(x), x, 7.26, None, None)
    # Pixel positions manually selected from the inspected second engraving rendering.
    # Hardware-independent measurements use the published camera and the actual rays to these pixels.
    eye = np.array([-0.24, -5.85, 4.38])
    target = np.array([-0.055, 0.015, 4.10])
    aim = target - eye
    distance = np.linalg.norm(aim)
    aim /= distance
    right = np.cross(aim, [0, 0, 1])
    right /= np.linalg.norm(right)
    up = np.cross(right, aim)
    focus = 650 * distance / 5.38
    for label, pixels, mat in (
        ("康 strokes", [(192, 353), (214, 364), (226, 372)], ["Oxide red name characters"]),
        ("綏 strokes", [(279, 354), (307, 364), (304, 376)], ["Oxide red name characters"]),
        ("公 strokes", [(367, 344), (371, 365), (380, 380)], ["Oxide red name characters"]),
        ("寓 strokes", [(444, 359), (456, 364), (474, 378)], ["Oxide red name characters"]),
        ("Exposed name field", [(252, 353), (334, 361), (416, 364), (375, 351), (450, 357)], field),
    ):
        for x, y in pixels:
            v = aim + right * (x + 0.5 - 325) / focus + up * (357.5 - y - 0.5) / focus
            ray(label + " " + str((x, y)), eye, v, 7.0, mat, (5.78, 6.21))
    return cases


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for key in ("raw", "full", "lod", "output"):
        parser.add_argument(key, type=Path)
    args = parser.parse_args()
    data = {role: inspect(getattr(args, role), probes()) for role in ("raw", "full", "lod")}
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    failed = [
        (role, p["name"], p["first_hit"])
        for role, v in data.items()
        for p in v["cases"]
        if not p["passed"]
    ]
    print({k: (len(v["cases"]), v["passed"]) for k, v in data.items()})
    for item in failed[:85]:
        print(item)
    raise SystemExit(bool(failed))
