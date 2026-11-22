"""Registered windows of the former St Luke's Hospital on Changzhi and Nanxun roads."""

import json
from math import cos, hypot, pi, sin, sqrt
from pathlib import Path
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

CASE = "Sashes | dark green perimeter"
STEEL = "Sashes | green painted glazing bars"
BEAD = "Sashes | rounded green meeting edge"
PANE = "Sashes | dim grey-green reflected glass"
SKY = "Sashes | cool sky reflected glass"
SHADE = "Sashes | sheltered mineral reveal"
SILL = "Sashes | pale narrow sill stone"
COVER = "Sashes | light temporary lower panels"
RUSSET = "Sashes | muted red lower infill"
BOARD_EDGE = "Sashes | narrow panel edging"


def _paint(rgb, roughness, metallic=0.):
    def linear(channel):
        v = channel / 255.
        return v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
    return dict(color=[linear(c) for c in rgb], roughness=roughness, metallic=metallic)


PALETTE = {
    CASE: _paint((53, 64, 58), .65), STEEL: _paint((59, 75, 66), .59, .12),
    BEAD: _paint((72, 86, 75), .54, .1), PANE: _paint((84, 105, 101), .39, .10),
    SKY: _paint((124, 148, 153), .34, .08), SHADE: _paint((157, 151, 139), .91),
    SILL: _paint((199, 196, 180), .88), COVER: _paint((186, 181, 180), .86),
    RUSSET: _paint((136, 83, 71), .83), BOARD_EDGE: _paint((153, 157, 155), .75),
}


def _faces(layout):
    fs = layout["faces"]
    return fs if isinstance(fs, dict) else {f["id"]: f for f in fs}


def _windows(layout):
    rows = json.loads(Path(__file__).with_name("upper-window-layout.json").read_bytes())["rows"]
    faces = _faces(layout)
    for row in rows:
        face = faces[row["face"]]
        length = hypot(face["b"][0] - face["a"][0], face["b"][1] - face["a"][1])
        yield row, face, row["center_fraction"] * length, row["width_fraction"] * length


def _mouth(center, width, sill, spring, crown, steps=32):
    left, right = center - width / 2, center + width / 2
    rise = crown - spring
    if rise < .003:
        return box(left, sill, right, crown)
    radius = (width * width / 4 + rise * rise) / (2 * rise)
    # Uniform horizontal subdivisions follow the segment. The same boundary cuts the host wall.
    points = [(left, sill), (right, sill)]
    for j in range(steps + 1):
        x = width * .5 * cos(j * pi / steps)
        z = crown - radius + sqrt(max(0., radius * radius - x * x))
        points.append((center + x, z))
    return Polygon(points)


def opening_profiles(layout):
    """Return a list of all clear mouths on each named face, in along-wall and elevation coordinates."""
    result = {face: [] for face in _faces(layout)}
    for r, _, c, w in _windows(layout):
        result[r["face"]].append(_mouth(c, w, r["sill"], r["spring"], r["crown"]))
    return result


def _mapper(face):
    a, end = face["a"], face["b"]
    length = hypot(end[0] - a[0], end[1] - a[1])
    tx, ty = (end[0] - a[0]) / length, (end[1] - a[1]) / length
    nx, ny = face["out"]
    orientation = 1. if ty * nx - tx * ny > 0. else -1.

    def world(s, z, depth):
        return a[0] + tx*s + nx*depth*orientation, a[1] + ty*s + ny*depth*orientation, z

    return world, orientation


