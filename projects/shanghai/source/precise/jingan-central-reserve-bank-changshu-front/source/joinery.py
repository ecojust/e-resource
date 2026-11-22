"""Rebated timber sashes, individually mapped pane fields and the pair of panelled entrance doors."""

import math
from shapely.geometry import box
from shapely.ops import unary_union
from stonework import GLASS, WOOD, DOOR, PANEL, METAL, SHADE, HALF, TERRACE, block


def pane(b, mapper, rect, depth, mat, label):
    x0, z0, x1, z1 = rect
    corners = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    # The local plane has its positive normal towards the garden.
    b.add([mapper(x, z, depth) for x, z in corners], [(0, 1, 2), (0, 2, 3)], mat, label)
    tile = GLASS.index(mat)
    left = (tile * 64 + 0.5) / 320
    right = (tile * 64 + 63.5) / 320
    b.parts[-1]["texcoords"] = [(left, 0.992), (right, 0.992), (right, 0.008), (left, 0.008)]


def sash(b, mapper, floor, bay, width, sill, head, side, lod):
    h = head - sill
    l = -width / 2
    r = width / 2
    rim = 0.09
    prefix = ("East return" if side else "Garden") + f" / level {floor + 1} sash {bay + 1}"
    material = (
        GLASS[0]
        if floor == 0
        else (GLASS[2] if bay == 1 else GLASS[1])
        if floor == 1
        else (GLASS[4] if bay == 2 else GLASS[3])
    )
    # Each unit has three principal leaves. Fine glazing bars subdivide the
    # centre light; the two side lights are wider, unobstructed curtain fields.
    div = [l, l + width * 0.233, r - width * 0.233, r]
    coarse = [
        box(l, sill, l + rim, head),
        box(r - rim, sill, r, head),
        box(l, sill, r, sill + rim),
        box(l, head - rim, r, head),
    ]
    for u in div[1:3]:
        coarse.append(box(u - 0.055, sill, u + 0.055, head))
    rail = sill + h * (0.70 if floor != 2 else 0.73)
    coarse.append(box(l, rail - 0.047, r, rail + 0.047))
    rails = [rail]
    if floor == 1:
        rails.append(sill + h * 0.48)
        coarse.append(box(div[1], rails[-1] - 0.043, div[2], rails[-1] + 0.043))
    b.prism(unary_union(coarse), -0.205, -0.10, mapper, WOOD, prefix + " / outer frame and transom")
    for j, (a, c) in enumerate(zip(div, div[1:])):
        va = a + (rim if j == 0 else 0.045)
        vc = c - (rim if j == 2 else 0.045)
        zs = sorted([sill + rim, head - rim, *(rails if j == 1 else [rail])])
        for n, (z0, z1) in enumerate(zip(zs, zs[1:])):
            use = (
                GLASS[2] if floor == 1 and (n == len(zs) - 2 or (bay == 1 and j != 1)) else material
            )
            pane(b, mapper, (va, z0, vc, z1), -0.263, use, prefix + " / recessed glass")
        if j != 1:
            continue
        thin = []
        for n in range(1, 4):
            u = va + (vc - va) * n / 4
            thin.append(box(u - 0.018, sill + rim, u + 0.018, rail - 0.024))
        if floor == 1 or not lod:
            for n in range(1, 3 if floor == 1 else 2):
                z = sill + rim + (rail - sill - rim) * n / (3 if floor == 1 else 2)
                thin.append(box(va, z - 0.016, vc, z + 0.016))
        if thin:
            b.prism(
                unary_union(thin), -0.254, -0.217, mapper, WOOD, prefix + " / slender glazing bars"
            )


def door(b, lod):
    frame_width = 2.60
    for sign in (-1, 1):
        u = sign * (frame_width / 2 - 0.047)
        block(
            b,
            u - 0.047,
            u + 0.047,
            0.11,
            0.27,
            TERRACE,
            TERRACE + 4.23,
            WOOD,
            "Entry / fixed reveal frame",
        )
    block(b, -1.30, 1.30, 0.11, 0.27, TERRACE + 4.10, TERRACE + 4.24, WOOD, "Entry / frame head")
    # The 2018 view shows the door open. The independent closed view records
    # the two-leaf layout and panels. Opening angle is an estimate.
    for sign in (-1, 1):
        theta = math.radians(67 if sign < 0 else 73)
        hinge = 1.23 * sign
        dx = -sign * math.cos(theta)
        dy = math.sin(theta)
        # Panel u increases from the hinge into the opening. Adapt the
        # horizontal axis on the right leaf so prism extrusion stays right-handed.
        vx, vy = (dx, dy) if sign < 0 else (-dx, -dy)

        def mp(u, z, d):
            return (hinge + vx * u + vy * d, 0.24 + vy * u - vx * d, z)

        a, c = (0, 1.217) if sign < 0 else (-1.217, 0)
        z0 = TERRACE + 0.055
        z1 = TERRACE + 4.08
        panel_shape = box(a, z0, c, z1)
        b.prism(panel_shape, -0.09, -0.015, mp, DOOR, "Entry / open panelled door leaf")
        if lod:
            continue
        for lo, hi in [(z0 + 0.24, z0 + 1.00), (z0 + 1.20, z0 + 2.02), (z0 + 2.24, z1 - 0.22)]:
            shape = box(a + 0.14, lo, c - 0.14, hi)
            b.prism(shape, -0.015, 0.001, mp, PANEL, "Entry / recessed panels")
            b.prism(
                shape.buffer(0.026, join_style=2).difference(shape),
                -0.016,
                0.025,
                mp,
                DOOR,
                "Entry / moulded panel edges",
            )
        u = a + 0.16 if sign > 0 else c - 0.16
        b.prism(
            box(u - 0.027, z0 + 1.25, u + 0.027, z0 + 1.47),
            -0.005,
            0.060,
            mp,
            METAL,
            "Entry / bronze handle",
        )
    block(
        b,
        -1.30,
        1.30,
        2.78,
        2.86,
        TERRACE,
        4.24 + TERRACE,
        SHADE,
        "Entry / shaded limit of visible vestibule",
    )
    block(
        b,
        -1.30,
        1.30,
        0.36,
        2.81,
        TERRACE - 0.03,
        TERRACE,
        SHADE,
        "Entry / floor of shallow reveal",
    )
    # These three surfaces prevent exterior sky showing through the sides or
    # overhead when viewing the documented open doorway from the garden.
    for side in (-1, 1):
        x = 1.30 * side
        block(
            b,
            x - 0.035,
            x + 0.035,
            0.26,
            2.85,
            TERRACE,
            TERRACE + 4.24,
            SHADE,
            "Entry / shaded side return",
        )
    block(
        b,
        -1.33,
        1.33,
        0.25,
        2.86,
        TERRACE + 4.10,
        TERRACE + 4.25,
        SHADE,
        "Entry / shaded underside of lintel return",
    )
