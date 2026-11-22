"""Rectangular casements and dressed sills on the 115 Yuanmingyuan Road east front.

X follows the facade north, Y increases into the building and Z is height.
openings() and add_windows() use exactly the same observed front-wall rectangles.
See measurements/wing-window-observations.json for pixel positions and sources.
"""

from functools import lru_cache
import json
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon

MEASUREMENTS = Path(__file__).resolve().parents[1] / "measurements"
PAINT = "Yuanming deep red-brown sash paint"
BEAD = "Yuanming dark sash rebate"
GLASS = "Yuanming blue-grey casement glazing"
TRANSOM = "Yuanming shaded small glazing"
STONE = "Yuanming grey-green sill stone"


def finish(rgb, roughness, metal=0.0):
    srgb = np.asarray(rgb) / 255.0
    linear = np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)
    return {"color": linear.tolist(), "roughness": roughness, "metallic": metal}


PALETTE = {
    PAINT: finish([78, 51, 51], 0.56),
    BEAD: finish([57, 41, 41], 0.61),
    GLASS: finish([78, 91, 103], 0.26, 0.24),
    TRANSOM: finish([71, 82, 93], 0.31, 0.21),
    STONE: finish([119, 121, 110], 0.83),
}


@lru_cache(maxsize=1)
def openings():
    """Return the measured outer masonry openings for the wall and sash builders."""
    from east_photo_plane import on_wall

    marks = json.loads((MEASUREMENTS / "wing-window-observations.json").read_bytes())
    rows = []
    for name, corners in marks["openings_px"].items():
        points = np.asarray([on_wall(*p, y=0.0, camera="2014_oblique") for p in corners])
        left = points[[0, 3], 0].mean()
        right = points[[1, 2], 0].mean()
        bottom = points[[2, 3], 2].mean()
        top = points[[0, 1], 2].mean()
        if not left < right or not bottom < top:
            raise ValueError(f"Invalid calibrated opening for {name}")
        rows.append({
            "label": name, "left": float(left), "right": float(right),
            "bottom": float(bottom), "top": float(top),
            "level": "attic" if "attic" in name else name.split("-")[1],
            "wing": name.split("-")[0],
        })
    return tuple(rows)


@lru_cache(maxsize=1)
def sash_face_depths():
    """Pools clear intersections on the same wing and level. Distances refer to the fine bar."""
    record = json.loads((MEASUREMENTS / "wing-sash-depth.json").read_bytes())
    groups = {}
    for point in record["triangulated"]:
        if point["partially_occluded_in_2016"]:
            continue
        wing, level, _ = point["window"].split("-")
        groups.setdefault((wing, level), []).append(point["xyz_m"][1])
    depths = {key: float(np.median(values)) - 0.044 for key, values in groups.items()}
    # The separate 2016 front view ends below the attic. Its jamb depth is an
    # estimate transferred from the upper row on each wing, not a triangulation.
    for wing in ("near", "far"):
        depths[(wing, "attic")] = depths[(wing, "upper")]
    return depths


