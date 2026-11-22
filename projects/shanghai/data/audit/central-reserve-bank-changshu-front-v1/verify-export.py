"""Sample actual openings, stone posts, window glass, frame positions, steps and roof limits."""

from pathlib import Path
import argparse, json, runpy, math

HERE = Path(__file__).resolve().parent
Scene = runpy.run_path(HERE.parent / "postal-office-v1/independent-glb-review-helpers.py")[
    "SerialScene"
]
STONE = ["Portal cut-stone trim", "Pale upper-storey ashlar"]
GLASS = [
    "Ground brown curtain",
    "Pale drape",
    "Reflected winter branches",
    "Upper grey curtain",
    "Upper brown curtain",
]
BAYS = [-5.14, 0, 5.14]


def cases():
    probes = []

    def check(name, origin, direction, length, materials=None, interval=None):
        probes.append(
            dict(
                name=name,
                origin=origin,
                direction=direction,
                length=length,
                allowed=materials,
                range_m=interval,
            )
        )

    for upper in (False, True):
        for index, x in enumerate(BAYS):
            central = index == 1
            caption = (
                ("upper" if upper else "middle")
                + " "
                + ("central splay" if central else ("left" if index == 0 else "right"))
            )
            nose = (0.80 if upper else 1.07) if central else 0.37
            flat = ((1.95 if upper else 2.05) - 0.49) if central else 1.71
            n = 9 if central else 11
            bot = (12.96 if upper else 5.79) + 0.42
            top = (13.86 if upper else 7.03) + 0.42
            h = (bot + (0.27 if upper else 0.34) + top - (0.21 if upper else 0.25)) / 2
            xs = [x - flat + 0.20 + (2 * flat - 0.40) * (k + 0.5) / n for k in range(n)]
            for k, px in enumerate(xs):
                check(
                    f"{caption} stone spindle {k + 1}",
                    [px, -2, h],
                    [0, 1, 0],
                    2 - nose + 0.12,
                    STONE,
                    [2 - nose - 0.13, 2 - nose + 0.01],
                )
            for k, (p, q) in enumerate(zip(xs, xs[1:])):
                check(
                    f"{caption} open gap {k + 1}", [(p + q) / 2, -2, h], [0, 1, 0], 2 - nose + 0.13
                )
            for px in [x - 0.57, x + 0.57]:
                check(
                    caption + " continuous coping " + str(px),
                    [px, -2, top - 0.036],
                    [0, 1, 0],
                    2 - nose + 0.14,
                    ["Pale dressed ledge"],
                )
            if central:
                half = 1.95 if upper else 2.05
                for sign in [-1, 1]:
                    check(
                        caption + " angled side spindle " + str(sign),
                        [x + sign * (flat + half) / 2, -2, h],
                        [0, 1, 0],
                        2,
                        STONE,
                    )
    for floor, (sill, head) in enumerate([(1.17, 4.29), (6.05, 10.40), (13.15, 15.89)]):
        for i, x in enumerate(BAYS):
            if (floor, i) == (0, 1):
                continue
            z = sill + 0.42 + 0.87 * (head - sill)
            for xx in [x - 1.16, x + 0.40, x + 1.12]:
                check(
                    f"level {floor + 1} sash {i + 1} glass {xx}",
                    [xx, -1.72, z],
                    [0, 1, 0],
                    2.2,
                    GLASS,
                    [1.979, 1.987],
                )
            rail = sill + 0.42 + (head - sill) * (0.73 if floor == 2 else 0.70)
            check(
                f"level {floor + 1} sash {i + 1} transom",
                [x + 0.42, -1.72, rail],
                [0, 1, 0],
                2.2,
                ["Brown window joinery"],
                [1.815, 1.825],
            )
            check(
                f"level {floor + 1} sash {i + 1} meeting stile",
                [x - 0.83571, -1.72, z],
                [0, 1, 0],
                2.2,
                ["Brown window joinery"],
                [1.815, 1.825],
            )
    for k, (yy, zz) in enumerate([(-2.86, 0.14), (-2.48, 0.28), (-2.08, 0.42)]):
        check(
            "individual entrance step " + str(k + 1),
            [0.17, yy, 1.1],
            [0, 0, -1],
            1.1,
            ["Grey granite basement", "Pale dressed ledge"],
            [1.1 - zz - 0.004, 1.1 - zz + 0.004],
        )
    for px in [-0.54, 0, 0.54]:
        check("central open threshold at " + str(px), [px, -1, 1.11], [0, 1, 0], 2.18)
        check(
            "shaded vestibule limit at " + str(px),
            [px, -1, 2.62],
            [0, 1, 0],
            4,
            ["Shadow inside open entry"],
            [3.775, 3.786],
        )
    for course in [3.55, 8.51, 15.98]:
        check(
            "solid west return " + str(course),
            [-9.4, 2.06, course],
            [1, 0, 0],
            2,
            ["Warm grey cut stone", "Pale upper-storey ashlar", "Silver-grey stone return"],
        )
        check(
            "east return glass " + str(course),
            [9.4, 2.93, course],
            [-1, 0, 0],
            2.3,
            GLASS,
            [1.604, 1.611],
        )
    check(
        "east ground return main mullion",
        [9.4, 2.62, 3.55],
        [-1, 0, 0],
        2.30,
        ["Brown window joinery"],
        [1.440, 1.449],
    )
    for x in [-7.1, -3.70, 3.70, 7.1]:
        check("open sky past attic " + str(x), [x, -2.02, 19.68], [0, 1, 0], 4.3)
        check(
            "upper square coping " + str(x),
            [x, -0.60, 19.66],
            [0, 0, -1],
            1.50,
            ["Pale dressed ledge"],
            [1.18, 1.20],
        )
    check(
        "highest central short parapet",
        [0.11, 1.32, 21.20],
        [0, 0, -1],
        1.56,
        ["Pale upper-storey ashlar"],
        [0.746, 0.754],
    )
    for side in (-1, 1):
        check(
            "closed shadow in vestibule side " + str(side),
            [0, 2.07, 2.19],
            [side, 0, 0],
            1.43,
            ["Shadow inside open entry"],
            [1.260, 1.271],
        )
    check(
        "closed underside behind open door",
        [0, 2.10, 1.35],
        [0, 0, 1],
        3.55,
        ["Shadow inside open entry"],
        [3.165, 3.175],
    )
    for x in BAYS:
        check(
            "recessed glass behind lower stone rail " + str(x),
            [x + 1.12, -0.14, 6.76],
            [0, 1, 0],
            0.50,
            GLASS,
            [0.399, 0.407],
        )
    for x in (-5.14, 5.14):
        check(
            "thick projecting ground sill " + str(x),
            [x + 0.43, -0.9, 1.45],
            [0, 1, 0],
            1.05,
            ["Pale dressed ledge"],
            [0.689, 0.699],
        )
    return probes


def inspect(path, probe_list):
    scene = Scene(path)
    results = []
    for p in probe_list:
        hit = scene.ray(p["origin"], p["direction"], p["length"])
        allowed = p["allowed"]
        limit = p["range_m"]
        ok = (hit is None) if allowed is None else (bool(hit) and hit["material"] in allowed)
        if limit and hit:
            ok = ok and limit[0] <= hit["distance_m"] <= limit[1]
        results.append({**p, "first_hit": hit, "passed": ok})
    return dict(
        asset=scene.asset,
        triangles=len(scene.tri),
        passed=all(x["passed"] for x in results),
        cases=results,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("full", type=Path)
    parser.add_argument("lod", type=Path)
    parser.add_argument("output", type=Path)
    options = parser.parse_args()
    states = {role: inspect(getattr(options, role), cases()) for role in ("raw", "full", "lod")}
    options.output.write_text(json.dumps(states, ensure_ascii=False, indent=1) + "\n")
    cases_failed = {
        k: [x["name"] for x in v["cases"] if not x["passed"]] for k, v in states.items()
    }
    print({k: (len(v["cases"]), len(cases_failed[k])) for k, v in states.items()}, flush=True)
    if any(cases_failed.values()):
        print(cases_failed)
        raise SystemExit(1)
