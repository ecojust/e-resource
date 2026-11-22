"""Cast short rays against the delivered garden-portico meshes in metres, Z up and +Y into the house."""

import argparse, json, math, runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
inspect = runpy.run_path(
    str(HERE.parent / "central-reserve-bank-changshu-front-v1/verify-export.py")
)["inspect"]
STONE = ["Warm grey dressed stone"]
LIGHT = ["Light grey raised mouldings"]
WOOD = ["Ivory painted glazing bars"]
IRON = ["Oxidised balcony iron"]
FLOOR = ["Grey garden paving"]
GLASS = [
    "Glazing in garden shade",
    "Glazing in reflected sky",
    "Glazing in recessed bay",
    "Clear garden transom glass",
]


def probes():
    rows = []

    def ray(name, origin, direction, length, material=None, interval=None):
        rows.append(
            dict(
                name=name,
                origin=list(origin),
                direction=list(direction),
                length=length,
                allowed=material,
                range_m=interval,
            )
        )

    axes = [u * 2.9162914 for u in (-1.5, -0.5, 0.5, 1.5)]
    for i, x in enumerate(axes):
        for z, r in [
            (0.29, 0.535),
            (0.45, 0.487),
            (1.35, 0.383),
            (3.32, 0.36),
            (5.80, 0.321),
            (6.02, 0.348),
            (6.46, 0.425),
        ]:
            mats = STONE + LIGHT
            ray(
                f"Column {i + 1} front section at {z:.2f}",
                (x, -1, z),
                (0, 1, 0),
                1.42,
                mats,
                (1.3 - r - 0.04, 1.3 - r + 0.045),
            )
        for j in (0, 1, 2):
            z = (1.4, 3.2, 5.3)[j]
            ray(f"Column {i + 1} outer air {j}", (x + 0.438, -0.65, z), (0, 1, 0), 1.85)
        for sign in (-1, 1):
            ray(
                f"Column {i + 1} volute face {sign}",
                (x + sign * 0.325, -0.5, 6.248),
                (0, 1, 0),
                1.12,
                STONE + LIGHT,
                (0.453, 0.55),
            )
        for j in range(3):
            # Sample a channel bottom and its neighbouring ridge at the same shaft height.
            for part, fraction in [("filet", 0), ("channel", 0.5)]:
                a = math.tau * (j + fraction + 0.07) / 24
                ux, uy = math.cos(a), math.sin(a)
                interval = (0.314, 0.353) if part == "filet" else (0.331, 0.366)
                ray(
                    f"Column {i + 1} flute {j + 1} {part}",
                    (x + 0.720 * ux, 0.30 + 0.720 * uy, 3.22),
                    (-ux, -uy, 0),
                    0.55,
                    STONE,
                    interval,
                )
    for bay, x in enumerate((-2.8134353, 0, 2.8134353)):
        for sign in (-1, 1):
            ray(
                f"Arch {bay + 1} stone jamb {sign}",
                (x + sign * 0.675, 2.6, 1.42),
                (0, 1, 0),
                1.38,
                LIGHT,
                (1.10, 1.13),
            )
            for z in (2.40, 2.60):
                ray(
                    f"Fan {bay + 1} glazing {sign} {z}",
                    (x + sign * 0.211, 3.4, z),
                    (0, 1, 0),
                    0.6,
                    GLASS + WOOD,
                    (0.41, 0.51),
                )
            for z in (4.76, 5.72):
                ray(
                    f"Upper leaf {bay + 1} pane {sign} {z}",
                    (x + sign * 0.435, 3.4, z),
                    (0, 1, 0),
                    0.65,
                    GLASS,
                    (0.45, 0.51),
                )
            if bay == 1:
                ray(
                    f"Open central leaf {sign}",
                    (sign * 0.65, 4.20, 1.07),
                    (-sign, 0, 0),
                    0.49,
                    GLASS + WOOD,
                    (0.06, 0.29),
                )
            else:
                for z in (0.92, 1.54):
                    ray(
                        f"Closed leaf {bay + 1} pane {sign} {z}",
                        (x + sign * 0.435, 3.4, z),
                        (0, 1, 0),
                        0.64,
                        GLASS,
                        (0.45, 0.51),
                    )
        ray(f"Fan {bay + 1} crown reveal", (x, 3.4, 2.897), (0, 1, 0), 0.58, LIGHT, (0.30, 0.34))
        ray(f"Fan {bay + 1} central spoke", (x, 3.48, 2.677), (0, 1, 0), 0.51, WOOD, (0.32, 0.39))
    for bay, x in enumerate((-2.8134353, 0, 2.8134353)):
        for sign in (-1, 1):
            ray(
                f"Rear fanlight {bay + 1} diagonal bead {sign}",
                (x + sign * 0.22, 4.35, 2.60),
                (0, -1, 0),
                0.65,
                ["Dark umber door reveals"],
                (0.423, 0.448),
            )
            ray(
                f"Rear fanlight {bay + 1} adjacent pane {sign}",
                (x + sign * 0.31, 4.35, 2.60),
                (0, -1, 0),
                0.65,
                ["Clear garden transom glass"],
                (0.44, 0.48),
            )
        ray(
            f"Rear fanlight {bay + 1} central glazing bead",
            (x, 4.35, 2.67),
            (0, -1, 0),
            0.67,
            ["Dark umber door reveals"],
            (0.42, 0.46),
        )
    for x in (-0.34, -0.18, 0, 0.18, 0.34):
        for z in (0.43, 1.05, 1.69, 2.09):
            ray(f"Open central entrance {x} {z}", (x, 2.85, z), (0, 1, 0), 1.65)
    for x in (-2.91, 0, 2.91):
        for z in (0.85, 1.65, 3.31):
            ray(f"Porch approach {x} {z}", (x, -1.22, z), (0, 1, 0), 3.35)
    for z in (0.70, 1.25, 2.72, 3.55):
        ray(f"Cross passage behind columns {z}", (-4.78, 1.55, z), (1, 0, 0), 9.56)
    for i, (y, z) in enumerate([(-0.81, 0.085), (-0.66, 0.17), (-0.49, 0.255)]):
        ray(
            f"Central curved step {i + 1}",
            (0, y, 0.70),
            (0, 0, -1),
            0.8,
            FLOOR,
            (0.70 - z - 0.004, 0.70 - z + 0.004),
        )
    for sign in (-1, 1):
        for j, (x, y, z) in enumerate(
            [(5.43, 0.50, 0.085), (5.35, 0.50, 0.17), (5.25, 0.50, 0.255)]
        ):
            ray(
                f"Rounded stair return {sign} {j + 1}",
                (sign * x, y, 0.72),
                (0, 0, -1),
                0.85,
                FLOOR,
                (0.72 - z - 0.004, 0.72 - z + 0.004),
            )
    for x in (-1.5, 0, 1.5):
        ray(f"Balcony slab from below {x}", (x, 2.58, 3.15), (0, 0, 1), 1.20, STONE, (0.85, 0.89))
        ray(f"Balcony coping from front {x}", (x, 1.81, 5.225), (0, 1, 0), 0.64, IRON, (0.32, 0.37))
    for x in (-4.37, 4.37):
        ray(f"Open balcony splay above slab {x}", (x, 1.9, 4.79), (0, 1, 0), 0.56)
    for i in range(3):
        left = -5.04 + 3.36 * i
        for k in range(1, 9):
            x = left + 3.36 * k / 9
            ray(
                f"Parapet bay {i + 1} baluster {k}",
                (x, -0.7, 8.287),
                (0, 1, 0),
                0.91,
                STONE,
                (0.565, 0.612),
            )
            if k < 8:
                ray(
                    f"Parapet bay {i + 1} opening {k}",
                    (x + 3.36 / 18, -0.7, 8.287),
                    (0, 1, 0),
                    1.01,
                )
    for i in range(8):
        x = -4.28 + 1.08 * i + 0.12
        y = 1.24
        ray(f"Open ceiling light {i + 1}", (x, y, 6.88), (0, 0, 1), 1.15)
        ray(
            f"Ceiling light cross {i + 1}",
            (-4.28 + 1.08 * i + 0.445, 1.245, 6.88),
            (0, 0, 1),
            1.12,
            IRON,
            (0.88, 0.95),
        )
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for n in ("raw", "full", "lod", "output"):
        parser.add_argument(n, type=Path)
    args = parser.parse_args()
    results = {k: inspect(getattr(args, k), probes()) for k in ("raw", "full", "lod")}
    args.output.write_text(json.dumps(results, ensure_ascii=False, indent=1) + "\n")
    failures = [
        (k, v["name"], v["first_hit"])
        for k, d in results.items()
        for v in d["cases"]
        if not v["passed"]
    ]
    print({k: [len(v["cases"]), v["passed"]] for k, v in results.items()})
    for item in failures[:30]:
        print(item)
    raise SystemExit(int(bool(failures)))
