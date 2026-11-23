"""Running-bond brickwork, punched sash openings, window surrounds and the pair of upright conduits."""

import math
from shapely.geometry import box
from portal_stone import panel, front
from lane_gate import PAINT, GLASS

BRICK = ("Weathered red face brick", "Brown red face brick", "Muted terracotta face brick")
MORTAR = "Grey lime mortar"
SILL = "Weathered dark stone window sill"
PIPE = "Dull galvanized pipe"
PANE = "Upper window shaded glass"


def sash(b, x, d, lod, label):
    width = d["window_width"]
    bottom, top = d["window_sill"], d["window_head"]
    west, east = x - width / 2, x + width / 2
    panel(
        b,
        west - 0.046,
        east + 0.046,
        bottom - 0.047,
        bottom + 0.012,
        0.22,
        0.55,
        SILL,
        label + " sill",
    )
    panel(
        b,
        west - 0.028,
        east + 0.028,
        top - 0.008,
        top + 0.081,
        0.234,
        0.54,
        SILL,
        label + " projecting head",
    )
    bar = 0.039
    transom = bottom + (top - bottom) * 0.72
    for u in (west, east - bar):
        panel(b, u, u + bar, bottom, top, 0.352, 0.459, PAINT, label + " side frame")
    for v in (bottom, transom, top - bar):
        panel(
            b, west + bar, east - bar, v, v + bar, 0.352, 0.459, PAINT, label + " horizontal sash"
        )
    panel(
        b,
        x - 0.014,
        x + 0.014,
        bottom + bar,
        transom,
        0.375,
        0.445,
        PAINT,
        label + " casement meeting rail",
    )
    for i, (a, c) in enumerate(((west + bar, x - 0.014), (x + 0.014, east - bar))):
        panel(b, a, c, bottom + bar, transom, 0.413, 0.426, GLASS, label + " casement glass")
        if not lod:
            panel(
                b, a, a + 0.013, bottom + bar, transom, 0.392, 0.413, PAINT, label + " glazing bead"
            )
    panel(
        b,
        west + bar,
        east - bar,
        transom + bar,
        top - bar,
        0.413,
        0.426,
        PANE,
        label + " transom glass",
    )


def upper_front(b, d, lod):
    west = d["stone_center_x"] - d["stone_width"] / 2
    east = west + d["stone_width"]
    bottom, top = d["crown"] - 0.105, d["wall_top"]
    window_x = d["window_centres"]
    wall = box(west, bottom, east, top)
    openings = []
    for x in window_x:
        opening = box(
            x - d["window_width"] / 2, d["window_sill"], x + d["window_width"] / 2, d["window_head"]
        )
        wall = wall.difference(opening)
        openings.append(opening)
    front(b, wall, 0.321, 0.60, MORTAR, "Upper common wall with two window reveals")
    # The face units share a recessed mortar bed cut through at both windows.
    height = 0.072
    length = 0.217
    for course in range(math.ceil((top - bottom) / height)):
        low = bottom + course * height + 0.0045
        high = min(top, low + height - 0.009)
        if high - low < 0.005:
            continue
        offset = -length / 2 if course % 2 else 0
        for col in range(math.ceil((east - west) / length) + 2):
            x0 = max(west, west + col * length + offset + 0.0045)
            x1 = min(east, west + (col + 1) * length + offset - 0.0045)
            if x1 - x0 < 0.007:
                continue
            shape = box(x0, low, x1, high)
            for hole in openings:
                if hole.intersects(shape):
                    shape = shape.difference(hole)
            if shape.area < 0.00006:
                continue
            material = BRICK[(col * 13 + course * 7 + col * course) % len(BRICK)]
            if lod:
                # Keep the observed bond at distance as single front quads.
                for piece in [shape] if shape.geom_type == "Polygon" else shape.geoms:
                    if piece.geom_type != "Polygon" or piece.area < 0.00006:
                        continue
                    from shapely import constrained_delaunay_triangles
                    from shapely.geometry.polygon import orient

                    for tri in constrained_delaunay_triangles(piece).geoms:
                        coords = list(orient(tri, sign=1).exterior.coords)[:3]
                        b.add(
                            [(x, 0.303, z) for x, z in coords],
                            [(0, 1, 2)],
                            material,
                            "Upper street brick bond",
                        )
            else:
                front(b, shape, 0.301, 0.326, material, "Upper street brick bond")
    for i, x in enumerate(window_x):
        sash(b, x, d, lod, ("West" if i == 0 else "East") + " upper window")
    # Two light pipes are seen between the two upper windows in the close street view.
    for i, x in enumerate(d["pipe_centres"]):
        b.lathe(
            (x, 0.253),
            [(d["crown"] - 0.005, 0.016), (top, 0.016)],
            PIPE,
            8 if lod else 16,
            "Vertical metal conduit " + str(i + 1),
        )
        for z in (d["crown"] + 0.34, top - 0.22):
            panel(
                b, x - 0.026, x + 0.026, z - 0.011, z + 0.011, 0.233, 0.322, PIPE, "Conduit saddle"
            )


def street_plates(b, d):
    west = d["stone_center_x"] - d["stone_width"] / 2
    x = (west + d["opening_center_x"] - d["clear_width"] / 2) / 2
    for z, w, h, mat in (
        (2.77, 0.41, 0.17, "Ochre street plate"),
        (2.05, 0.40, 0.29, "Pale enamel plate"),
    ):
        panel(
            b,
            x - w / 2,
            x + w / 2,
            z - h / 2,
            z + h / 2,
            -0.012,
            0.035,
            mat,
            "West jamb street plate",
        )
        for u in (x - w * 0.42, x + w * 0.42):
            for v in (z - h * 0.34, z + h * 0.34):
                panel(
                    b,
                    u - 0.007,
                    u + 0.007,
                    v - 0.007,
                    v + 0.007,
                    -0.019,
                    -0.01,
                    PIPE,
                    "Plate fixing",
                )
