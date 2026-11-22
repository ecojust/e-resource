"""Ashlar, recessed openings, projecting cornices and low steps of the Changshu Road house.

Local X is right in the garden photograph. Y increases into the house. All heights
are metres above the garden paving; the principal entrance terrace is 0.42 m up.
"""

from pathlib import Path
import math
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

SOURCE = Path(__file__).resolve().parent
HALF = 16.111300836 / 2
TERRACE = 0.42
RETURN = 4.22
BAYS = (-5.14, 0.0, 5.14)
WARM = "Warm grey cut stone"
PALE = "Pale upper-storey ashlar"
HONEY = "Buff-grey alternate course"
COLD = "Silver-grey stone return"
JOINT = "Shadowed stone bed"
LIGHT = "Pale dressed ledge"
DARK = "Grey granite basement"
CHEEK = "Portal cut-stone trim"
WOOD = "Brown window joinery"
DOOR = "Dark honey-brown door"
PANEL = "Deep-set door panels"
METAL = "Dark bronze fittings"
SHADE = "Shadow inside open entry"
GLASS = [
    "Ground brown curtain",
    "Pale drape",
    "Reflected winter branches",
    "Upper grey curtain",
    "Upper brown curtain",
]


def finish(rgb, rough=0.80, metal=0):
    def linear(value):
        v = value / 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

    return dict(color=[linear(x) for x in rgb], roughness=rough, metallic=metal)


PALETTE = {
    WARM: finish((170, 158, 137)),
    PALE: finish((192, 190, 181)),
    HONEY: finish((175, 162, 140)),
    COLD: finish((177, 176, 167)),
    JOINT: finish((122, 116, 107)),
    LIGHT: finish((204, 196, 178)),
    DARK: finish((133, 127, 113)),
    CHEEK: finish((189, 176, 151)),
    WOOD: finish((64, 51, 47), 0.53),
    DOOR: finish((115, 71, 48), 0.54),
    PANEL: finish((93, 58, 40), 0.58),
    METAL: finish((94, 84, 65), 0.43, 0.43),
    SHADE: finish((49, 46, 42)),
}
for material in GLASS:
    PALETTE[material] = dict(
        color=[1, 1, 1], roughness=0.47, metallic=0.08, texture=str(SOURCE / "window-samples.png")
    )


def block(b, x0, x1, y0, y1, z0, z1, mat, name):
    b.box(
        ((x1 + x0) / 2, (y1 + y0) / 2, (z1 + z0) / 2), (x1 - x0, y1 - y0, z1 - z0), mat, label=name
    )


def horizontal(b, polygon, low, high, mat, name):
    b.prism(polygon, low, high, lambda x, y, z: (x, y, z), mat, name)


def front(b, shape, out, back, mat, name):
    b.prism(shape, -back, -out, lambda x, z, d: (x, -d, z), mat, name)


def storey_windows():
    # Sills behind the balustrades extend down to the balcony floor, as seen
    # through the gaps. The upper and middle central units are taller casements.
    for floor, (sill, head) in enumerate([(1.17, 4.29), (6.05, 10.40), (13.15, 15.89)]):
        for i, x in enumerate(BAYS):
            if floor == 0 and i == 1:
                continue
            yield floor, i, x, 3.13, sill + TERRACE, head + TERRACE


def return_windows():
    return [
        (floor, 2.06, width, sill + TERRACE, head + TERRACE)
        for floor, width, sill, head in [
            (0, 2.23, 1.17, 4.29),
            (1, 2.44, 6.47, 10.40),
            (2, 2.44, 13.15, 15.89),
        ]
    ]


