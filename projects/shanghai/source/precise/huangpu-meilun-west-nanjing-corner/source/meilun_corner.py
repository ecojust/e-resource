"""Initial measured corner study for the west Meilun building at 161 East Nanjing Road."""
from pathlib import Path
import json
import math
from shapely.geometry import Point, Polygon, box as rectangle
from photo_architecture import PALETTE as COMMON, Facade, opening

STONE = 'grey facing stone'
DRESSING = 'dressed grey stone'
GLASS = 'shop and office glazing'
SASH = 'dark bronze sash'
PALETTE = {
    **COMMON,
    STONE: {'color': [.36, .35, .32], 'roughness': .84},
    DRESSING: {'color': [.44, .42, .38], 'roughness': .77},
    GLASS: {'color': [.13, .19, .20], 'roughness': .25, 'metallic': .18},
    SASH: {'color': [.107, .113, .108], 'roughness': .48, 'metallic': .32},
}


def pediment(wall, u, base, half_width, rise, detail):
    outline = Polygon([(u - half_width, base), (u + half_width, base), (u, base + rise)])
    wall.prism(outline, .12, .28, STONE, 'triangular tympanum')
    wall.box(u, base - .035, half_width * 2.12, .15, .29, .17, DRESSING, 'pediment bed')
    for side in (-1, 1):
        wall.line((u + side * half_width, base, .29), (u, base + rise, .29),
                  .073 if detail else .085, DRESSING, 7, 'raking cornice')


def carved_pier(wall, u, detail):
    for i in range(7):
        wall.box(u, .36 + .74 * i, .70, .706, .29, .12, STONE, 'rusticated ground pier')
    wall.box(u, 9.13, .49, 7.64, .25, .12, DRESSING, 'upper pilaster')
    for edge in (-.17, .17):
        wall.line((u + edge, 5.42, .28), (u + edge, 12.80, .28),
                  .043, STONE, 6, 'pilaster edge bead')
    if detail:
        for z in (4.58, 12.35):
            cartouche = Point(u, z).buffer(.20, quad_segs=8)
            wall.prism(cartouche, .247, .34, DRESSING, 'relief medallion')
            for side in (-1, 1):
                curve = [(u + side * (.12 + .15 * i / 6),
                          z + .11 - .28 * math.sin(math.pi * i / 6), .302) for i in range(7)]
                wall.builder.tube([wall.point(*p) for p in curve], .032,
                                  DRESSING, 6, 'pier foliage outline')


def sash_group(wall, center, width, base, height, detail, corner):
    panes = 1 if corner and width < 1.0 else 2
    aperture = opening(center, base, width, height)
    wall.window(aperture, panes, 2, frame=SASH, glass=GLASS, trim=False, label='sash in stone reveal')
    wall.box(center, base - .045, width + .29, .13, .27, .11, DRESSING, 'projecting stone sill')
    if detail:
        for side in (-1, 1):
            wall.box(center + side * (width / 2 + .073), base + height / 2,
                     .105, height + .08, .13, .055, DRESSING, 'window jamb')


