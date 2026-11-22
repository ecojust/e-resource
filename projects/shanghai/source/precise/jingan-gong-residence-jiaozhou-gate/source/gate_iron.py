"""Trace the three principal spokes, paired scrolls and two pierced iron gate leaves."""

import math
from shapely.geometry import LineString, Polygon

from gate_stone import ARCH_RISE, GOLD, IRON, SPRING, front


def bezier(start, curves, count):
    points = [start]
    for p1, p2, p3 in curves:
        x0, z0 = points[-1]
        for i in range(1, count + 1):
            t = i / count
            s = 1 - t
            points.append(
                (
                    s**3 * x0 + 3 * s * s * t * p1[0] + 3 * s * t * t * p2[0] + t**3 * p3[0],
                    s**3 * z0 + 3 * s * s * t * p1[1] + 3 * s * t * t * p2[1] + t**3 * p3[1],
                )
            )
    return points


def strip(b, path, width, depth, plane, material, label):
    """Give a drawn rail its rectangular forged section and all exposed returns."""
    outline = LineString(path).buffer(width / 2, cap_style="flat", join_style="round", quad_segs=2)
    b.prism(outline, -depth / 2, depth / 2, plane, material, label)


# The left half of the iron fan was traced from the winter photograph. The right
# half repeats the reflected motif. Coordinates refer to the rectified survey drawing.
FAN_SCROLLS = [
    (
        (420, 122),
        [
            ((413, 74), (351, 75), (326, 108)),
            ((282, 163), (284, 267), (321, 313)),
            ((348, 352), (405, 363), (415, 317)),
            ((427, 275), (372, 265), (366, 298)),
        ],
    ),
    ((420, 205), [((406, 153), (355, 179), (332, 209)), ((303, 247), (311, 296), (325, 319))]),
    ((420, 204), [((413, 240), (381, 246), (368, 224))]),
    (
        (325, 318),
        [
            ((291, 271), (296, 223), (252, 201)),
            ((217, 182), (192, 208), (218, 229)),
            ((229, 239), (239, 231), (239, 224)),
        ],
    ),
    (
        (323, 381),
        [
            ((279, 343), (226, 299), (167, 306)),
            ((121, 309), (125, 370), (160, 373)),
            ((178, 373), (193, 360), (191, 347)),
        ],
    ),
    (
        (322, 381),
        [
            ((279, 334), (267, 288), (206, 255)),
            ((146, 223), (85, 248), (90, 291)),
            ((89, 333), (146, 344), (152, 285)),
        ],
    ),
    (
        (96, 314),
        [
            ((47, 311), (31, 361), (52, 412)),
            ((65, 443), (132, 467), (147, 428)),
            ((163, 389), (118, 372), (108, 405)),
            ((104, 419), (117, 428), (121, 423)),
        ],
    ),
    ((90, 358), [((113, 376), (125, 335), (104, 317))]),
    (
        (150, 440),
        [
            ((139, 391), (185, 349), (237, 355)),
            ((274, 359), (296, 396), (322, 422)),
            ((343, 445), (303, 457), (296, 430)),
            ((294, 420), (302, 414), (306, 419)),
        ],
    ),
    ((208, 439), [((195, 450), (198, 429), (207, 413))]),
    ((420, 440), [((391, 448), (371, 429), (379, 408)), ((389, 389), (407, 404), (393, 414))]),
]


def fan_point(px, py, side):
    x = (px - 420) / 817
    baseline = 438 - 25 * x
    return (x if side < 0 else -x, SPRING + (baseline - py) / 411 * ARCH_RISE)


def fan(b, lod):
    depth = 0.013
    plane = lambda x, z, d: (x, 0.070 - d, z)
    strip(b, [(-0.5, SPRING), (0.5, SPRING)], 0.015, depth, plane, IRON, "Fan / lintel tie")
    inner = 0.078
    arc = [
        (inner * math.cos(t * math.pi / 36), SPRING + inner * math.sin(t * math.pi / 36))
        for t in range(37)
    ]
    strip(b, arc, 0.006, depth, plane, IRON, "Fan / central semicircle")
    for deg in (45, 90, 135):
        theta = math.radians(deg)
        cs, sn = math.cos(theta), math.sin(theta)
        strip(
            b,
            [(inner * cs, SPRING + inner * sn), (0.5 * cs, SPRING + ARCH_RISE * sn)],
            0.013 if deg != 90 else 0.0155,
            depth,
            plane,
            IRON,
            f"Fan / spoke {deg}",
        )
    for side, name in [(-1, "left"), (1, "right")]:
        for index, (start, curves) in enumerate(FAN_SCROLLS):
            pts = [fan_point(x, y, side) for x, y in bezier(start, curves, 5 if lod else 13)]
            strip(
                b,
                pts,
                0.0037 if lod else 0.0030,
                0.006,
                plane,
                IRON,
                f"Fan / {name} wrought scroll {index + 1:02}",
            )


