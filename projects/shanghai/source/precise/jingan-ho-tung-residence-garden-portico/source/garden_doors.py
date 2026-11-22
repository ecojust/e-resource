"""Garden thresholds, the three arch-headed doors and the recessed iron balcony."""

import math
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from ionic_garden import (
    BASE,
    HALF,
    WALL_Y,
    RETURN_Y,
    STONE,
    LIGHT,
    BELT,
    FLOOR,
    WALL,
    WOOD,
    FRAME,
    IRON,
    GLASS,
    FAN,
)

BAYS = (-2.8134353, 0, 2.8134353)
RADIUS = 0.623
CROWN = 2.8466397
SPRING = CROWN - RADIUS
SLAB = 4.235


def front(b, shape, y0, y1, mat, name):
    b.prism(shape, -y1, -y0, lambda x, z, d: (x, -d, z), mat, name)


def semicircle(x, z, r, steps):
    return [
        (x + r * math.cos(math.pi * i / steps), z + r * math.sin(math.pi * i / steps))
        for i in range(steps + 1)
    ]


def arch(x, r, bottom, lod):
    return Polygon([(x - r, bottom), (x + r, bottom)] + semicircle(x, SPRING, r, 12 if lod else 30))


def platform(b, lod):
    # Three low rises. The elliptical front sweeps around both end column bases.
    n = 18 if lod else 42
    for i in range(3):
        rx = 5.53 - 0.115 * i
        ry = 1.38 - 0.145 * i
        arc = [
            (rx * math.cos(math.pi * j / n), 0.52 - ry * math.sin(math.pi * j / n))
            for j in range(n + 1)
        ]
        outline = Polygon(
            arc
            + [
                (-rx, RETURN_Y),
                (-HALF, RETURN_Y),
                (-HALF, 4.26),
                (HALF, 4.26),
                (HALF, RETURN_Y),
                (rx, RETURN_Y),
            ]
        )
        b.plan_prism(outline, 0.085 * i, 0.085 * (i + 1), FLOOR, f"Curved garden step {i + 1}")


def masonry(b, lod):
    ground = [arch(x, RADIUS, BASE - 0.01, lod) for x in BAYS]
    upper = [box(x - 0.62, SLAB - 0.012, x + 0.62, 6.34) for x in BAYS]
    rear = box(-HALF, BASE, HALF, 7.79).difference(unary_union(ground + upper))
    front(b, rear, WALL_Y, WALL_Y + 0.31, WALL, "Pierced two-storey garden wall")
    # The faces at right angles to the arcade have their own narrow arches.
    for sign in (-1, 1):
        # Coordinates progress into the garden on the left and into the house on the right.
        mapper = lambda u, z, d, s=sign: (s * (HALF - d), -s * u, z)
        mid = -sign * (RETURN_Y + 0.84)
        low, high = sorted((-sign * RETURN_Y, -sign * (WALL_Y + 0.31)))
        opening = arch(mid, 0.51, BASE - 0.01, lod)
        shape = box(low, BASE, high, 7.72).difference(opening)
        b.prism(shape, 0, 0.24, mapper, WALL, "Pierced short inner return")
        b.prism(opening, 0.018, 0.045, mapper, GLASS[2], "Return door recessed glass")
        for u in (mid - 0.48, mid, mid + 0.48):
            b.tube(
                [mapper(u, 0.29, 0.06), mapper(u, SPRING, 0.06)],
                0.028,
                WOOD,
                5 if lod else 8,
                "Return door glazing bar",
            )
        for z in (0.80, 1.28, 1.76, SPRING):
            b.tube(
                [mapper(mid - 0.48, z, 0.061), mapper(mid + 0.48, z, 0.061)],
                0.022,
                WOOD,
                5 if lod else 8,
                "Return door crossbar",
            )
        b.tube(
            [mapper(u, z, 0.075) for u, z in semicircle(mid, SPRING, 0.488, 10 if lod else 20)],
            0.027,
            WOOD,
            5 if lod else 8,
            "Return door fanlight",
        )
        # The narrow return reads as a stone pier at the portico-wing junction.
        b.box(
            (sign * (HALF - 0.12), RETURN_Y + 0.065, 3.61),
            (0.35, 0.23, 6.71),
            STONE,
            label="Wing junction pilaster",
        )
        b.box(
            (sign * (HALF - 0.12), RETURN_Y + 0.05, 6.96),
            (0.47, 0.32, 0.17),
            LIGHT,
            label="Wing junction impost",
        )