def walls(b, lod):
    holes = [box(x - w / 2, sill, x + w / 2, head) for _, _, x, w, sill, head in storey_windows()]
    holes.append(box(-1.30, TERRACE - 0.01, 1.30, 4.24 + TERRACE))
    wall = box(-HALF, TERRACE, HALF, 17.76 + TERRACE).difference(unary_union(holes))
    front(b, wall, 0.025, 0.44, JOINT, "Garden front / masonry bed with cut-through reveals")

    def facade_section(s0, s1, z0, z1):
        return wall.intersection(box(s0, z0, s1, z1))

    stages = [
        (0.00, 1.0, 0.50),
        (1, 4.36, 0.67),
        (4.36, 6.35, 0.67),
        (6.35, 10.47, 0.68),
        (10.47, 12.65, 0.73),
        (12.65, 15.93, 0.65),
        (15.93, 17.76, 0.61),
    ]
    for stage, (low, high, nominal) in enumerate(stages):
        nz = round((high - low) / nominal)
        upper = low >= 12.65
        for row in range(nz):
            z0 = TERRACE + low + (high - low) * row / nz
            z1 = TERRACE + low + (high - low) * (row + 1) / nz
            # Pilaster joints run to the corners of each casement. The recessed
            # field blocks break bond on alternating rows.
            bounds = [-HALF, -6.82, -3.53, -2.91, -2.15, -1.56, 1.56, 2.15, 2.91, 3.53, 6.82, HALF]
            if not lod and row % 2 == 0:
                bounds = sorted([*bounds, -5.18, 0, 5.18])
            for j, (a, c) in enumerate(zip(bounds, bounds[1:])):
                prominent = (
                    a <= -6.82 or c >= 6.82 or -2.91 <= a < c <= -2.15 or 2.15 <= a < c <= 2.91
                )
                pad = 0.012 if not lod else 0.016
                tile = facade_section(a + pad, c - pad, z0 + 0.012, z1 - 0.012)
                if tile.area < 0.002:
                    continue
                color = (PALE if upper else WARM) if (j + row) % 5 else (COLD if upper else HONEY)
                front(
                    b,
                    tile,
                    -(0.083 if prominent else 0.021),
                    0.036,
                    color,
                    f"Garden front / stone course {stage + 1}.{row + 1}",
                )
    rholes = [box(u - w / 2, lo, u + w / 2, hi) for _, u, w, lo, hi in return_windows()]
    for sign, side in [(-1, "West"), (1, "East")]:
        # Only the east return is identifiable in the two obliques. The west
        # return closes the cut through the known footprint, without invented windows.
        shape = box(0, TERRACE, RETURN, 17.76 + TERRACE)
        if sign == 1:
            shape = shape.difference(unary_union(rholes))
        mapper = (
            (lambda u, z, d: (HALF + d, u, z))
            if sign > 0
            else (lambda u, z, d: (-HALF - d, RETURN - u, z))
        )
        b.prism(shape, -0.40, 0, mapper, COLD, side + " return / stone skin")
        for row in range(26):
            z0 = TERRACE + row * 17.76 / 26
            z1 = TERRACE + (row + 1) * 17.76 / 26
            span = shape.intersection(box(0.015, z0 + 0.012, RETURN - 0.015, z1 - 0.012))
            if span.area > 0.001:
                b.prism(
                    span,
                    -0.012,
                    0.021,
                    mapper,
                    PALE if row >= 19 else WARM,
                    side + " return / ashlar courses",
                )
    footing = box(-HALF, 0.12, HALF, RETURN).difference(box(-1.30, 0, 1.30, 2.81))
    horizontal(
        b,
        footing,
        TERRACE,
        1.05 + TERRACE,
        DARK,
        "Entrance block / foundation around recessed threshold",
    )

    # The garden photograph shows a thick projecting sill and a darker lower
    # return below the two ground-floor curtains.
    for x in (BAYS[0], BAYS[2]):
        block(
            b,
            x - 1.68,
            x + 1.68,
            -0.207,
            0.07,
            TERRACE + 0.94,
            TERRACE + 1.17,
            LIGHT,
            "Garden front / projecting ground window sills",
        )
        block(
            b,
            x - 1.58,
            x + 1.58,
            -0.094,
            0.04,
            TERRACE + 0.77,
            TERRACE + 0.94,
            DARK,
            "Garden front / sub-sill shadow band",
        )