def section(wall, number_of_bays, detail, corner=False, entrance_setback=0.):
    lo, hi = -wall.length / 2, wall.length / 2
    bay = wall.length / number_of_bays
    axes = [lo + bay * (i + .5) for i in range(number_of_bays)]
    openings = []
    groups = []
    for axis in axes:
        openings.append(opening(axis, .12, bay - .82, 4.16))
        upper_axes = [(axis - bay * .227, bay * .111), (axis, bay * .261),
                      (axis + bay * .227, bay * .111)] if corner else [
            (axis - bay * .226, bay * .31), (axis + bay * .226, bay * .31)]
        for x, width in upper_axes:
            for base, height in ((5.35, 2.86), (9.46, 2.77)):
                groups.append((x, width, base, height))
                openings.append(opening(x, base, width, height))
    wall.wall(0., 13.05, openings, thickness=.41, material=STONE)
    for axis in axes:
        portal = opening(axis, .12, bay - .82, 4.16)
        if entrance_setback:
            dx, dy = -wall.n[:2] * entrance_setback
            inner = Facade(wall.builder, wall.a[:2] + [dx, dy], wall.b[:2] + [dx, dy],
                           wall.label + ' inset')
            inner.window(portal, 2 if corner else 3, 2, frame=SASH, glass=GLASS,
                         trim=False, label='recessed shopfront')
            left, bottom, right, top = portal.bounds
            surfaces = [(rectangle(left - .015, bottom, left + .04, top), 'left jamb'),
                        (rectangle(right - .04, bottom, right + .015, top), 'right jamb'),
                        (rectangle(left, top - .038, right, top + .015), 'door soffit')]
            for strip, name in surfaces:
                wall.prism(strip, -entrance_setback - .34, -.36, STONE, name)
            step = rectangle(left, .045, right, .125)
            wall.prism(step, -entrance_setback - .34, -.04, STONE, 'shop threshold')
        else:
            wall.window(portal, 3, 2, frame=SASH, glass=GLASS, trim=False, label='recessed shopfront')
    for x, width, base, height in groups:
        sash_group(wall, x, width, base, height, detail, corner)
    for i in range(number_of_bays+1):
        u = lo + bay * i
        carved_pier(wall, max(lo + .32, min(hi - .32, u)), detail)
    for z, height, depth in ((4.82, .21, .39), (5.04, .12, .48),
                              (8.94, .11, .22), (12.99, .19, .33), (13.18, .14, .56)):
        wall.box(0, z, wall.length, height, depth, depth / 2 - .035, DRESSING, 'continuous horizontal course')
    for axis in axes:
        if corner:
            for side in (-1, 1):
                column_u = axis + side * bay * .158
                center = wall.point(column_u, 0, .15)[:2]
                profile = [(5.35, .134), (5.48, .146), (5.57, .090), (8.04, .080),
                           (8.13, .133), (8.24, .145)]
                wall.builder.lathe(center, profile, DRESSING, 12 if detail else 8,
                                   'colonnettes supporting the lower pediment')
            pediment(wall, axis, 8.31, bay * .282, .55, detail)
            pediment(wall, axis, 13.32, bay * .443, .92, detail)
        else:
            width = bay * .76
            wall.box(axis, 13.72, width, .12, .19, .03, DRESSING, 'parapet handrail')
            count = 9 if detail else 6
            for i in range(count):
                x = axis + width * ((i + .5) / count - .5)
                if detail:
                    center = wall.point(x, 0, .03)[:2]
                    wall.builder.lathe(center, [(13.23, .09), (13.277, .102), (13.332, .063),
                                                (13.42, .091), (13.585, .05), (13.66, .092)],
                                       DRESSING, 8, 'turned parapet baluster')
                else:
                    wall.box(x, 13.44, .125, .50, .13, .015, DRESSING, 'balustrade spindle')
    if detail:
        count = max(4, round(wall.length / .4))
        for i in range(count):
            u = lo + wall.length * ((i + .5) / count)
            wall.box(u, 12.83, .12, .13, .20, .12, DRESSING, 'cornice dentil')


def add_corner(builder, lod=False):
    data = json.loads((Path(__file__).resolve().parents[1] / 'corner-study.json').read_bytes())
    q = data['corner']
    west, north = q['west_end'], q['nanjing_end']
    # The first study covers the two broad shop bays next to the diagonal. The
    # longer 21.5 m photographic measurement also includes the approach to the arcade.
    north_study_end = [north[0] + 12.8, north[1]]
    for a, b, name, bays, corner in [
        (north_study_end, north, 'Nanjing Road storefront', 2, False),
        (north, west, 'diagonal entrance', 1, True),
        (west, q['west_study_end'], 'Jiangxi Road return', 1, False),
    ]:
        section(Facade(builder, a, b, name), bays, not lod, corner)