def leaf(b, x, level, side, y, angle, lod, label):
    sill, top = (BASE + 0.027, SPRING - 0.042) if level == 0 else (SLAB + 0.033, 6.316)
    width = RADIUS - 0.037
    # u advances from hinge to meeting stile. The central pair opens inward.
    direction = (-side * math.cos(angle), math.sin(angle), 0)
    normal = (side * math.sin(angle), math.cos(angle), 0)
    hinge = x + side * (RADIUS - 0.029)

    def put(u, z, d, w, h, depth, mat, name):
        origin = (hinge + u * direction[0] + normal[0] * d, y + u * direction[1] + normal[1] * d, z)
        b.box(origin, (w, depth, h), mat, (direction, normal, (0, 0, 1)), label + " " + name)

    for u in (0.025, width - 0.025):
        put(u, (top + sill) / 2, 0, 0.050, top - sill, 0.052, WOOD, "stile")
    rows = 4 if level == 0 else 3
    step = (top - sill) / rows
    for i in range(rows + 1):
        z = sill + i * step
        put(width / 2, z, 0, width, 0.050, 0.053, WOOD, "horizontal rail")
    put(width / 2, (sill + top) / 2, 0, 0.021, top - sill, 0.038, WOOD, "fine glazing bar")
    for row in range(rows):
        for col in range(2):
            span = (width - 0.074) / 2
            u = 0.037 + span * (col + 0.5)
            put(
                u,
                sill + step * (row + 0.5),
                0.012,
                span - 0.016,
                step - 0.05,
                0.016,
                GLASS[(int(level == 1) * 2 + (row + col) % 2) % 3],
                "inset pane",
            )
    if not lod:
        put(width - 0.083, sill + 0.85, -0.038, 0.016, 0.12, 0.036, FRAME, "door pull")


def fenestration(b, lod):
    for i, x in enumerate(BAYS):
        ground = arch(x, RADIUS, BASE, lod)
        border = arch(x, RADIUS + 0.11, BASE, lod).difference(ground)
        front(b, border, WALL_Y - 0.073, WALL_Y + 0.034, LIGHT, "Architrave of garden door")
        frame = ground.difference(arch(x, RADIUS - 0.046, BASE, lod))
        front(b, frame, WALL_Y + 0.016, WALL_Y + 0.105, WOOD, "French door arched frame")
        fan = Polygon(semicircle(x, SPRING, RADIUS - 0.042, 12 if lod else 28))
        front(b, fan, WALL_Y + 0.085, WALL_Y + 0.105, FAN, "Fanlight recessed glazing")
        for r in (RADIUS - 0.03, RADIUS * 0.53):
            path = [(a, WALL_Y + 0.055, z) for a, z in semicircle(x, SPRING, r, 12 if lod else 26)]
            b.tube(
                path,
                0.017 if r < 0.4 else 0.025,
                WOOD,
                5 if lod else 8,
                "Semicircular fanlight glazing bar",
            )
        for k in range(1, 6):
            a = k * math.pi / 6
            b.tube(
                [
                    (x, WALL_Y + 0.05, SPRING),
                    (
                        x + (RADIUS - 0.036) * math.cos(a),
                        WALL_Y + 0.05,
                        SPRING + (RADIUS - 0.036) * math.sin(a),
                    ),
                ],
                0.016,
                WOOD,
                5 if lod else 8,
                "Radial fanlight glazing bar",
            )
        # Slim inner glazing beads can also be seen in the photograph looking out.
        back_y = WALL_Y + 0.117
        inner_arc = semicircle(x, SPRING, RADIUS * 0.53, 12 if lod else 26)
        b.tube(
            [(u, back_y, z) for u, z in inner_arc],
            0.011,
            FRAME,
            5 if lod else 7,
            "Fanlight inner curved bead",
        )
        for k in range(1, 6):
            a = k * math.pi / 6
            b.tube(
                [
                    (x, back_y, SPRING),
                    (
                        x + (RADIUS - 0.036) * math.cos(a),
                        back_y,
                        SPRING + (RADIUS - 0.036) * math.sin(a),
                    ),
                ],
                0.010,
                FRAME,
                5 if lod else 7,
                "Fanlight inner radial bead",
            )
        b.box(
            (x, WALL_Y + 0.061, SPRING),
            (2 * RADIUS, 0.085, 0.075),
            WOOD,
            label="French door transom",
        )
        surround = box(x - 0.709, SLAB - 0.02, x + 0.709, 6.43).difference(
            box(x - 0.62, SLAB - 0.03, x + 0.62, 6.34)
        )
        front(b, surround, WALL_Y - 0.052, WALL_Y + 0.034, LIGHT, "Upper opening stone surround")
        for level in (0, 1):
            for side in (-1, 1):
                angle = math.radians(70) if i == 1 and level == 0 else 0.0
                leaf(
                    b,
                    x,
                    level,
                    side,
                    WALL_Y + 0.076,
                    angle,
                    lod,
                    f"{'Upper' if level else 'Ground'} bay {i + 1} {'left' if side < 0 else 'right'} leaf",
                )


