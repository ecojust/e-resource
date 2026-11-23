"""Upper pair of casements on the garden entrance wall of 159 Yanqing Road.

X increases to the corner, Y enters the wall, Z is up. The default placement fits
the photographed masonry opening. Supply layout['opening'] = [x0,z0,x1,z1] to
rescale or reposition this pair. layout['recess'] and layout['angle_deg'] are in
metres and degrees. The exterior stone surround and sill belong to the wall.
"""
from math import cos, radians, sin

from shapely.geometry import box
from shapely.ops import unary_union

from garden_finishes import IVORY_RENDER

OPENING = (-2.34, 3.17, -.60, 4.29)
LIGHT = 'Yanqing 159 | light painted steel'
GREEN = 'Yanqing 159 | green painted steel'
LIGHT_GLASS = 'Yanqing 159 | pale casement reflection'
GREEN_GLASS = 'Yanqing 159 | blue-green fixed glazing'
RECESS = 'Yanqing 159 | shaded open casement'


def finish(rgb, roughness):
    values = [n / 255 for n in rgb]
    linear = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in values]
    return {'color': linear, 'roughness': roughness}


PALETTE = {LIGHT: finish((185, 180, 151), .73), GREEN: finish((60, 79, 70), .66),
           LIGHT_GLASS: finish((113, 133, 136), .29), GREEN_GLASS: finish((86, 111, 109), .31),
           RECESS: finish((42, 43, 36), .93)}


def add_upper_sash(b, lod=False, layout=None):
    """Add the recessed frames, central post, photographed open leaf and closed green glazing."""
    options = layout or {}
    left, bottom, right, top = options.get('opening', OPENING)
    if right <= left or top <= bottom:
        raise ValueError('The masonry opening must have positive width and height')
    sx, sz = (right - left) / 1.74, (top - bottom) / 1.12
    depth = options.get('recess', .10)
    angle = radians(options.get('angle_deg', 92.0))
    for name, spec in PALETTE.items():
        b.palette.setdefault(name, spec)

    def x(value):
        return left + (value - OPENING[0]) * sx

    def z(value):
        return bottom + (value - OPENING[1]) * sz

    def solid(shape, origin, along, back, front, material, label):
        ux, uy = along
        def point(u, height, outward):
            return (origin[0] + ux*u + uy*outward,
                    origin[1] + uy*u - ux*outward, height)
        b.prism(shape, back, front, point, material, '159 upper pair | ' + label)

    sill, head = z(3.254), z(4.224)
    hinge = x(-1.987)
    leaf_width = .513 * sx
    fixed_left, fixed_right = x(-1.25), x(-.735)
    # Image 190 shows a pale central pier and two horizontal reveal edges.
    # The dark sheet terminates the visible opening at the model cut.
    solid(box(left, bottom, right, top), (0., depth + .27), (1., 0.), -.023, 0.,
          RECESS, 'recess beyond open steel leaf')
    left_aperture = box(hinge - .018*sx, sill - .015*sz, hinge + leaf_width + .018*sx, head + .015*sz)
    right_aperture = box(fixed_left - .012*sx, sill - .015*sz, fixed_right + .012*sx, head + .015*sz)
    reveal = box(left, bottom, right, top).difference(unary_union([left_aperture, right_aperture]))
    solid(reveal, (0., depth), (1., 0.), -.055, -.011, IVORY_RENDER, 'inner reveals and central mullion')

    def sash(origin, along, width, steel, glass, label):
        outer = box(0., sill, width, head)
        stile = .018*sx
        low, high = sill + .051*sz, head - .025*sz
        nx, nz = 3, 3
        bars = .012*sx
        rails = .013*sz
        pane_width = (width - 2*stile - (nx-1)*bars) / nx
        pane_height = (high - low - (nz-1)*rails) / nz
        panes = []
        for row in range(nz):
            for col in range(nx):
                a, h = stile + col*(pane_width + bars), low + row*(pane_height + rails)
                pane = box(a, h, a + pane_width, h + pane_height)
                panes.append(pane)
                solid(pane, origin, along, -.0025, .0025, glass, label + ' | glass')
        solid(outer.difference(unary_union(panes)), origin, along, -.012, .012,
              steel, label + ' | perimeter and glazing bars')

    sash((hinge, depth), (cos(angle), -sin(angle)), leaf_width, LIGHT, LIGHT_GLASS, 'open pale casement')
    sash((fixed_left, depth), (1., 0.), fixed_right - fixed_left, GREEN, GREEN_GLASS, 'closed green casement')
    if not lod:
        # A narrow lower rolled edge is visible on the outward leaf.
        solid(box(.008*sx, sill + .014*sz, leaf_width - .008*sx, sill + .022*sz),
              (hinge, depth), (cos(angle), -sin(angle)), -.018, -.010, LIGHT, 'rolled bottom edge')