def ledge(b, top, width, projection, name, lod):
    # U-shaped cornice follows the garden face and the two short returns.
    def outline(d):
        return Polygon(
            [
                (-width - d, -d),
                (width + d, -d),
                (width + d, RETURN),
                (width - 0.18, RETURN),
                (width - 0.18, 0.18),
                (-width + 0.18, 0.18),
                (-width + 0.18, RETURN),
                (-width - d, RETURN),
            ]
        )

    for low, high, depth, mat, lab in [
        (-0.45, -0.31, projection * 0.37, WARM, "stone architrave"),
        (-0.31, -0.23, projection * 0.54, DARK, "drip groove"),
        (-0.23, -0.12, projection * 0.79, LIGHT, "lower fascia"),
        (-0.12, 0, projection, LIGHT, "square cap"),
    ]:
        horizontal(b, outline(depth), top + low, top + high, mat, name + " / " + lab)
    for i in range(48):
        x = -width + 0.19 + (width * 2 - 0.38) * i / 47
        block(
            b,
            x - 0.045,
            x + 0.045,
            -0.145,
            -0.062,
            top - 1.05,
            top - 0.44,
            PALE if top > 16 else CHEEK,
            name + " / relief under eaves",
        )
    for end in [-1, 1]:
        for i in range(1, 13 if not lod else 9):
            y = RETURN * i / (13 if not lod else 9)
            x = end * width
            block(
                b,
                min(x, x + end * 0.092),
                max(x, x + end * 0.092),
                y - 0.04,
                y + 0.04,
                top - 1.05,
                top - 0.44,
                PALE,
                name + " / return relief",
            )


def podium(b, lod):
    for j in range(3):
        width = 9.72 - 0.23 * j
        block(
            b,
            -width / 2,
            width / 2,
            -3.05 + j * 0.38,
            -0.01,
            j * 0.14,
            (j + 1) * 0.14,
            LIGHT if j == 2 else DARK,
            "Garden / three terrace risers",
        )
    block(b, -HALF, HALF, -0.55, 0.32, 0, TERRACE, DARK, "Garden / plinth at the projecting front")
    for side in (-1, 1):
        x = 4.86 * side
        block(b, x - 0.23, x + 0.23, -2.76, -0.16, 0.10, 0.56, CHEEK, "Garden / flank of steps")
        block(b, x - 0.29, x + 0.29, -2.8, -2.27, 0.10, 0.9, WARM, "Garden / low end post")
        block(b, x - 0.31, x + 0.31, -2.82, -2.24, 0.87, 0.94, LIGHT, "Garden / low post cap")


def crown(b, lod):
    ledge(b, 12.98 + TERRACE, HALF, 0.86, "Middle cornice", lod)
    ledge(b, 18.05 + TERRACE, HALF, 0.90, "Upper cornice", lod)
    block(
        b,
        -HALF - 0.88,
        HALF + 0.88,
        -0.88,
        RETURN,
        17.96 + TERRACE,
        18.05 + TERRACE,
        LIGHT,
        "Upper cornice / terrace closure",
    )
    for width, y0, low, hi, material, title in [
        (6.0, 0.56, 18.05, 19.13, COLD, "short attic base"),
        (6.12, 0.49, 19.13, 19.25, LIGHT, "attic coping"),
        (3.13, 0.72, 19.25, 19.57, PALE, "attic first step"),
        (2.45, 0.79, 19.57, 19.78, PALE, "attic second step"),
        (1.80, 0.84, 19.78, 20.03, PALE, "upper rectangular crown"),
    ]:
        block(
            b,
            -width / 2,
            width / 2,
            y0,
            2.0,
            low + TERRACE,
            hi + TERRACE,
            material,
            "Terrace / " + title,
        )
