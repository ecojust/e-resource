"""Cast short rays into real sashes, stonework, balusters and their gaps on each exported mesh."""

from pathlib import Path
import argparse, json, math, runpy

HERE = Path(__file__).resolve().parent
Scene = runpy.run_path(HERE.parent / "postal-office-v1/independent-glb-review-helpers.py")[
    "SerialScene"
]
MASONRY = "Cream washed aggregate"
TRIM = "Pale washed aggregate moulding"
SASH = "Red-brown timber sash"
SITE_HEIGHTS = [(0, 0), (5.20, 5.21), (10.19, 10.32), (14.34, 14.68), (17.25, 17.84)]


def measured_height(design):
    for (a, h), (b, k) in zip(SITE_HEIGHTS, SITE_HEIGHTS[1:]):
        if design <= b:
            return h + (k - h) * (design - a) / (b - a)
    return design + 0.59


def y_at(x, sag=1.47):
    r = (2.23**2 + sag**2) / (2 * sag)
    return -0.75 + r - sag - math.sqrt(r * r - x * x)


def test_rays():
    out = []

    def record(name, ori, aim, length, materials, limits=None):
        out.append(
            dict(
                name=name,
                origin=ori,
                direction=aim,
                length=length,
                allowed=materials,
                range_m=limits,
            )
        )

    def front(name, x, design, mat, limits=None):
        record(name, [x, -4, measured_height(design)], [0, 1, 0], 8, mat, limits)

    for floor, lo, hi, palette in [
        ("Ground", 0.94, 4.04, ["Ground blue curtain", "Ground deep reflection"]),
        ("Middle", 5.91, 8.92, ["Middle pale curtain", "Middle blue reflection"]),
    ]:
        for ix, (west, east) in enumerate([(-1.96, -1.17), (-0.91, 0.91), (1.17, 1.96)]):
            a = y_at(west)
            c = y_at(east)
            w = math.hypot(east - west, c - a)
            tangent = [(east - west) / w, (c - a) / w]
            normal = [tangent[1], -tangent[0]]

            def perpendicular(label, u, z, mat, limits):
                orig = [
                    (west + east) / 2 + tangent[0] * u + normal[0],
                    (a + c) / 2 + tangent[1] * u + normal[1],
                    measured_height(z),
                ]
                record(
                    f"{floor} sash {ix + 1} / {label}",
                    orig,
                    [-normal[0], -normal[1], 0],
                    1.47,
                    mat,
                    limits,
                )

            sill = lo + 0.025
            head = hi - 0.025
            for col in [-0.27, 0.27]:
                for row in [0.15, 0.45, 0.81]:
                    perpendicular(
                        f"curtain {col}, {row}",
                        w * col,
                        sill + (head - sill) * row,
                        palette,
                        [1.25, 1.267],
                    )
            perpendicular(
                "timber transom", w * 0.23, sill + 0.69 * (head - sill), [SASH], [1.162, 1.18]
            )
            if ix == 1:
                perpendicular(
                    "stone return before right-hand stile",
                    w / 2 - 0.071,
                    (sill + head) / 2,
                    [MASONRY],
                    [1.13, 1.16],
                )
                perpendicular("central meeting stile", 0, (sill + head) / 2, [SASH], [1.162, 1.18])
            else:
                perpendicular(
                    "outer timber stile", w / 2 - 0.071, (sill + head) / 2, [SASH], [1.162, 1.18]
                )
    for x in (-1.02, 1.02):
        for z in (1.43, 2.91, 6.55, 8.24):
            front("Stone between angled windows " + str([x, z]), x, z, [MASONRY], [1.55, 2.65])
    for x in [-1.75, -0.70, 0, 0.70, 1.75]:
        for z, mat in (
            (0.25, "Grey cement plinth"),
            (0.62, MASONRY),
            (4.49, MASONRY),
            (5.60, MASONRY),
            (9.40, MASONRY),
        ):
            front("Bow masonry or base " + str([x, z]), x, z, [mat], [1.72, 2.85])
    for i in range(13):
        x = -1.86 + 3.72 * i / 12
        front(
            "Turned balcony baluster " + str(i + 1), x, 10.19 + 0.075 + 0.25, [TRIM], [1.75, 3.46]
        )
    for i in range(12):
        x = -1.86 + 3.72 * (i + 0.5) / 12
        target = y_at(x, 1.23) + 0.21
        record(
            f"Genuine opening between balusters {i + 1} and {i + 2}",
            [x, -3.55, measured_height(10.19 + 0.075 + 0.26)],
            [0, 1, 0],
            target + 3.55,
            None,
        )
    for x in [-1.52, -0.73, 0, 0.73, 1.52]:
        front("Continuous curved handrail " + str(x), x, 10.19 + 0.75, [TRIM], [1.70, 3.14])
    for x in [-1.20, -0.43, 0.40, 1.17]:
        front("Attic transom glazing " + str(x), x, 12.82, ["Attic blue reflection"], [4.25, 4.267])
    for x in (-2.72, 2.72):
        for z in (1.42, 6.36, 8.72, 11.73):
            front("Stone side pilaster " + str([x, z]), x, z, [MASONRY], [3.81, 4.01])
        front("Lower pilaster medallion " + str(x), x, 10.25, [TRIM], [3.832, 3.86])
    front(
        "Cast 3 upper lobe", -2.67 + 0.028, 4.20 + 0.35, ["Bronze building numeral"], [3.785, 3.81]
    )
    front(
        "Cast 3 lower lobe", -2.67 + 0.031, 4.2 - 0.378, ["Bronze building numeral"], [3.785, 3.81]
    )
    front("Hospital building plaque", 2.71, 3.075, ["Grey cement plinth"], [3.831, 3.85])
    for x, z in ((-0.42, 15.85), (0.42, 15.85), (-1.40, 15.0), (1.40, 15.0)):
        front("Gable shoulder " + str([x, z]), x, z, [MASONRY], [3.955, 3.98])
    front("Stone ball finial", 0, 17.115, [TRIM], [3.82, 3.90])
    for x, z in (
        (-2.37, 15.72),
        (2.37, 15.72),
        (-1.38, 15.98),
        (1.38, 15.98),
        (-0.42, 16.80),
        (0.42, 16.80),
    ):
        record(
            "Sky over stepped gable " + str([x, z]),
            [x, -1, measured_height(z)],
            [0, 1, 0],
            1.36,
            None,
        )
    return out


def verify(path, cases):
    scene = Scene(path)
    rows = []
    for case in cases:
        h = scene.ray(case["origin"], case["direction"], case["length"])
        allow = case["allowed"]
        limit = case["range_m"]
        assert h is None if allow is None else h and h["material"] in allow, (
            case["name"],
            allow,
            h,
        )
        if limit:
            assert limit[0] <= h["distance_m"] <= limit[1], (case["name"], limit, h)
        rows.append({**case, "first_hit": h})
    return dict(asset=scene.asset, triangles=len(scene.tri), cases=rows)


if __name__ == "__main__":
    args = argparse.ArgumentParser(description=__doc__)
    for name in ("raw", "full", "lod", "output"):
        args.add_argument(name, type=Path)
    args = args.parse_args()
    rays = test_rays()
    out = {role: verify(getattr(args, role), rays) for role in ("raw", "full", "lod")}
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(len(rays), "surface and air checks per variant")
