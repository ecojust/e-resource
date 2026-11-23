"""Recessed two-leaf iron gate, sash bars, corridor walls and ceiling beams."""

import math

IRON = "Blackened iron gate"
PAINT = "Dark grey joinery"
PLASTER = "Off-white passage plaster"
DADO = "Charcoal green passage dado"
PAVING = "Grey concrete walking surface"
CEILING = "Light grey passage ceiling"
GLASS = "Dark sage window reflections"


def gate_leaf(b, hinge, side, width, yaw, head, y, lod, label):
    into = (-side * math.cos(yaw), math.sin(yaw), 0)
    normal = (side * math.sin(yaw), math.cos(yaw), 0)

    def bar(u, z, depth, w, h, thickness, mat, name):
        center = (hinge + into[0] * u + normal[0] * depth, y + into[1] * u + normal[1] * depth, z)
        b.box(center, (w, thickness, h), mat, (into, normal, (0, 0, 1)), label + " " + name)

    low = 0.055
    high = head
    for u in (0.026, width - 0.026):
        bar(u, (low + high) / 2, 0, 0.052, high - low, 0.053, IRON, "frame upright")
    rails = (low + 0.028, 0.72, high * 0.60, high - 0.028)
    for z in rails:
        bar(width / 2, z, 0, width, 0.05, 0.055, IRON, "frame rail")
    uprights = max(6, round(width / 0.135))
    for i in range(1, uprights):
        bar(
            width * i / uprights,
            (low + high) / 2,
            0,
            0.015,
            high - low - 0.07,
            0.019,
            IRON,
            "vertical grille",
        )
    if not lod:
        for u in (0.035, width - 0.035):
            for z in (0.33, high - 0.30):
                bar(u, z, 0.033, 0.076, 0.10, 0.035, IRON, "corner connection")
        bar(width - 0.10, 1.00, -0.047, 0.024, 0.175, 0.045, IRON, "handle")
    for z in (0.33, high - 0.28):
        b.lathe(
            (hinge, y),
            [(z - 0.062, 0.029), (z + 0.062, 0.029)],
            IRON,
            8 if lod else 14,
            label + " hinge barrel",
        )


def opening(b, d, lod):
    mid = d["opening_center_x"]
    clear = d["clear_width"]
    head = d["opening_head"]
    left, right = mid - clear / 2, mid + clear / 2
    depth = d["passage_depth"]
    for i, x in enumerate([left, right]):
        sign = -1 if i == 0 else 1
        label = ("West" if i == 0 else "East") + " passage wall"
        for low, high, mat in [(0.005, 1.02, DADO), (1.02, head, PLASTER)]:
            b.box(
                (x + sign * 0.07, (0.42 + depth) / 2, (low + high) / 2),
                (0.14, depth - 0.42, high - low),
                mat,
                label=label,
            )
        gate_leaf(
            b,
            x - sign * 0.048,
            sign,
            clear / 2 - 0.055,
            math.radians(74 if i == 0 else 60),
            d["gate_top"],
            0.47,
            lod,
            label + " hinged gate",
        )
    b.box(
        (mid, (0.33 + depth) / 2, head + 0.075),
        (clear, depth - 0.33, 0.15),
        CEILING,
        label="Passage ceiling",
    )
    for j, fraction in enumerate((0.36, 0.76)):
        y = 0.45 + fraction * (depth - 0.45)
        b.box(
            (mid, y, head - 0.025),
            (clear, 0.135, 0.095),
            CEILING,
            label=f"Passage cross beam {j + 1}",
        )
    b.box(
        (mid, (depth + 0.00) / 2, 0.013),
        (clear, depth, 0.026),
        PAVING,
        label="Continuous lane threshold",
    )