def profile(t):
    return 0.845 + 0.125 * (t * t * (3 - 2 * t)) + 0.012 * math.sin(t * math.pi * 2)


def spiral(cx, cz, rx, rz, turn, side, steps):
    points = []
    for i in range(steps + 1):
        t = i / steps
        r = 1 - 0.87 * t
        a = turn + t * 1.7 * math.pi
        points.append((cx + side * rx * r * math.cos(a), cz + rz * r * math.sin(a)))
    return points


def leaf(b, sign, angle, lod):
    name = "Left open leaf" if sign < 0 else "Right near-closed leaf"
    # The coordinate u increases from each hinge towards the free stile.
    vx = -sign * math.cos(math.radians(angle))
    vy = math.sin(math.radians(angle))

    def plane(u, z, d):
        return (sign * 0.487 + u * vx + vy * d, 0.139 + u * vy - vx * d, z)

    def rail(pts, width, thickness, label, mat=IRON):
        strip(b, pts, width, thickness, plane, mat, name + " / " + label)

    span = 0.480
    rail([(0, 0.027), (0, profile(0))], 0.016, 0.016, "hinge stile")
    rail([(span, 0.027), (span, profile(1))], 0.017, 0.016, "meeting stile")
    for i, (dz, width) in enumerate([(0, 0.017), (-0.079, 0.012)]):
        rail(
            [(span * t / 28, profile(t / 28) + dz) for t in range(29)],
            width,
            0.015,
            f"swept top rail {i + 1}",
        )
    for z, width in [(0.028, 0.015), (0.147, 0.012)]:
        rail([(0, z), (span, z)], width, 0.013, f"lower rail {round(z * 100)}")
    for i in range(1, 12):
        t = i / 12
        u = span * t
        rail(
            [(u, 0.033), (u, profile(t) - 0.005)],
            0.0036 if i % 3 else 0.005,
            0.006,
            f"plain vertical bar {i:02}",
        )
        if i % 2:
            for level, mid, r in [("upper", profile(t) - 0.043, 0.016), ("foot", 0.084, 0.014)]:
                for a in (-1, 1):
                    pts = spiral(u + a * r, mid, r, 0.030, -math.pi, a, 12 if lod else 22)
                    rail(
                        pts,
                        0.0027,
                        0.004,
                        f"{level} paired scrolls {i:02}",
                        GOLD if level == "upper" else IRON,
                    )
    for i, u in enumerate([span * 0.26, span * 0.72]):
        rail(
            bezier(
                (u, 0.150),
                [
                    ((u + 0.024, 0.25), (u - 0.026, 0.31), (u, 0.396)),
                    ((u + 0.033, 0.465), (u - 0.023, 0.56), (u + 0.004, 0.63)),
                    ((u + 0.014, 0.69), (u - 0.026, 0.745), (u, 0.797)),
                ],
                5 if lod else 10,
            ),
            0.0039,
            0.007,
            f"vine stem {i + 1}",
        )
        for j in range(5):
            hand = 1 if j % 2 == 0 else -1
            base = 0.204 + j * 0.125
            shoulder = (u + hand * 0.049, base + 0.065)
            sweep = bezier(
                (u, base),
                [((u + hand * 0.024, base + 0.003), (u + hand * 0.055, base + 0.029), shoulder)],
                4 if lod else 9,
            )
            rail(sweep, 0.0035, 0.006, f"vine {i + 1} branch {j + 1}")
            curls = spiral(
                shoulder[0] - hand * 0.022, shoulder[1], 0.022, 0.025, 0, hand, 12 if lod else 25
            )
            rail(curls, 0.005, 0.006, f"gilt scrolls {i + 1}", GOLD)
            tip = [
                (u + hand * 0.02, base + 0.020),
                (u + hand * 0.033, base + 0.032),
                (u + hand * 0.05, base + 0.036),
                (u + hand * 0.043, base + 0.023),
                (u + hand * 0.039, base + 0.021),
                (u + hand * 0.036, base + 0.014),
            ]
            b.prism(Polygon(tip), -0.003, 0.003, plane, GOLD, name + f" / gilt leaves {i + 1}")
    for j, z in enumerate([0.183, 0.733]):
        for k, (lo, hi) in enumerate([(z - 0.02, z + 0.002), (z + 0.008, z + 0.030)]):
            b.lathe(
                (sign * 0.487, 0.139),
                [(lo, 0.011), (lo + 0.004, 0.016), (hi - 0.003, 0.016), (hi, 0.011)],
                IRON,
                8 if lod else 14,
                name + f" / hinge knuckle {j + 1}.{k + 1}",
            )
    # Erect crest loops rise above the meeting ends; each leaf has its own serpentine outline.
    for j in range(3):
        u = span * (0.67 + 0.10 * j)
        rise = 0.032 + 0.01 * j
        pts = spiral(u, profile(u / span) + rise * 0.48, 0.020, rise, math.pi, 1, 14 if lod else 28)
        rail(pts, 0.0034, 0.0045, f"crest scroll {j + 1}", GOLD)