def add_sashes(b, lod=False, layout=None):
    """Place sashes after the matching masonry cuts. An outward offset has positive sign."""
    if layout is None:
        raise ValueError("A registered street layout is required")
    b.palette.update(PALETTE)
    for r, f, c, w in _windows(layout):
        world, sign = _mapper(f)
        name = f"St Luke windows / {r['face']} {r['axis']:02} L{r['level']} / "
        sill, spring, top = (float(r[k]) for k in ("sill", "spring", "crown"))
        shape = _mouth(c, w, sill, spring, top)
        width = min(.058, max(.032, w * .039))
        case_profile = _mouth(c, w, sill, spring, top, 12) if lod else shape
        case_outer = case_profile.buffer(-.014, join_style=2)
        light = case_outer.buffer(-width, join_style=2)
        l, z0, hi, z1 = light.bounds
        xmid = (l + hi) / 2
        depth = r["setback_m"]

        def solid(poly, front, back, mat, label):
            if poly.is_empty or poly.area < .000002:
                return
            low, high = sorted((front * sign, back * sign))
            b.prism(poly, low, high, world, mat, name + label)

        solid(shape.difference(case_outer), -.004, -depth-.037, SHADE, "recess lining")
        solid(case_outer.difference(light), -depth, -depth-.055, CASE, "fixed wood and steel case")
        # The surface shields and sill plates on the far three lower windows are recorded in January 2021.
        covered = r["face"] == "nanxun" and r["level"] == 2 and r["axis"] > 3
        if covered:
            # From the northern street position, bay six has three paired lights.
            # In bays four and five the lower pair shows a discontinuous rusty-red backing.
            levels = (.0, .36, .65, 1.) if r["axis"] == 6 else (.0, .59, 1.)
            solid(light, -depth-.040, -depth-.063, BOARD_EDGE, "panel backing and narrow seams")
            for j, (lo, hi_z) in enumerate(zip(levels, levels[1:])):
                y0 = z0+(z1-z0)*lo
                y1 = z0+(z1-z0)*hi_z
                for side, (x0, x1) in enumerate(((l, xmid), (xmid, hi))):
                    panel = light.intersection(box(x0+.014, y0+.016, x1-.014, y1-.016))
                    red = r["axis"] == 6 and (j == 0 or j == 1 and side == 0)
                    mat = RUSSET if red else COVER
                    solid(panel, -depth-.012, -depth-.039, mat, f"metal-framed lower infill {side+1}/{j+1}")
                    if r["axis"] in (4,5) and j == 0 and (side == 0 or r["axis"] == 5):
                        tint = .43 if r["axis"] == 4 else (.62 if side == 0 else .73)
                        backing = panel.intersection(box(x0-.01,y0-.01,x1+.01,y0+(y1-y0)*tint))
                        solid(backing, -depth-.010, -depth-.012, RUSSET, f"visible dark backing {side+1}")
        else:
            rounded = r["shape"] == "round"
            narrow = w < 1.02 or (r["face"] == "changzhi" and r["axis"] in (7, 9)) or (r["face"].startswith("corner") and r["level"] != 3)
            cols = 2 if narrow else 4
            step_h = z1-z0
            if rounded:
                transom = spring
                rails = [z0 + (spring-z0)*k/3 for k in (1, 2)] + [spring]
            elif r["face"].startswith("corner") or r["face"] == "nanxun":
                transom = z0 + .605*step_h
                rails = [z0+(transom-z0)*k/3 for k in (1,2)] + [transom, transom+(z1-transom)*.5]
            else:
                transom = z0 + step_h*.75
                rails = [z0 + step_h*i/4 for i in (1, 2, 3)]
            glz = light.buffer(-.002, join_style=2)
            mat = SKY if rounded else PANE
            solid(glz, -depth-.043, -depth-.060, mat, "glazing")
            if not lod and not rounded and cols == 4:
                inset = box(l+.002,z0+.002,l+(hi-l)/4-.006,rails[0]-.006)
                solid(inset, -depth-.042, -depth-.043, SKY, "individual reflected lower light")
            bars = []
            for i in range(1, cols):
                x = l+(hi-l)*i/cols
                thick = .030 if i*2 == cols else .017
                limit = spring if rounded else z1+.01
                bars.append(box(x-thick/2,z0-.01,x+thick/2,limit))
            for z in rails:
                thick = .038 if abs(z-transom)<.001 else .020
                bars.append(box(l-.01,z-thick/2,hi+.01,z+thick/2))
            if rounded:
                # Upper fanlights range from radiating spokes to three nearly upright bars.
                fan = r["face"] == "changzhi" and r["axis"] in (3,4,5)
                for i in (1,2,3):
                    u = l+(hi-l)*i/4
                    start = (xmid+(u-xmid)*.14,spring) if fan else (u,spring)
                    end = (u+(u-xmid)*(.38 if fan else .17),z1+.02)
                    bars.append(LineString([start,end]).buffer(.010,cap_style=2))
            grid = light.intersection(unary_union(bars))
            solid(grid, -depth-.008, -depth-.042, STEEL, "glazing bars and opening transom")
            if not lod:
                strip = light.intersection(box(xmid-.008,z0+.002,xmid+.008,(spring if rounded else transom)-.017))
                solid(strip, -depth-.001, -depth-.008, BEAD, "central meeting edge")
        # A small projecting ledge sits at each photographically visible sill.
        lout, rout = c-w/2-.024, c+w/2+.024
        solid(box(lout,sill-.045,rout,sill-.002), .066, -.014, SILL, "sill nosing")
