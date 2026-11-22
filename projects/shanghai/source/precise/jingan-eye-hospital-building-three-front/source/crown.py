"""Washed-stone pilasters, the curved attic pediment, cast wall numeral and short returns."""

import math
from shapely.geometry import Point, Polygon, LineString, box
from shapely.affinity import scale
from shapely.ops import unary_union
from bay import (
    HALF,
    BOW,
    BACK,
    BALCONY,
    EDGE_Y,
    PLASTER,
    EDGE,
    SHADOW,
    BASE,
    WOOD,
    BRASS,
    METAL,
    ROOF,
    TOP_SILL,
    TOP_HEAD,
    TEXTILE,
    plane,
    horizontal,
    recessed_window,
    make_bow,
    balcony,
)


def arc(cx, cz, rx, rz, a0, a1, n):
    return [
        (cx + rx * math.cos(a0 + (a1 - a0) * i / n), cz + rz * math.sin(a0 + (a1 - a0) * i / n))
        for i in range(n + 1)
    ]


def relief(f, pts, t, lo, hi, mat, name):
    shape = LineString(pts).buffer(t / 2, cap_style="round", join_style="round", quad_segs=3)
    f.prism(shape, lo, hi, mat, name)


def medallion(f, x, z, rx, rz, lod, label):
    disc = scale(Point(x, z).buffer(1, quad_segs=5 if lod else 11), rx, rz, origin=(x, z))
    f.prism(disc, 0.115, 0.157, EDGE, label + " / circular medallion")
    if not lod:
        f.prism(
            disc.buffer(0.026).difference(disc.buffer(0.006)),
            0.1,
            0.133,
            SHADOW,
            label + " / sunken border",
        )


def numeral(f, lod):
    # Centreline of the cast 3, scaled from Legolas1024's close ground-storey view.
    top = [
        (-0.19, 0.20),
        (-0.165, 0.28),
        (-0.094, 0.34),
        (0.028, 0.35),
        (0.13, 0.318),
        (0.192, 0.243),
        (0.197, 0.161),
        (0.163, 0.089),
        (0.087, 0.027),
        (0.014, -0.006),
    ]
    bottom = [
        (0.012, -0.005),
        (0.109, -0.025),
        (0.189, -0.088),
        (0.219, -0.18),
        (0.203, -0.267),
        (0.136, -0.34),
        (0.031, -0.378),
        (-0.082, -0.364),
        (-0.165, -0.315),
        (-0.208, -0.222),
        (-0.180, -0.175),
    ]
    x, z = -2.67, 4.20
    for off, thickness, low, high, mat, label in [
        (0.014, 0.078, 0.102, 0.155, METAL, "backplate"),
        (0, 0.063, 0.152, 0.205, BRASS, "cast face"),
    ]:
        line = [(x + u + off, z + v - off) for u, v in top + bottom]
        relief(f, line, thickness, low, high, mat, "Building 3 / " + label)
        for k, (u, v) in enumerate((top[0], bottom[-1])):
            disk = Point(x + u + off, z + v - off).buffer(
                0.054 if k else 0.041, quad_segs=5 if lod else 11
            )
            f.prism(disk, low, high, mat, "Building 3 / numeral terminals")


def pilaster(b, f, sign, lod):
    x = sign * 2.72
    name = ("West" if sign < 0 else "East") + " pilaster"
    # In the photograph the recessed joints continue round each pier.
    z = 0.43
    count = 17
    step = (9.29 - z) / count
    for i in range(count):
        height = step - 0.022
        b.box(
            (x, 0.27, z + i * step + height / 2),
            (1.025, 0.75, height),
            PLASTER,
            label=name + " / channelled lower shaft",
        )
    f.box(x, 0.218, 1.06, 0.436, 0.67, -0.23, BASE, name + " / grey footing")
    b.box((x, 0.265, 9.46), (0.99, 0.70, 0.40), EDGE, label=name + " / neck")
    for i in range(6):
        cx = x - 0.38 + i * 0.153
        f.box(cx, 9.52, 0.067, 0.18, 0.10, 0.11, EDGE, name + " / carved tablets")
    for z, w, h, d in [
        (9.28, 1.10, 0.065, 0.17),
        (9.76, 1.13, 0.08, 0.19),
        (9.91, 1.21, 0.12, 0.225),
    ]:
        f.box(x, z, w, h, 0.23, d - 0.115, EDGE, name + " / capital courses")
    f.box(x, 10.23, 1.04, 0.51, 0.73, -0.235, PLASTER, name + " / square entablature")
    medallion(f, x, 10.25, 0.16, 0.155, lod, name + " lower frieze")
    for side in (-1, 1):
        for j in range(3 if not lod else 2):
            f.box(
                x + side * (0.272 + j * 0.060),
                10.25,
                0.022,
                0.235,
                0.042,
                0.122,
                EDGE,
                name + " / frieze grooves",
            )
    f.box(x, 10.57, 1.19, 0.12, 0.82, -0.225, EDGE, name + " / attic base")
    f.box(x, 12.44, 0.84, 3.59, 0.64, -0.215, PLASTER, name + " / attic shaft")
    for side in (-1, 1):
        f.box(x + side * 0.39, 12.39, 0.067, 3.37, 0.105, 0.066, EDGE, name + " / attic arris")
    medallion(f, x, 13.81, 0.165, 0.159, lod, name + " attic")
    if not lod:
        for j in range(3):
            z = 13.50 - j * 0.125
            drop = Point(x, z).buffer(0.043 - j * 0.007, quad_segs=6)
            f.prism(drop, 0.093, 0.145, EDGE, name + " / descending pendant")
    for z, w, dep, h in [
        (14.00, 0.96, 0.16, 0.084),
        (14.13, 1.09, 0.22, 0.15),
        (14.245, 1.18, 0.265, 0.10),
        (14.34, 1.21, 0.29, 0.089),
    ]:
        f.box(x, z, w, h, 0.29, dep - 0.145, EDGE, name + " / overhanging cap")
    for i in range(7):
        f.box(
            x - 0.424 + i * 0.141,
            14.055,
            0.074,
            0.093,
            0.16,
            0.087,
            SHADOW,
            name + " / underslung dentils",
        )


