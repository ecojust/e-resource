"""The projecting southwest bay at 805 North Shaanxi Road. Local Y points into the house."""

import math
from pathlib import Path
from shapely.geometry import box, Polygon, LineString
from shapely.ops import unary_union
from photo_architecture import Facade
from glazing import PANES

HERE = Path(__file__).resolve().parent
PLASTER = "Cream washed aggregate"
EDGE = "Pale washed aggregate moulding"
SHADOW = "Ochre recessed aggregate"
BASE = "Grey cement plinth"
WOOD = "Red-brown timber sash"
BRASS = "Bronze building numeral"
METAL = "Oxidised bronze edge"
ROOF = "Weathered red clay tile"
TEXTILE = list(PANES)


def finish(rgb, rough=0.79, metal=0):
    return {
        "color": [
            (v / 255 / 12.92 if v / 255 <= 0.04045 else ((v / 255 + 0.055) / 1.055) ** 2.4)
            for v in rgb
        ],
        "roughness": rough,
        "metallic": metal,
    }


PALETTE = {
    PLASTER: finish((207, 196, 161)),
    EDGE: finish((221, 209, 173)),
    SHADOW: finish((163, 149, 122)),
    BASE: finish((133, 127, 122)),
    WOOD: finish((84, 44, 35), 0.49),
    BRASS: finish((177, 137, 67), 0.42, 0.57),
    METAL: finish((98, 83, 66), 0.64, 0.31),
    ROOF: finish((130, 80, 61), 0.80),
}
for name in TEXTILE:
    PALETTE[name] = {
        "color": [1, 1, 1],
        "roughness": 0.45,
        "metallic": 0.08,
        "texture": str(HERE / "curtain-samples.png"),
    }

# These dimensions describe the owned six-and-a-half-metre bay. The outline and
# the separate hospital wings are recorded in measurements, outside this file.
HALF = 3.24
BOW = 2.23
EDGE_Y = -0.75
NOSE = 1.47
BACK = 2.72
HEADS = [("Street storey", 0.94, 4.04), ("Middle storey", 5.91, 8.92)]
BALCONY = 10.19
TOP_SILL = 10.20
TOP_HEAD = 13.24


def front_y(x, sag=NOSE):
    radius = (BOW**2 + sag**2) / (2 * sag)
    return EDGE_Y + radius - sag - math.sqrt(radius**2 - min(abs(x), BOW) ** 2)


def path(count, width=BOW, sag=NOSE):
    return [
        (x, front_y(x, sag)) for x in [-width + 2 * width * i / count for i in range(count + 1)]
    ]


def horizontal(b, polygon, lo, hi, material, name):
    # u = X, v = Y, thickness = Z.
    b.prism(polygon, lo, hi, lambda x, y, z: (x, y, z), material, name)


def fan(b, lo, hi, material, name, segments, lip=0):
    points = [(x, y - lip) for x, y in path(segments)]
    horizontal(b, Polygon([*points, (BOW, 0.43), (-BOW, 0.43)]), lo, hi, material, name)


def bow_trim(b, z, profile, material, name, segments, sag=NOSE):
    v = []
    for x, y in path(segments, sag=sag):
        radius = (BOW**2 + sag**2) / (2 * sag)
        normal = (x / math.sqrt(radius**2 - x**2), -1)
        length = math.hypot(*normal)
        for d, h in profile:
            v.append((x + d * normal[0] / length, y + d * normal[1] / length, z + h))
    n = len(profile)
    faces = []
    for j in range(segments):
        for k in range(n):
            p = j * n + k
            q = j * n + (k + 1) % n
            faces.append((p, q, q + n, p + n))
    faces.extend([tuple(reversed(range(n))), tuple(range(n * segments, n * (segments + 1)))])
    b.add(v, faces, material, name)


def plane(b, x0, y0, x1, y1, name):
    return Facade(b, (x0, y0), (x1, y1), name)


