"""Brick piers, moulded springers, masonry arch and photograph-derived signs at 522 Jiaozhou Road.

The drawing units are multiples of the clear opening. A single physical scale is applied
by the model entry point. The exterior points towards negative Y.
"""

from pathlib import Path
import math

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from plaque_samples import TILES

SOURCE = Path(__file__).resolve().parent
PIER = 0.241
SPRING = 1.096
WIDTH = 0.5 + PIER / 2
DEPTH = 0.226
ARCH_RISE = 0.515
BASE = "Grey stippled plinth"
MORTAR = "Warm lime joints"
BRICKS = ["Umber brick", "Russet brick", "Smoked brick"]
CREAM = "Limestone coloured render"
LIGHT = "Stone nosing"
SHADE = "Recessed rendered panel"
IRON = "Graphite wrought iron"
GOLD = "Ochre gilt iron tips"
BORDER = "Bronze plaque returns"
WHITE = "Glazed alarm cover"


def finish(rgb, rough=0.8, metal=0.0):
    def linear(x):
        c = x / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return dict(color=[linear(c) for c in rgb], roughness=rough, metallic=metal)


PALETTE = {
    BASE: finish((101, 101, 102)),
    MORTAR: finish((132, 118, 109)),
    BRICKS[0]: finish((117, 79, 69)),
    BRICKS[1]: finish((125, 84, 73)),
    BRICKS[2]: finish((107, 75, 66)),
    CREAM: finish((209, 201, 183)),
    LIGHT: finish((225, 216, 197)),
    SHADE: finish((193, 183, 164)),
    IRON: finish((58, 55, 51), 0.55, 0.43),
    GOLD: finish((172, 126, 56), 0.52, 0.48),
    "Ochre yellow sign enamel": finish((191, 142, 45), 0.50),
    BORDER: finish((129, 104, 65), 0.53, 0.45),
    WHITE: finish((195, 192, 177), 0.40, 0.18),
}
for name in TILES:
    PALETTE[name] = dict(
        color=[1, 1, 1], roughness=0.68, metallic=0.08, texture=str(SOURCE / "entrance-plaques.png")
    )


def block(b, bounds, material, name):
    x0, y0, z0, x1, y1, z1 = bounds
    b.box(
        ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
        (x1 - x0, y1 - y0, z1 - z0),
        material,
        label=name,
    )


def front(b, shape, out, back, material, name):
    b.prism(shape, -back, -out, lambda x, z, d: (x, -d, z), material, name)


def ring(r0, h0, r1, h1, n):
    def arc(w, h):
        return [
            (w * math.cos(math.pi * i / n), SPRING + h * math.sin(math.pi * i / n))
            for i in range(n + 1)
        ]

    return Polygon(arc(r1, h1) + list(reversed(arc(r0, h0))))


def pier(b, sign, lod):
    caption = "Left pier" if sign < 0 else "Right pier"
    c = sign * WIDTH
    for name, base, top, extra, y, mat in [
        ("plinth", 0, 0.145, 0.018, -0.017, BASE),
        ("lower plinth edge", 0.136, 0.159, 0.020, -0.021, BASE),
        ("plinth top", 0.158, 0.181, 0.011, -0.011, BASE),
        ("brick backing", 0.178, 0.927, 0, 0.003, MORTAR),
        ("lower capital lip", 0.923, 0.943, 0.021, -0.026, LIGHT),
        ("capital bed", 0.943, 0.953, 0.015, -0.019, SHADE),
        ("capital", 0.951, 1.071, 0.010, -0.012, CREAM),
        ("upper capital lip", 1.067, 1.085, 0.023, -0.028, LIGHT),
        ("impost", 1.084, SPRING, 0.019, -0.022, CREAM),
    ]:
        block(
            b,
            (c - PIER / 2 - extra, y, base, c + PIER / 2 + extra, DEPTH - y, top),
            mat,
            caption + " / " + name,
        )
    for z0, z1, mat, label in [
        (0.025, 0.127, BASE, "plinth ashlar"),
        (0.961, 1.061, SHADE, "impost sunk panel"),
    ]:
        panel = box(c - PIER * 0.44, z0, c + PIER * 0.44, z1)
        inner = box(c - PIER * 0.40, z0 + 0.009, c + PIER * 0.40, z1 - 0.009)
        if label.startswith("impost"):
            front(
                b,
                panel.difference(inner),
                -0.0175,
                -0.012,
                CREAM,
                caption + " / panel relief frame",
            )
            front(b, inner, -0.0135, -0.012, mat, caption + " / inset tablet")
        else:
            front(b, panel.difference(inner), -0.0195, -0.017, mat, caption + " / " + label)
    z0 = 0.181
    h = (0.925 - z0) / 32
    for row in range(32):
        low = z0 + h * row + 0.00125
        high = z0 + h * (row + 1) - 0.00125
        # Header/stretcher alternation continues over the exposed three sides of each pier.
        front_left = c - PIER / 2
        for axis, (length, origin) in enumerate([(PIER, front_left), (DEPTH, 0), (DEPTH, 0)]):
            if lod and axis == 2:
                continue
            start = -0.060 * (row % 2)
            tile = 0
            while start < length:
                lo = max(0, start) + 0.001
                hi = min(length, start + 0.122) - 0.001
                if hi > lo + 0.002:
                    mat = BRICKS[(row * 5 + tile * 11 + axis * 7 + (sign + 1)) % 3]
                    if axis == 0:
                        bounds = (origin + lo, -0.002, low, origin + hi, 0.003, high)
                    else:
                        x = c + (1 if axis == 1 else -1) * PIER / 2
                        bounds = (x - 0.0017, lo, low, x + 0.0017, hi, high)
                    block(b, bounds, mat, caption + f" / bonded brick courses {row // 4 + 1}")
                tile += 1
                start += 0.122