def gable(f, lod):
    n = 5 if lod else 12
    # The shoulder and crown consist of three separate curves with square steps between.
    half = [(-3.18, 14.27), (-3.18, 14.71), (-2.49, 14.71)]

    def eased(a, b, top, bottom):
        return [
            (a + (b - a) * i / n, bottom + (top - bottom) * (math.sin(i / n * math.pi / 2) ** 0.92))
            for i in range(1, n + 1)
        ]

    half += eased(-2.49, -1.20, 15.52, 14.71)
    half += [(-1.09, 15.52), (-1.09, 15.71), (-0.82, 15.71)]
    half += eased(-0.82, 0, 16.64, 15.71)
    outline = half + [(-x, z) for x, z in reversed(half[:-1])]
    face = Polygon([(-3.18, 13.63), (3.18, 13.63), *reversed(outline)])
    f.prism(face, -0.41, 0.034, PLASTER, "Attic / stepped curvilinear gable")
    relief(f, outline, 0.092, -0.015, 0.115, EDGE, "Attic / coping around both shoulders")
    for z in [14.00, 14.44, 14.94, 15.39, 15.88, 16.27]:
        incision = box(-3.17, z - 0.009, 3.17, z + 0.009).intersection(face)
        f.prism(incision, 0.034, 0.041, SHADOW, "Attic / washed-stone joints")
    f.box(0, 15.45, 0.40, 0.62, 0.075, 0.043, EDGE, "Attic / flat rectangular key")
    for z, w in ((15.12, 0.71), (15.77, 0.79)):
        f.box(0, z, w, 0.089, 0.11, 0.085, EDGE, "Attic / projecting key ledges")
    ped = arc(0, 13.43, 1.84, 0.62, math.pi, 0, n * 2)
    f.prism(
        Polygon([(-1.84, 13.37), (1.84, 13.37), *reversed(ped)]),
        0.05,
        0.127,
        PLASTER,
        "Attic opening / segmental tympanum",
    )
    relief(f, ped, 0.104, 0.10, 0.21, EDGE, "Attic opening / arched pediment cornice")
    f.box(0, 13.39, 3.75, 0.10, 0.16, 0.12, EDGE, "Attic opening / pediment tie")
    for s in (-1, 1):
        for j, (cx, cz, r) in enumerate(
            (
                (0.32, 13.67, 0.129),
                (0.635, 13.67, 0.115),
                (0.930, 13.6, 0.085),
                (1.19, 13.54, 0.066),
            )
        ):
            pts = []
            for i in range(10 if lod else 22):
                t = i / (9 if lod else 21)
                a = t * math.pi * 1.78 + 0.16
                rr = r * (1 - 0.66 * t)
                pts.append((s * (cx + rr * math.cos(a)), cz + rr * math.sin(a)))
            relief(f, pts, 0.037, 0.126, 0.176, EDGE, "Attic opening / foliate scroll")
    medallion(f, 0, 13.73, 0.083, 0.095, lod, "Tympanum rosette")
    f.builder.lathe(
        (0, -0.02),
        [(16.61, 0.15), (16.78, 0.13), (16.85, 0.079), (16.98, 0.075), (17.01, 0.105)],
        EDGE,
        9 if lod else 18,
        "Attic / finial pedestal",
    )
    radii = [
        (16.99, 0.065),
        (17.026, 0.099),
        (17.071, 0.124),
        (17.12, 0.128),
        (17.18, 0.106),
        (17.22, 0.071),
        (17.25, 0.021),
    ]
    f.builder.lathe((0, -0.02), radii, EDGE, 10 if lod else 22, "Attic / ball finial")


