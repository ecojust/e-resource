"""Four Ionic columns and the stone entablature of the south garden portico."""

import math
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

PITCH = 2.9162914
AXES = tuple(i * PITCH for i in (-1.5, -0.5, 0.5, 1.5))
COLUMN_Y = 0.30
WALL_Y = COLUMN_Y + 3.4876327
RETURN_Y = COLUMN_Y + 1.9758510
HALF = 5.12
BASE = 0.255
STONE = "Warm grey dressed stone"
LIGHT = "Light grey raised mouldings"
BELT = "Grey cornice shadow courses"
FLOOR = "Grey garden paving"
WALL = "Grey buff mineral render"
WOOD = "Ivory painted glazing bars"
FRAME = "Dark umber door reveals"
IRON = "Oxidised balcony iron"
FAN = "Clear garden transom glass"
GLASS = ("Glazing in garden shade", "Glazing in reflected sky", "Glazing in recessed bay")


def finish(rgb, roughness, metallic=0):
    def linear(byte):
        s = byte / 255
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4

    return dict(color=[linear(c) for c in rgb], roughness=roughness, metallic=metallic)


PALETTE = {
    STONE: finish((169, 160, 142), 0.83),
    LIGHT: finish((194, 185, 166), 0.77),
    BELT: finish((142, 135, 120), 0.82),
    FLOOR: finish((149, 147, 141), 0.84),
    WALL: finish((158, 148, 129), 0.88),
    WOOD: finish((207, 202, 183), 0.56),
    FRAME: finish((87, 77, 62), 0.72),
    IRON: finish((70, 68, 59), 0.52, 0.35),
    FAN: {**finish((165, 185, 182), 0.16, 0.04), "alpha": 0.25},
    GLASS[0]: finish((71, 82, 79), 0.24, 0.19),
    GLASS[1]: finish((110, 124, 121), 0.27, 0.14),
    GLASS[2]: finish((53, 58, 54), 0.32, 0.14),
}


def fluted_shaft(b, x, lod, name):
    flutes = 24
    subdivisions = 3 if lod else 7
    count = flutes * subdivisions
    rings = (
        (0.0, 0.025, 0.52, 0.975, 1.0)
        if lod
        else (0.0, 0.012, 0.032, 0.16, 0.33, 0.51, 0.72, 0.955, 0.985, 1.0)
    )
    base, top = 0.68, 5.99
    vertices = []
    for t in rings:
        radius = 0.398 - 0.061 * t + 0.013 * math.sin(t * math.pi)
        fade = max(0, min(1, t / 0.032, (1 - t) / 0.035))
        for i in range(count):
            fraction = i % subdivisions / subdivisions
            channel = max(0, 1 - ((fraction - 0.5) / 0.45) ** 2)
            r = radius - 0.023 * math.sqrt(channel) * fade
            angle = math.tau * (i / count + 0.5 / count)
            vertices.append(
                (x + r * math.cos(angle), COLUMN_Y + r * math.sin(angle), base + (top - base) * t)
            )
    faces = [
        tuple(reversed(range(count))),
        tuple(range((len(rings) - 1) * count, len(rings) * count)),
    ]
    for row in range(len(rings) - 1):
        for i in range(count):
            a = row * count + i
            n = row * count + (i + 1) % count
            faces.append((a, n, n + count, a + count))
    b.add(vertices, faces, STONE, name + " fluted tapered shaft")


def ionic_column(b, index, x, lod):
    name = f"Ionic column {index + 1}"
    n = 20 if lod else 48
    b.box((x, COLUMN_Y, BASE + 0.045), (1.07, 1.07, 0.09), STONE, label=name + " square foot")
    base = [
        (0.34, 0.51),
        (0.374, 0.51),
        (0.387, 0.472),
        (0.407, 0.461),
        (0.425, 0.485),
        (0.451, 0.494),
        (0.473, 0.484),
        (0.494, 0.446),
        (0.512, 0.434),
        (0.525, 0.426),
        (0.550, 0.419),
        (0.568, 0.443),
        (0.592, 0.448),
        (0.617, 0.437),
        (0.638, 0.401),
        (0.68, 0.398),
    ]
    if lod:
        base = [base[k] for k in (0, 1, 3, 5, 7, 10, 12, 14, 15)]
    b.lathe((x, COLUMN_Y), base, LIGHT, n, name + " torus and scotia")
    fluted_shaft(b, x, lod, name)
    neck = [
        (5.985, 0.338),
        (6.015, 0.351),
        (6.043, 0.375),
        (6.070, 0.365),
        (6.092, 0.338),
        (6.126, 0.349),
        (6.159, 0.383),
        (6.193, 0.417),
        (6.238, 0.429),
    ]
    b.lathe((x, COLUMN_Y), neck, LIGHT, n, name + " neck and echinus")
    b.box((x, COLUMN_Y, 6.287), (0.78, 0.58, 0.16), STONE, label=name + " cushion")
    for side in (-1, 1):
        cx = x + side * 0.325
        b.tube(
            [(cx, COLUMN_Y - 0.297, 6.248), (cx, COLUMN_Y + 0.297, 6.248)],
            0.115,
            STONE,
            12 if lod else 24,
            name + " bolster",
        )
        for face in (-1, 1):
            path = []
            samples = 15 if lod else 35
            for k in range(samples + 1):
                t = k / samples
                a = math.pi / 2 - 1.8 * math.tau * t
                r = 0.132 * (1 - t) ** 1.1 + 0.010
                path.append(
                    (cx + side * r * math.cos(a), COLUMN_Y + face * 0.308, 6.247 + r * math.sin(a))
                )
            b.tube(path, 0.014 if lod else 0.016, LIGHT, 5 if lod else 8, name + " scroll")
    b.box((x, COLUMN_Y, 6.429), (0.97, 0.85, 0.122), LIGHT, label=name + " abacus")