def arch(b, lod):
    n = 38 if lod else 86
    # The soffit is deeper than either face moulding and the two recessed fascia lines are concentric.
    for rin, hin, rout, hout, y0, y1, mat, name in [
        (0.5, ARCH_RISE, 0.742, 0.731, -0.006, DEPTH + 0.006, CREAM, "solid rendered barrel"),
        (0.500, ARCH_RISE, 0.528, 0.538, -0.017, -0.005, LIGHT, "inner reveal moulding"),
        (0.530, 0.540, 0.721, 0.703, -0.010, -0.005, CREAM, "arched fascia"),
        (0.718, 0.702, 0.735, 0.720, -0.014, -0.005, SHADE, "weather groove"),
        (0.731, 0.717, 0.745, 0.735, -0.020, -0.006, LIGHT, "raised outer coping"),
        (
            0.500,
            ARCH_RISE,
            0.518,
            0.532,
            DEPTH + 0.005,
            DEPTH + 0.015,
            LIGHT,
            "courtyard soffit rim",
        ),
    ]:
        front(b, ring(rin, hin, rout, hout, n), y0, y1, mat, "Arch / " + name)


def plaque(b, name, x, z, width, height, out):
    block(
        b,
        (
            x - width / 2 - 0.004,
            out,
            z - height / 2 - 0.004,
            x + width / 2 + 0.004,
            -0.002,
            z + height / 2 + 0.004,
        ),
        BORDER,
        name + " / frame",
    )
    verts = [
        (x - width / 2, out - 0.0008, z - height / 2),
        (x + width / 2, out - 0.0008, z - height / 2),
        (x + width / 2, out - 0.0008, z + height / 2),
        (x - width / 2, out - 0.0008, z + height / 2),
    ]
    b.add(verts, [(0, 1, 2), (0, 2, 3)], name, name + " / lettering")
    i = list(TILES).index(name)
    a = (128 * i + 0.5) / 384
    c = (128 * i + 127.5) / 384
    b.parts[-1]["texcoords"] = [(a, 0.995), (c, 0.995), (c, 0.005), (a, 0.005)]


def add_stone(b, lod):
    for sign in (-1, 1):
        pier(b, sign, lod)
    arch(b, lod)
    plaque(b, list(TILES)[0], -WIDTH, 0.831, 0.178, 0.124, -0.012)
    plaque(b, list(TILES)[1], -WIDTH, 0.726, 0.115, 0.065, -0.011)
    plaque(b, list(TILES)[2], WIDTH, 0.758, 0.183, 0.150, -0.012)
    block(
        b,
        (WIDTH - 0.054, -0.013, 0.856, WIDTH + 0.054, 0, 0.925),
        SHADE,
        "Right pier / lamp bedding",
    )
    # Circular housing immediately above the 2015 plaque. The 2024 image shows a later red fitting.
    for r, d, mat, ident in [(0.031, 0.013, BORDER, "rim"), (0.023, 0.018, WHITE, "round cover")]:
        from shapely.geometry import Point

        disc = Point(WIDTH, 0.891).buffer(r, quad_segs=7 if lod else 16)
        front(b, disc, -0.014 - d, -0.013, mat, "Right pier / lamp " + ident)