def add_building(b, lod=False):
    start = len(b.parts)
    f = plane(b, -HALF, 0, HALF, 0, "Courtyard face")
    for s in (-1, 1):
        left, right = sorted((s * HALF, s * BOW))
        b.box(
            ((left + right) / 2, BACK / 2, 7.01),
            (right - left, BACK, 14.02),
            PLASTER,
            label="Cut section / solid lateral pier",
        )
        b.box(
            (s * (BOW + 0.14), (-0.75 + 0.08) / 2, 5.04),
            (0.28, 0.83, 10.08),
            PLASTER,
            label="Bay / cheek return to pier",
        )
        pilaster(b, f, s, lod)
    b.box(
        (0, (0.43 + BACK) / 2, 5.04),
        (2 * BOW, BACK - 0.43, 10.08),
        PLASTER,
        label="Cut section / opaque lower inner wall",
    )
    aperture = box(-1.57, TOP_SILL, 1.57, TOP_HEAD)
    f.prism(
        box(-BOW, BALCONY - 0.12, BOW, 14.24).difference(aperture),
        -BACK,
        -0.012,
        PLASTER,
        "Attic / cut wall and balcony-door reveals",
    )
    # The photographed glazing sits behind the lintel, between four large transom lights.
    recessed_window(f, TOP_SILL, TOP_HEAD, 3.14, WOOD, "Attic balcony door", 4, TEXTILE[-1:], lod)
    f.box(0, 13.29, 3.41, 0.097, 0.152, 0.061, EDGE, "Attic / head of balcony door")
    f.box(0, 13.12, 3.37, 0.084, 0.126, 0.058, EDGE, "Attic / recessed soffit bead")
    make_bow(b, lod)
    balcony(b, lod)
    gable(f, lod)
    numeral(f, lod)
    # The sign occupies the right pier; the small inscription is illegible at this scale.
    f.box(2.71, 3.09, 0.61, 0.51, 0.032, 0.120, METAL, "Heritage plaque / cast frame")
    f.box(2.71, 3.09, 0.57, 0.468, 0.025, 0.145, BASE, "Heritage plaque / stone face")
    for i, (w, z) in enumerate(((0.36, 3.175), (0.29, 3.122), (0.43, 3.024), (0.38, 2.988))):
        f.box(
            2.71,
            z,
            w,
            0.012 if i else 0.020,
            0.008,
            0.161,
            METAL,
            "Heritage plaque / inscription groups",
        )
    # Roof behind the gable is a bounded section of the red-tiled roof in the earlier survey.
    cross = Polygon([(-HALF, 13.86), (HALF, 13.86), (HALF, 14.07), (0, 15.34), (-HALF, 14.07)])
    f.prism(cross, -BACK, -0.40, ROOF, "Roof / sheltered pitched tile section")
    if not lod:
        for sign in (-1, 1):
            for row in range(11):
                a = row * HALF / 11
                end = (row + 1) * HALF / 11
                z0 = 15.34 - a * 1.27 / HALF
                z1 = 15.34 - end * 1.27 / HALF
                b.tube(
                    [(sign * end, 0.41, z1), (sign * end, BACK - 0.014, z1)],
                    0.022,
                    ROOF,
                    5,
                    "Roof / overlapping flat-tile rows",
                )
                joints = [0.43 + j * 0.31 + (row % 2) * 0.155 for j in range(8)]
                for y in joints:
                    if y > BACK - 0.035:
                        continue
                    b.tube(
                        [(sign * a, y, z0 + 0.014), (sign * end, y, z1 + 0.014)],
                        0.010,
                        SHADOW,
                        5,
                        "Roof / staggered tile joints",
                    )
    else:
        for j in range(1, 6):
            for sign in (-1, 1):
                x = sign * j * HALF / 6
                z = 15.34 - abs(x) * 1.27 / HALF
                b.tube(
                    [(x, 0.42, z), (x, BACK - 0.015, z)],
                    0.024,
                    ROOF,
                    5,
                    "Roof / distant tile courses",
                )
    # Piecewise vertical rectification uses the independent February and July
    # cameras. Different storeys require different corrections under perspective.
    surveyed = [(0, 0), (5.20, 5.21), (10.19, 10.32), (14.34, 14.68), (17.25, 17.84)]

    def corrected(z):
        for (a, za), (c, zc) in zip(surveyed, surveyed[1:]):
            if z <= c + 1e-6:
                return za + (z - a) * (zc - za) / (c - a)
        return z + surveyed[-1][1] - surveyed[-1][0]

    for part in b.parts[start:]:
        part["vertices"] = [(x, y, corrected(z)) for x, y, z in part["vertices"]]