def entablature(b, lod):
    profiles = [
        (6.49, 6.56, -0.19, STONE),
        (6.56, 6.64, -0.215, LIGHT),
        (6.64, 6.74, -0.185, STONE),
        (6.74, 6.79, -0.24, LIGHT),
        (6.79, 6.99, -0.155, STONE),
        (6.99, 7.055, -0.255, BELT),
        (7.055, 7.105, -0.29, LIGHT),
        (7.105, 7.45, -0.16, STONE),
        (7.45, 7.52, -0.22, LIGHT),
        (7.52, 7.64, -0.255, BELT),
        (7.64, 7.71, -0.32, LIGHT),
        (7.71, 7.80, -0.30, STONE),
        (7.80, 7.875, -0.375, LIGHT),
        (7.875, 7.94, -0.405, LIGHT),
    ]
    for i, (low, high, front, mat) in enumerate(profiles):
        side = HALF + (-0.155 - front) * 0.80
        outer = box(-side, front, side, 4.22)
        inner = box(-4.58, 0.78, 4.58, 4.35)
        b.plan_prism(
            outer.difference(inner), low, high, mat, f"Returning cornice course {i + 1:02}"
        )
    for i in range(46):
        x = -5.145 + 10.29 * i / 45
        b.box((x, -0.247, 7.57), (0.120, 0.142, 0.114), STONE, label="Front dentil course")
    for sign in (-1, 1):
        for i in range(19):
            b.box(
                (sign * (HALF + 0.07), -0.08 + i * 0.226, 7.57),
                (0.125, 0.117, 0.114),
                STONE,
                label="Returning dentil course",
            )
    # The bright openings in the front photograph sit behind the lintel.
    # Keep a row of actual roof openings in the soffit with shallow crossing bars.
    holes = [box(-4.28 + i * 1.08, 0.87, -3.39 + i * 1.08, 1.62) for i in range(8)]
    deck = box(-4.62, 0.74, 4.62, 4.23).difference(unary_union(holes))
    b.plan_prism(deck, 7.66, 7.86, STONE, "Openings in stone portico ceiling")
    for cut in holes:
        u, v, s, t = cut.bounds
        for p, q in [((u, v), (s, t)), ((s, v), (u, t))]:
            b.tube([(*p, 7.81), (*q, 7.81)], 0.018, IRON, 5 if lod else 7, "Ceiling light diagonal")


def parapet(b, lod):
    count = 8

    def bay(a, c):
        dx, dy = c[0] - a[0], c[1] - a[1]
        length = math.hypot(dx, dy)
        along = (dx / length, dy / length, 0)
        cross = (-dy / length, dx / length, 0)
        mid = ((a[0] + c[0]) / 2, (a[1] + c[1]) / 2)
        for z, thickness, width, mat in [
            (8.008, 0.136, 0.31, STONE),
            (8.559, 0.105, 0.345, STONE),
            (8.645, 0.07, 0.38, LIGHT),
        ]:
            b.box(
                (*mid, z),
                (length, width, thickness),
                mat,
                basis=(along, cross, (0, 0, 1)),
                label="Parapet rail",
            )
        for j in range(1, count + 1):
            t = j / (count + 1)
            x = a[0] + t * dx
            y = a[1] + t * dy
            profile = [
                (8.075, 0.07),
                (8.096, 0.079),
                (8.132, 0.056),
                (8.181, 0.055),
                (8.252, 0.089),
                (8.311, 0.088),
                (8.372, 0.064),
                (8.432, 0.043),
                (8.474, 0.051),
                (8.507, 0.070),
            ]
            if lod:
                profile = [profile[k] for k in (0, 1, 3, 4, 6, 7, 9)]
            b.lathe((x, y), profile, STONE, 7 if lod else 12, "Parapet turned baluster")

    points = [(x, -0.035) for x in (-5.04, -1.68, 1.68, 5.04)]
    for i in range(3):
        bay(points[i], points[i + 1])
    for end in [points[0], points[-1]]:
        bay(end, (end[0], 3.55))
    for x, y in points + [(points[0][0], 3.55), (points[-1][0], 3.55)]:
        b.box((x, y, 8.26), (0.39, 0.39, 0.65), STONE, label="Parapet square pedestal")
        b.box((x, y, 8.627), (0.49, 0.47, 0.106), LIGHT, label="Parapet pedestal coping")