def glass_pane(f, u0, u1, z0, z1, mat, name, depth):
    b = f.builder
    vertices = [
        tuple(f.point(u0, z0, depth)),
        tuple(f.point(u1, z0, depth)),
        tuple(f.point(u1, z1, depth)),
        tuple(f.point(u0, z1, depth)),
    ]
    b.add(vertices, [(0, 1, 2), (0, 2, 3)], mat, f.label + "/" + name)
    index = TEXTILE.index(mat)
    left = (index * 64 + 1.5) / 320
    right = (index * 64 + 62.5) / 320
    b.parts[-1]["texcoords"] = [(left, 0.977), (right, 0.977), (right, 0.023), (left, 0.023)]


def recessed_window(f, z0, z1, width, frame, name, columns, variants, lod):
    w = width / 2
    h = z1 - z0
    inner = 0.084 if width > 1.3 else 0.064
    bars = [
        box(-w, z0, -w + inner, z1),
        box(w - inner, z0, w, z1),
        box(-w, z0, w, z0 + inner),
        box(-w, z1 - inner, w, z1),
    ]
    positions = [-w + width * i / columns for i in range(columns + 1)]
    for x in positions[1:-1]:
        bars.append(box(x - 0.035, z0, x + 0.035, z1))
    rail = z0 + h * 0.69
    bars.append(box(-w, rail - 0.050, w, rail + 0.050))
    # In each leaf the timber meeting rail is shallower than the main transom.
    if not lod and z0 < 10:
        bars.append(box(-w, z0 + h * 0.31 - 0.022, w, z0 + h * 0.31 + 0.022))
    f.prism(unary_union(bars), -0.255, -0.17, WOOD, name + " / rebated timber frame")
    for i in range(columns):
        a = positions[i] + (0.032 if i else inner * 0.55)
        c = positions[i + 1] - (0.032 if i != columns - 1 else inner * 0.55)
        for row, (lo, hi) in enumerate(
            [(z0 + inner * 0.5, rail + 0.018), (rail - 0.018, z1 - inner * 0.5)]
        ):
            mat = variants[(i + row) % len(variants)]
            glass_pane(f, a, c, lo, hi, mat, name + f" / sash {i + 1} pane {row + 1}", -0.259)
    f.box(0, z0 - 0.042, width + 0.13, 0.084, 0.13, 0.046, EDGE, name + " / projecting sill")
    if not lod:
        f.box(0, z1 + 0.032, width + 0.06, 0.064, 0.098, 0.04, EDGE, name + " / lintel lip")


