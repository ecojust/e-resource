"""Open stone balustrades, the shallow splayed balconies and the carved entrance surround."""

import math
from shapely.geometry import box, Polygon
from stonework import BAYS, TERRACE, LIGHT, CHEEK, WARM, PALE, DARK, block, front, horizontal


def profile_post(b, x, y, low, high, r, lod, mat, name):
    rings = [
        (0, 0.92),
        (0.12, 0.92),
        (0.17, 0.64),
        (0.30, 0.58),
        (0.43, 0.83),
        (0.56, 1.0),
        (0.64, 0.99),
        (0.77, 0.63),
        (0.87, 0.57),
        (0.91, 0.86),
        (1, 0.87),
    ]
    if lod:
        rings = [rings[i] for i in (0, 2, 3, 5, 7, 9, 10)]
    # The photograph shows squared collars and a cut, tapering central body.
    n = 4 if lod else 8
    v = [
        (
            x + r * k * math.cos(2 * math.pi * j / n + math.pi / 4),
            y + r * k * math.sin(2 * math.pi * j / n + math.pi / 4),
            low + t * (high - low),
        )
        for t, k in rings
        for j in range(n)
    ]
    faces = [
        (i * n + j, i * n + (j + 1) % n, (i + 1) * n + (j + 1) % n, (i + 1) * n + j)
        for i in range(len(rings) - 1)
        for j in range(n)
    ]
    faces.extend([tuple(reversed(range(n))), tuple(range(n * (len(rings) - 1), n * len(rings)))])
    b.add(v, faces, mat, name)


def span(b, a, c, width, z0, z1, mat, name):
    dx, dy = c[0] - a[0], c[1] - a[1]
    h = math.hypot(dx, dy)
    nx, ny = -dy * width / (2 * h), dx * width / (2 * h)
    horizontal(
        b,
        Polygon(
            [
                (a[0] + nx, a[1] + ny),
                (c[0] + nx, c[1] + ny),
                (c[0] - nx, c[1] - ny),
                (a[0] - nx, a[1] - ny),
            ]
        ),
        z0,
        z1,
        mat,
        name,
    )


def railing(b, floor, index, x, lod):
    central = index == 1
    upper = floor == 2
    prefix = (
        ("Upper" if upper else "Middle")
        + " balcony / "
        + ("centre" if central else ("left" if index == 0 else "right"))
    )
    material = PALE if upper else CHEEK
    bottom = (12.96 if upper else 5.79) + TERRACE
    roof = (13.86 if upper else 7.03) + TERRACE
    half = (1.95 if upper else 2.05) if central else 1.76
    nose = (0.80 if upper else 1.07) if central else 0.37
    flat = half - (0.49 if central else 0.05)
    path = [(x - half, -0.10), (x - flat, -nose), (x + flat, -nose), (x + half, -0.10)]
    deck = Polygon([*path, (x + half, 0.10), (x - half, 0.10)])
    horizontal(
        b,
        deck.buffer(0.065, join_style=2),
        bottom - 0.12,
        bottom + 0.045,
        LIGHT,
        prefix + " / drip edge",
    )
    horizontal(b, deck, bottom + 0.035, bottom + 0.19, material, prefix + " / stone slab")
    lower = bottom + (0.27 if upper else 0.34)
    head = roof - (0.21 if upper else 0.25)
    for j, (a, c) in enumerate(zip(path, path[1:])):
        name = prefix + " / " + ("front" if j == 1 else "splayed cheek")
        span(b, a, c, 0.185, bottom + 0.12, lower, material, name + " / sill")
        span(b, a, c, 0.225, head, roof - 0.074, material, name + " / handrail")
        span(b, a, c, 0.254, roof - 0.074, roof, LIGHT, name + " / coping")
        length = math.dist(a, c)
        count = (9 if central else 11) if j == 1 else (1 if central else 0)
        end = 0.20 if j == 1 else 0.12
        if count:
            ux, uy = (c[0] - a[0]) / length, (c[1] - a[1]) / length
            for k in range(count):
                t = end + (length - 2 * end) * (k + 0.5) / count
                profile_post(
                    b,
                    a[0] + t * ux,
                    a[1] + t * uy,
                    lower - 0.002,
                    head + 0.002,
                    0.082 if upper else 0.091,
                    lod,
                    material,
                    name + " / turned stone balusters",
                )
        for t in [0, length] if j == 1 else [0, length] if central else [length / 2]:
            d = 0.32 if j == 1 else (0.20 if central else length)
            p0 = max(0, t - d / 2)
            p1 = min(length, t + d / 2)
            vertex = lambda q: (
                a[0] + (c[0] - a[0]) * q / length,
                a[1] + (c[1] - a[1]) * q / length,
            )
            span(b, vertex(p0), vertex(p1), 0.198, lower, head, material, name + " / solid jamb")
    if not upper and not central:
        front(
            b,
            box(x - 1.48, bottom - 0.90, x + 1.48, bottom - 0.18),
            -0.008,
            0.035,
            CHEEK,
            prefix + " / panel behind apron",
        )
        for a in [-1.36, -0.72, 0.72, 1.36]:
            block(
                b,
                x + a - 0.047,
                x + a + 0.047,
                -0.067,
                -0.007,
                bottom - 0.79,
                bottom - 0.23,
                LIGHT,
                prefix + " / apron mouldings",
            )
        block(
            b,
            x - 0.13,
            x + 0.13,
            -0.075,
            -0.01,
            bottom - 0.58,
            bottom - 0.37,
            LIGHT,
            prefix + " / centre square in apron",
        )


