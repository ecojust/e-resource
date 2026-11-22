"""Cast independent rays through the walk-through opening and into each separately modeled gate element."""

from pathlib import Path
import argparse
import json
import math
import runpy

HERE = Path(__file__).resolve().parent
reader = HERE.parent / "postal-office-v1/independent-glb-review-helpers.py"
Scene = runpy.run_path(reader)["SerialScene"]
PIER_BRICK = ["Umber brick", "Russet brick", "Smoked brick", "Warm lime joints"]
STONE = ["Limestone coloured render", "Stone nosing", "Recessed rendered panel"]
IRON = ["Graphite wrought iron"]


def checks():
    rows = []

    def ray(label, origin, direction, length, allow, window=None):
        rows.append(
            dict(
                name=label,
                origin=origin,
                direction=direction,
                length=length,
                allowed=allow,
                distance_limits_m=window,
            )
        )

    def front(label, x, z, allow, window=None):
        ray(label, [x, -2, z], [0, 1, 0], 4.6, allow, window)

    # Survey dimensions in metres, measured on the street plane. The aperture and
    # the left/right stop plates remain independent of the rear residential building.
    for sign, name in [(-1, "South pier at left"), (1, "North pier at right")]:
        x = 2.245 * sign
        for i, z in enumerate([0.26, 0.39]):
            front(name + " plinth " + str(i), x, z, ["Grey stippled plinth"], [1.88, 2.01])
        for i, z in enumerate([0.72, 1.12, 1.64, 1.95, 2.29, 3.18]):
            front(name + " brick " + str(i), x + 0.24 * sign, z, PIER_BRICK, [1.97, 2.03])
        for i, z in enumerate([3.32, 3.50, 3.76]):
            front(name + " impost " + str(i), x, z, STONE, [1.87, 2.01])
    for x in [-1.80, -1.44, -1.05, -0.72, 0, 0.72, 1.05, 1.44, 1.80]:
        inner = 3.86 + 1.83 * math.sqrt(max(0, 1 - (x / 1.81) ** 2))
        outer = 3.86 + 2.61 * math.sqrt(max(0, 1 - (x / 2.697) ** 2))
        front("Rendered masonry arch " + str(x), x, (inner + outer) / 2, STONE, [1.90, 2.02])
        if abs(x) > 1.78:
            ray(
                "Projecting impost under arch " + str(x),
                [x, 0.42, 3.822],
                [0, 0, 1],
                0.18,
                STONE,
                [0.025, 0.053],
            )
        else:
            ray(
                "Soffit above " + str(x),
                [x, 0.42, inner - 0.23],
                [0, 0, 1],
                0.49,
                STONE,
                [0.20, 0.27],
            )
    for name, x, z in [
        ("Bronze activity centre plaque", -2.246, 2.93),
        ("Bronze 522 address plaque", -2.246, 2.56),
        ("Pale heritage plaque", 2.246, 2.67),
    ]:
        for i, (dx, dz) in enumerate([(-0.1, -0.035), (0, 0.012), (0.09, 0.032)]):
            front(name + " lettering " + str(i), x + dx, z + dz, [name], [1.94, 1.97])
    for x in [-1.58, -0.89, -0.54, 0, 0.55, 0.93, 1.56]:
        front("Fan horizontal tie " + str(x), x, 3.86, IRON, [2.21, 2.29])
    for deg in (45, 90, 135):
        theta = math.radians(deg)
        for length in [0.28, 0.57, 0.80]:
            x = 1.81 * math.cos(theta) * length
            z = 3.86 + 1.83 * math.sin(theta) * length
            front(f"Main spoke {deg} at {length}", x, z, IRON, [2.20, 2.3])
    for t in [0.19, 0.31, 0.50, 0.69, 0.81]:
        front(
            "Semicircular hub " + str(t),
            0.282 * math.cos(math.pi * t),
            3.86 + 0.277 * math.sin(math.pi * t),
            IRON,
            [2.20, 2.30],
        )
    for sign, deg, label in [(-1, 82, "open leaf"), (1, 7, "near-closed leaf")]:
        a = math.radians(deg)
        tangent = (-sign * math.cos(a), math.sin(a))
        normal = (tangent[1], -tangent[0])
        for frac in [2 / 12, 3 / 12, 5 / 12, 7 / 12, 9 / 12, 11 / 12]:
            u = 1.738 * frac
            x = sign * 1.763 + tangent[0] * u
            y = 0.503 + tangent[1] * u
            for z in [1.2, 2.04]:
                ray(
                    label + f" vertical {frac:.2f} at {z}",
                    [x + 0.36 * normal[0], y + 0.36 * normal[1], z],
                    [-normal[0], -normal[1], 0],
                    0.7,
                    IRON,
                    [0.33, 0.38],
                )
        for frac in [0.18, 0.42, 0.69, 0.83]:
            u = 1.738 * frac
            x = sign * 1.763 + tangent[0] * u
            y = 0.503 + tangent[1] * u
            ray(
                label + f" lower rail {frac}",
                [x + 0.36 * normal[0], y + 0.36 * normal[1], 0.518],
                [-normal[0], -normal[1], 0],
                0.7,
                IRON,
                [0.32, 0.39],
            )
    for x in [-1.13, -0.91, -0.65, -0.42, -0.18]:
        for z in [0.25, 1.1, 1.85, 2.5]:
            front("Open walk-through " + str([x, z]), x, z, None)
    for x in [-2.30, -1.55, -0.80, 0.80, 1.55, 2.30]:
        z = 3.86 + 2.61 * math.sqrt(1 - (x / 2.698) ** 2) + 0.14
        front("Sky above coping " + str(x), x, z, None)
    ray("Circular slow sign black rim", [-1.43, 0.402, 2.535], [-1, 0, 0], 0.60, IRON, [0.34, 0.39])
    ray(
        "Circular slow sign ochre field",
        [-1.43, 0.404, 2.44],
        [-1, 0, 0],
        0.60,
        ["Ochre yellow sign enamel"],
        [0.34, 0.39],
    )
    ray(
        "Open leaf seen before lower character stroke",
        [-1.43, 0.471, 2.116],
        [-1, 0, 0],
        0.6,
        IRON,
        [0.299, 0.319],
    )
    for i, (u, v, material) in enumerate(
        [
            (-0.24, 0.30, IRON),
            (0.20, -0.32, IRON),
            (0.18, -0.10, ["Ochre yellow sign enamel"]),
            (-0.20, -0.20, IRON),
            (-0.55, 0.12, ["Ochre yellow sign enamel"]),
            (0.64, -0.10, ["Ochre yellow sign enamel"]),
        ]
    ):
        ray(
            "Photographed slow character or ochre field " + str(i),
            [-1.76, 0.402 + u * 0.344, 2.222 + v * 0.332],
            [-1, 0, 0],
            0.10,
            material,
            [0.011, 0.041],
        )
    return rows


def review(asset, cases):
    scene = Scene(asset)
    result = []
    for c in cases:
        h = scene.ray(c["origin"], c["direction"], c["length"])
        assert h is None if c["allowed"] is None else h and h["material"] in c["allowed"], (
            c["name"],
            c["allowed"],
            h,
        )
        w = c["distance_limits_m"]
        if w:
            assert w[0] <= h["distance_m"] <= w[1], (c["name"], w, h)
        result.append({**c, "hit": h})
    return dict(asset=scene.asset, triangles=len(scene.tri), cases=result)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("raw", "full", "lod", "output"):
        p.add_argument(name, type=Path)
    args = p.parse_args()
    cases = checks()
    out = {role: review(getattr(args, role), cases) for role in ("raw", "full", "lod")}
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(len(cases), "material, depth and empty-space checks per variant")