def make_bow(b, lod):
    seg = 12 if lod else 30
    for floor, z0, z1 in HEADS:
        start = 0 if floor == "Street storey" else 5.20
        if start == 0:
            fan(b, 0, 0.43, BASE, "Street storey / grey plinth", seg)
            fan(b, 0.43, z0, PLASTER, "Street storey / plaster above grey plinth", seg, 0.017)
        else:
            fan(b, start, z0, PLASTER, floor + " / solid lower breast", seg)
        fan(b, z1, 5.19 if start == 0 else BALCONY, PLASTER, floor + " / curved spandrel", seg)
        spans = [
            (-BOW, -1.96, False),
            (-1.96, -1.17, True),
            (-1.17, -0.91, False),
            (-0.91, 0.91, True),
            (0.91, 1.17, False),
            (1.17, 1.96, True),
            (1.96, BOW, False),
        ]
        for i, (a, c, opening) in enumerate(spans):
            y0, y1 = front_y(a), front_y(c)
            f = plane(b, a, y0, c, y1, floor + " / bay " + str(i + 1))
            width = f.length
            if opening:
                # Each sash sits in its own chord behind the real stone reveal.
                skin = box(-width / 2, z0, width / 2, z1)
                aperture = box(-width / 2 + 0.027, z0 + 0.025, width / 2 - 0.027, z1 - 0.025)
                f.prism(skin.difference(aperture), -0.30, 0.0, PLASTER, "wash and jamb returns")
                options = TEXTILE[:2] if floor == "Street storey" else TEXTILE[2:4]
                recessed_window(
                    f,
                    z0 + 0.025,
                    z1 - 0.025,
                    width - 0.054,
                    WOOD,
                    "sash",
                    2 if i == 3 else 1,
                    options,
                    lod,
                )
            else:
                f.prism(
                    box(-width / 2, z0, width / 2, z1), -0.36, 0, PLASTER, "masonry dividing pier"
                )
        for z, h, d, mat, tag in [
            (z0 - 0.09, 0.08, 0.08, EDGE, "sill course"),
            (z1 + 0.09, 0.09, 0.09, EDGE, "lintel band"),
        ]:
            bow_trim(
                b,
                z,
                [(-0.035, -0.025), (d, -0.025), (d, h * 0.40), (d * 0.45, h), (-0.035, h)],
                mat,
                floor + " / " + tag,
                seg,
            )
    for z, tag in [(4.90, "first floor belt"), (9.85, "balcony soffit")]:
        bow_trim(
            b,
            z,
            [
                (-0.045, 0),
                (0.085, 0),
                (0.12, 0.038),
                (0.16, 0.110),
                (0.19, 0.13),
                (0.19, 0.19),
                (0.03, 0.22),
                (-0.045, 0.22),
            ],
            EDGE,
            "Bay courses / " + tag,
            seg,
        )
    for z in [0.44, 4.60, 5.11, 9.55]:
        bow_trim(
            b,
            z,
            [(-0.012, 0), (0.016, 0), (0.016, 0.019), (-0.012, 0.019)],
            SHADOW,
            "Bay courses / incised joint",
            seg,
        )


def balcony(b, lod):
    seg = 14 if lod else 32
    vases = 13
    for i in range(vases):
        x = -1.86 + 3.72 * i / (vases - 1)
        y = front_y(x, 1.23) - 0.045
        # Open spaces between individually turned bottle-shaped balusters.
        profile = [
            (0, 0.090),
            (0.06, 0.101),
            (0.105, 0.078),
            (0.15, 0.062),
            (0.22, 0.102),
            (0.29, 0.101),
            (0.385, 0.060),
            (0.45, 0.041),
            (0.50, 0.065),
            (0.545, 0.085),
            (0.58, 0.092),
        ]
        if lod:
            profile = [profile[k] for k in (0, 1, 3, 5, 7, 10)]
        b.lathe(
            (x, y),
            [(BALCONY + 0.075 + z, r) for z, r in profile],
            EDGE,
            7 if lod else 12,
            label="Upper balcony / turned stone vase " + str(i + 1),
        )
    for sign in (-1, 1):
        b.box(
            (sign * 2.10, front_y(2.10, 1.23), BALCONY + 0.366),
            (0.32, 0.39, 0.73),
            PLASTER,
            label="Upper balcony / solid end pier",
        )
    bow_trim(
        b,
        BALCONY + 0.012,
        [(-0.065, 0), (0.10, 0), (0.11, 0.062), (0.07, 0.12), (-0.065, 0.12)],
        EDGE,
        "Upper balcony / lower curb",
        seg,
        1.23,
    )
    bow_trim(
        b,
        BALCONY + 0.65,
        [(-0.105, 0), (0.10, 0), (0.135, 0.041), (0.135, 0.105), (0.06, 0.15), (-0.105, 0.15)],
        EDGE,
        "Upper balcony / handrail",
        seg,
        1.23,
    )
    for i in range(13):
        x = -1.99 + 3.98 * i / 12
        y = front_y(x)
        b.box(
            (x, y - 0.085, 9.72),
            (0.13, 0.30, 0.14),
            EDGE,
            label="Balcony underside / spaced modillions",
        )