def portal(b, lod):
    floor = TERRACE
    head = 4.24 + floor
    for s in [-1, 1]:
        x = s * 1.32
        for outward, width, z0, z1, mat in [
            (0.19, 0.31, floor, head + 0.37, WARM),
            (0.34, 0.21, floor, head + 0.25, CHEEK),
            (0.38, 0.087, floor, head + 0.13, LIGHT),
        ]:
            mid = x + s * (width / 2 + 0.012)
            block(
                b,
                mid - width / 2,
                mid + width / 2,
                -outward,
                -0.014,
                z0,
                z1,
                mat,
                "Central portal / nested stone jamb",
            )
        for n in range(4):
            z = head - 0.1 - n * 0.26
            block(
                b,
                s * 1.57 - 0.061,
                s * 1.57 + 0.061,
                -0.32,
                -0.18,
                z,
                z + 0.12,
                LIGHT,
                "Central portal / stepped jamb ornament",
            )
    for width, y, z0, z1, mat, label in [
        (3.17, -0.27, head, head + 0.36, CHEEK, "fluted lintel"),
        (3.42, -0.35, head + 0.36, head + 0.47, LIGHT, "lintel bead"),
        (3.56, -0.43, head + 0.47, head + 0.70, WARM, "carved frieze"),
        (3.70, -0.48, head + 0.70, head + 0.80, LIGHT, "top bead"),
        (3.82, -0.55, head + 0.80, head + 0.88, CHEEK, "cavetto face"),
        (4.0, -0.62, head + 0.88, head + 1.04, LIGHT, "upper coping"),
    ]:
        block(b, -width / 2, width / 2, y, 0.015, z0, z1, mat, "Central portal / " + label)
    for k in range(19):
        x = (k - 9) * 0.127
        block(
            b,
            x - 0.025,
            x + 0.025,
            -0.302,
            -0.268,
            head + 0.034,
            head + 0.325,
            LIGHT,
            "Central portal / fluted lintel ribs",
        )
    for k in range(12):
        x = (k - 5.5) * 0.27
        for dx in [-1, 1]:
            p = Polygon(
                [
                    (x, head + 0.53),
                    (x + dx * 0.135, head + 0.66),
                    (x + dx * 0.135, head + 0.70),
                    (x, head + 0.57),
                ]
            )
            front(b, p, -0.452, -0.425, CHEEK, "Central portal / chevron carving")