def balcony(b, lod):
    path = [(-4.95, 2.79), (-2.32, 2.18), (2.32, 2.18), (4.95, 2.79)]
    balcony = Polygon(path + [(4.95, WALL_Y + 0.08), (-4.95, WALL_Y + 0.08)])
    b.plan_prism(balcony, SLAB - 0.22, SLAB - 0.07, STONE, "Faceted balcony slab")
    b.plan_prism(
        balcony.buffer(0.036, join_style="mitre"), SLAB - 0.07, SLAB, LIGHT, "Balcony nosing"
    )
    for x in (-3.76, -1.63, 1.63, 3.76):
        side = Polygon(
            [
                (2.62, SLAB - 0.22),
                (WALL_Y, SLAB - 0.22),
                (WALL_Y, SLAB - 0.83),
                (3.57, SLAB - 0.68),
                (3.46, SLAB - 0.53),
                (3.14, SLAB - 0.39),
            ]
        )
        b.prism(side, x - 0.09, x + 0.09, lambda y, z, x: (x, y, z), STONE, "Balcony stone console")
    rail = [(-4.95, WALL_Y), *path, (4.95, WALL_Y)]
    for (ax, ay), (bx, by) in zip(rail, rail[1:]):
        length = math.hypot(bx - ax, by - ay)

        def point(t, z):
            return (ax + (bx - ax) * t, ay + (by - ay) * t, z)

        for z, r in [(4.34, 0.022), (4.44, 0.016), (5.112, 0.020), (5.225, 0.034)]:
            b.tube([point(0, z), point(1, z)], r, IRON, 6 if lod else 10, "Iron balcony rail")
        panels = max(1, round(length / 0.68))
        for j in range(panels):
            t = j / panels
            b.tube(
                [point(t, SLAB), point(t, 5.23)],
                0.024,
                IRON,
                6 if lod else 8,
                "Balcony iron standard",
            )
            for k in (1, 2, 3):
                pos = (j + k / 4) / panels
                b.tube(
                    [point(pos, 4.41), point(pos, 5.14)],
                    0.011,
                    IRON,
                    5 if lod else 7,
                    "Balcony iron picket",
                )
            # A closed curved lozenge in each panel sits behind its straight pickets.
            n = 10 if lod else 20
            loop = [
                point(
                    (j + 0.5 + 0.32 * math.cos(math.tau * i / n)) / panels,
                    4.775 + 0.246 * math.sin(math.tau * i / n),
                )
                for i in range(n + 1)
            ]
            b.tube(loop, 0.013, IRON, 5 if lod else 7, "Balcony iron oval")
    b.tube([(*rail[-1], SLAB), (*rail[-1], 5.23)], 0.024, IRON, 7, "Balcony end standard")
