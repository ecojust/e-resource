"""The independently hinged street leaves and arched open ironwork observed in February 2020."""

import math
import numpy as np
from shapely.geometry import Polygon

IRON = "Black-green painted iron"
METAL = "Iron edge catching light"
SHEET = "Dark iron door panels"
NOTICE = "Warm enamel on gate"
PAPER = "Muted paper notice"


def add_leaf(b, hinge, sense, width, angle, d, lod, label):
    height = d["leaf_shoulder_height"]
    rise = d["leaf_rise"]
    yaw = math.radians(angle)
    along = (sense * math.cos(yaw), math.sin(yaw), 0)
    normal = (-along[1] * sense, along[0] * sense, 0)
    zaxis = (0, 0, 1)
    low = 0.115
    sheet_top = height * 0.83

    def point(u, offset, z):
        return (hinge[0] + u * along[0] + offset * normal[0],
                hinge[1] + u * along[1] + offset * normal[1], z)

    def box_at(u, offset, z, length, thick, tall, mat, name):
        b.box(point(u, offset, z), (length, thick, tall), mat,
              (along, normal, zaxis), label + " " + name)

    def crest(t):
        return height + rise * t * t * (3 - 2 * t)

    def tube(coords, radius, mat, name):
        b.tube([point(u, offset, z) for u, offset, z in coords], radius, mat,
               5 if lod else 8, label + " " + name)

    def plate(vertices, low_y, high_y, mat, name):
        # Keep u, z and outward depth right handed on the two opposite leaves.
        if sense == 1:
            b.prism(Polygon(vertices), -high_y, -low_y, lambda u, z, v: point(u, -v, z), mat, label + " " + name)
        else:
            b.prism(Polygon(vertices), low_y, high_y, lambda u, z, v: point(u, v, z), mat, label + " " + name)

    for fraction in (0.0, 1.0):
        u = 0.028 + (width - 0.056) * fraction
        top = crest(fraction)
        box_at(u, 0, (low + top) / 2, 0.045, 0.048, top - low, IRON, "edge stile")
    for z in (low + 0.03, 0.31, sheet_top):
        box_at(width / 2, 0, z, width, 0.05, 0.043, IRON, "straight cross rail")
    # Dark infill below the open shoulder and narrow gaps right above the ground.
    box_at(width / 2, 0.018, (sheet_top + 0.31) / 2, width - 0.064, 0.016,
           sheet_top - 0.31, SHEET, "solid lower leaf")
    n = max(8, round(width / 0.15))
    band = 0.139
    for i in range(1, n):
        t = i / n
        z = crest(t) - band
        box_at(t * width, 0, (z + low) / 2, 0.016, 0.025, z - low, METAL, "upright")
    curve = np.linspace(0, 1, 13 if lod else 29)
    for offset in (0, -band):
        tube([(t * width, 0, crest(t) + offset) for t in curve],
             0.017 if offset == 0 else 0.011, METAL, "swept crest")
    for i in range(n):
        mid = (i + 0.5) / n
        profile = []
        for a in np.linspace(0, 2 * math.pi, 9 if lod else 17):
            u = mid * width + math.cos(a) * width / n * 0.31
            z = crest(u / width) - band / 2 + math.sin(a) * band * 0.37
            profile.append((u, 0, z))
        tube(profile, 0.008, METAL, "open crest ring")
        if not lod:
            # The photographed cast band contains repeated curled strokes inside its loops.
            curl = []
            for a in np.linspace(-0.18, 4.44, 12):
                radius = 0.86 - (a + 0.18) * 0.13
                u = mid * width + math.cos(a) * radius * width / n * 0.30
                z = crest(u / width) - band / 2 + math.sin(a) * radius * band * 0.38
                curl.append((u, -0.0005, z))
            tube(curl, 0.0055, METAL, "inward iron scroll")
        if not lod or i % 2 == 0:
            tip = crest(mid) + 0.093
            tube([(mid * width, 0, crest(mid)), (mid * width, 0, tip - 0.027)],
                 0.0065, IRON, "finial stem")
            u = mid * width
            plate([(u, tip), (u + 0.016, tip - 0.032), (u, tip - 0.056),
                   (u - 0.016, tip - 0.032)], -0.008, 0.008, IRON, "spearhead")
    if sense < 0:
        for offset, mat in ((0.11, PAPER), (0.48, NOTICE)):
            z = sheet_top - 0.45 + offset
            ww = width * 0.42
            cx = width * 0.59
            h = 0.195 if mat == PAPER else 0.235
            outline = [(cx - ww / 2, z - h / 2), (cx, z - h * 0.65),
                       (cx + ww / 2, z - h / 2), (cx + ww / 2, z + h / 2),
                       (cx, z + h * 0.69), (cx - ww / 2, z + h / 2)]
            plate(outline, -0.038, -0.022, mat, "notice plate")
            if not lod and mat == NOTICE:
                box_at(cx, -0.040, z + h * 0.32, ww * 0.89, 0.006, 0.029, IRON, "enamel heading band")
    for z in (0.34, height - 0.34):
        b.lathe(hinge, [(z - 0.063, 0.025), (z + 0.063, 0.025)],
                IRON, 8 if lod else 14, label + " hinge barrel")