def add_casement(builder, opening, lod=False, frame_y=None):
    """Add one measured recessed glazed unit. frame_y is the frame face depth."""
    x0, x1, z0, z1 = (opening[k] for k in ("left", "right", "bottom", "top"))
    label = opening["label"]
    attic = opening["level"] == "attic"
    width, height = x1 - x0, z1 - z0
    if min(width, height) <= 0:
        raise ValueError(f"Empty sash {label}")
    if frame_y is None:
        frame_y = sash_face_depths()[opening["wing"], opening["level"]]

    def rail(xa, xb, za, zb, y, thickness, material, name):
        builder.box([(xa + xb) / 2, y + thickness / 2, (za + zb) / 2],
                    [xb - xa, thickness, zb - za], material, label=f"{label} · {name}")

    border = min(0.081, 0.048 * width, 0.085 * height)
    xa, xb, za, zb = x0 + border, x1 - border, z0 + border, z1 - border
    mid = (xa + xb) / 2
    rail(x0, xa, z0, z1, frame_y, 0.084, PAINT, "south jamb")
    rail(xb, x1, z0, z1, frame_y, 0.084, PAINT, "north jamb")
    rail(xa, xb, z0, za, frame_y, 0.084, PAINT, "bottom rail")
    rail(xa, xb, zb, z1, frame_y, 0.084, PAINT, "head rail")

    if attic:
        verticals = [(mid, min(0.14, 0.082 * width)),
                     (xa + (xb - xa) * 0.25, 0.058),
                     (xa + (xb - xa) * 0.75, 0.058)]
        horizontals = [(za + (zb - za) * 0.26, 0.024),
                       (za + (zb - za) * 0.62, 0.026)]
        rail(xa, xb, za, zb, frame_y + 0.082, 0.012, GLASS, "four short lights")
        for x, thickness in verticals:
            rail(x - thickness / 2, x + thickness / 2, za, zb, frame_y + 0.009,
                 0.067, PAINT, "short sash stile")
        for z, thickness in horizontals:
            rail(xa, xb, z - thickness / 2, z + thickness / 2, frame_y + 0.038,
                 0.032, PAINT, "short sash horizontal glazing bar")
        return

    divider = za + (zb - za) * 0.675
    main_bar = za + (divider - za) * 0.48
    transom_bar = divider + (zb - divider) * 0.51
    mullion = min(0.145, 0.082 * width)
    transom_thick = min(0.135, 0.064 * height)
    rail(xa, xb, za, divider, frame_y + 0.086, 0.015, GLASS, "lower paired glass")
    rail(xa, xb, divider, zb, frame_y + 0.087, 0.015, TRANSOM, "small upper lights")
    rail(mid - mullion / 2, mid + mullion / 2, za, zb, frame_y + 0.006,
         0.075, PAINT, "meeting stiles")
    rail(xa, xb, divider - transom_thick / 2, divider + transom_thick / 2,
         frame_y + 0.004, 0.079, PAINT, "transom")
    rail(xa, xb, main_bar - 0.013, main_bar + 0.013, frame_y + 0.044,
         0.030, PAINT, "main sash glazing bars")
    for x in (xa + (xb - xa) * 0.25, xa + (xb - xa) * 0.75):
        rail(x - 0.019, x + 0.019, divider + transom_thick / 2, zb, frame_y + 0.026,
             0.048, PAINT, "upper vertical glazing bars")
    rail(xa, xb, transom_bar - 0.015, transom_bar + 0.015, frame_y + 0.043,
         0.030, PAINT, "upper horizontal glazing bars")
    if not lod:
        # The lacquered meeting stiles have a separate narrow arris.
        rail(mid - 0.004, mid + 0.005, za, divider - transom_thick / 2,
             frame_y + 0.002, 0.004, BEAD, "joint between meeting stiles")
        for y, z in [(frame_y + 0.026, divider - transom_thick / 2 - 0.010),
                     (frame_y + 0.023, divider + transom_thick / 2 + 0.009)]:
            rail(xa, xb, z - 0.008, z + 0.008, y, 0.033, BEAD, "moulded transom edges")


def add_sill(builder, left, right, z, level, label, lod=False):
    """Sweep the photographed drip profile, including the offset ends at mid-floor."""
    x0, x1 = left - 0.16, right + 0.16
    if level == "upper":
        # Photo shows two projecting ends and a short inset middle above the brick apron.
        thirds = [(x0, x0 + (x1 - x0) * .33, .276),
                  (x0 + (x1 - x0) * .33, x0 + (x1 - x0) * .67, .226),
                  (x0 + (x1 - x0) * .67, x1, .276)]
    else:
        thirds = [(x0, x1, .215 if level == "attic" else .235)]
    for a, b, reach in thirds:
        section = [(.03, -.009), (-reach + .022, -.029),
                   (-reach, -.041), (-reach + .004, -.068)]
        if lod:
            section += [(-reach + .047, -.11)]
        else:
            section += [(-reach + .016, -.077), (-reach + .037, -.079),
                        (-reach + .032, -.090), (-reach + .034, -.103),
                        (-reach + .048, -.112)]
        section.extend([(-reach + .07, -.12), (-reach + .085, -.144), (.03, -.144)])
        builder.prism(Polygon(section), a, b, lambda y, height, x: (x, y, z + height),
                      STONE, f"{label} · profiled stone sill")


def add_windows(builder, lod=False):
    rows = openings()
    for row in rows:
        add_casement(builder, row, lod)
        if row["level"] != "attic":
            add_sill(builder, row["left"], row["right"], row["bottom"],
                     row["level"], row["label"], lod)
    for wing in ("near", "far"):
        pair = [r for r in rows if r["level"] == "attic" and r["wing"] == wing]
        if len(pair) != 2:
            raise ValueError(f"Expected two attic openings in the {wing} wing")
        add_sill(builder, min(r["left"] for r in pair), max(r["right"] for r in pair),
                 sum(r["bottom"] for r in pair) / 2, "attic", f"{wing} shared attic sill", lod)
