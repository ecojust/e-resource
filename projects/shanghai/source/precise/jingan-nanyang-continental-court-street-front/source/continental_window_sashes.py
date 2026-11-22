"""Editable street window frames, glazed lights and outward-opening leaves.

The facade's point(u, depth, z) uses metres, with depth positive indoors.
The mason supplies clear opening boundaries. Floors use street numbering 2–4.
Angles describe the photographed state of the fittings, not historical hardware.
"""
from collections import defaultdict
from dataclasses import dataclass
from math import cos, radians, sin
from pathlib import Path

IRON = 'Windows | dark painted glazing bars'
GREEN = 'Windows | weathered grey-green steel'
DARK_GLASS = 'Windows | shaded glass'
GREY_GLASS = 'Windows | grey glass'
LIGHT_GLASS = 'Windows | reflected pale glass'


def finish(rgb, roughness, metallic):
    def linear(value):
        value /= 255.
        return value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4
    return {'color': [linear(value) for value in rgb], 'roughness': roughness,
            'metallic': metallic}


PALETTE = {
    IRON: finish((60, 58, 52), .66, .14),
    GREEN: finish((82, 88, 80), .58, .19),
    DARK_GLASS: finish((66, 69, 65), .24, .14),
    GREY_GLASS: finish((87, 99, 101), .23, .16),
    LIGHT_GLASS: finish((135, 148, 151), .24, .13),
}

for name in (DARK_GLASS, GREY_GLASS, LIGHT_GLASS):
    PALETTE[name]['texture'] = str(Path(__file__).with_name('window-glazing.png'))


@dataclass(frozen=True)
class Pattern:
    transom: float
    lower_columns: tuple
    lower_rows: int
    upper_columns: int
    upper_rows: int


# Lower columns are counted separately for each opening leaf. Counts behind the
# fixed fabric shades use the adjoining visible parts of the same window family.
PAIRED = Pattern(.69, (2, 2), 4, 4, 2)
PLAIN = Pattern(.72, (1, 1), 4, 2, 1)
UPPER_LEFT = Pattern(.62, (2, 2), 4, 4, 2)
OPEN_WITH_INNER_POST = Pattern(.575, (2, 2), 4, 4, 2)
FINE_LIGHT = Pattern(.66, (2, 2), 4, 4, 2)
THREE_STRIP = Pattern(.70, (2,), 3, 2, 1)
NARROW_STRIP = Pattern(.71, (1,), 3, 1, 1)

# (bay, floor, opening): pattern, frame, glass, lower left/right turns and
# outward tilt of the top-hinged transom. Partly masked heads remain shut unless
# the source resolves an advancing lower edge or the leaf's projecting return.
SOUTH = {
    (7, 4): ((OPEN_WITH_INNER_POST, GREEN, DARK_GLASS, (77, 70), 65),
             (FINE_LIGHT, IRON, GREY_GLASS, (55, 61), 0)),
    (7, 3): ((UPPER_LEFT, GREEN, LIGHT_GLASS, (0, 0), 0),
             (PLAIN, GREEN, LIGHT_GLASS, (0, 0), 0)),
    (7, 2): ((FINE_LIGHT, GREEN, GREY_GLASS, (0, 0), 0),
             (PAIRED, IRON, DARK_GLASS, (0, 0), 0)),
    (8, 4): ((PLAIN, IRON, GREY_GLASS, (0, 57), 29),
             (FINE_LIGHT, GREEN, LIGHT_GLASS, (0, 0), 42)),
    (8, 3): ((PLAIN, GREEN, LIGHT_GLASS, (0, 42), 41),
             (PAIRED, GREEN, GREY_GLASS, (0, 33), 39)),
    (8, 2): ((FINE_LIGHT, GREEN, GREY_GLASS, (0, 0), 0),
             (PLAIN, GREEN, DARK_GLASS, (0, 0), 43)),
    (9, 4): ((FINE_LIGHT, GREEN, LIGHT_GLASS, (0, 0), 0),
             (PLAIN, GREEN, GREY_GLASS, (0, 57), 41)),
    (9, 3): ((PLAIN, GREEN, LIGHT_GLASS, (0, 0), 37),
             (PAIRED, GREEN, GREY_GLASS, (0, 39), 0)),
    (9, 2): ((PLAIN, GREEN, GREY_GLASS, (40, 44), 38),
             (PLAIN, GREEN, GREY_GLASS, (0, 0), 0)),
}
BROAD = {0, 5, 10}
EAST_PATTERNS = {
    (1, 2): (PAIRED, PAIRED), (1, 3): (PAIRED, PAIRED), (1, 4): (PAIRED, PLAIN),
    (2, 2): (PAIRED, PAIRED), (2, 3): (PAIRED, PAIRED), (2, 4): (PAIRED, PAIRED),
    (3, 2): (PAIRED, PAIRED), (3, 3): (PAIRED, PAIRED), (3, 4): (PAIRED, PAIRED),
    (4, 2): (PAIRED, PAIRED), (4, 3): (PAIRED, PAIRED), (4, 4): (PAIRED, PAIRED),
    (6, 2): (PAIRED, PAIRED), (6, 3): (PAIRED, PAIRED), (6, 4): (PAIRED, PAIRED),
}


def specification(bay, floor, index):
    if bay in BROAD:
        pattern = NARROW_STRIP if bay == 10 or (bay == 0 and floor == 2) else THREE_STRIP
        glass = GREY_GLASS if (bay, floor, index) in {(5, 4, 0), (5, 3, 2), (10, 2, 2)} else DARK_GLASS
        angle = 24 if (bay, floor, index) == (10, 2, 2) else 0
        return pattern, IRON, glass, (angle,), 0
    if (bay, floor) in SOUTH:
        return SOUTH[bay, floor][index]
    pattern = EAST_PATTERNS[bay, floor][index]
    glass = GREY_GLASS if (bay, floor, index) in {(2, 4, 0), (3, 4, 1), (4, 3, 1), (4, 2, 1)} else DARK_GLASS
    return pattern, IRON, glass, (0, 0), 0


FACES = ((0,3,2,1), (4,5,6,7), (0,1,5,4), (1,2,6,5), (2,3,7,6), (3,0,4,7))


class WindowParts:
    """Each operable wing keeps a separate native edit group and local UV chart."""
    def __init__(self, point, prefix):
        self.point, self.prefix = point, prefix
        self.groups = defaultdict(lambda: ([], [], []))

    def box(self, name, material, x0, x1, y0, y1, z0, z1, transform):
        if x1 <= x0 or y1 <= y0 or z1 <= z0:
            raise ValueError('A frame or pane has a nonpositive dimension')
        verts, faces, uv = self.groups[name, material]
        base = len(verts)
        for x, y, z in ((x0,y0,z0), (x1,y0,z0), (x1,y1,z0), (x0,y1,z0),
                        (x0,y0,z1), (x1,y0,z1), (x1,y1,z1), (x0,y1,z1)):
            verts.append(self.point(*transform(x, y, z)))
            # The thickness has its own small UV displacement. The UVs follow
            # the swing and retain their scale on all six faces of each solid.
            uv.append((x - x0 + (y-y0)*.57, z-z0 + (y-y0)*.39))
        faces.extend(tuple(base + vertex for vertex in face) for face in FACES)

    def write(self, builder):
        for (part, material), (verts, faces, uv) in self.groups.items():
            builder.add(verts, faces, material, self.prefix + ' | ' + part)
            builder.parts[-1]['texcoords'] = uv


def static(x, y, z):
    return x, y, z


def side_hinge(pivot, y_pivot, angle):
    c, s = cos(radians(angle)), sin(radians(angle))
    def turn(x, y, z):
        dx, dy = x - pivot, y - y_pivot
        return pivot + c*dx + s*dy, y_pivot - s*dx + c*dy, z
    return turn


def top_hinge(z_pivot, y_pivot, angle):
    c, s = cos(radians(angle)), sin(radians(angle))
    def turn(x, y, z):
        dz, dy = z - z_pivot, y - y_pivot
        return x, y_pivot + c*dy + s*dz, z_pivot - s*dy + c*dz
    return turn


def rim(parts, name, frame, a, b, low, high, front, back, width, transform):
    box = parts.box
    box(name, frame, a, a+width, front, back, low, high, transform)
    box(name, frame, b-width, b, front, back, low, high, transform)
    box(name, frame, a+width, b-width, front, back, low, low+width, transform)
    box(name, frame, a+width, b-width, front, back, high-width, high, transform)


def glazed_leaf(parts, name, frame, glass, a, b, low, high, front, cols, rows, turn, coarse):
    width = min(.037, (b-a)*.105, (high-low)*.1)
    rim(parts, name, frame, a, b, low, high, front, front+.047, width, turn)
    a += width
    b -= width
    low += width
    high -= width
    xs = [a+(b-a)*i/cols for i in range(cols+1)]
    zs = [low+(high-low)*i/rows for i in range(rows+1)]
    half = min(.0105, (b-a)/(cols*9), (high-low)/(rows*9))
    for x in xs[1:-1]:
        parts.box(name, frame, x-half, x+half, front+.011, front+.040, low, high, turn)
    for z in zs[1:-1]:
        for j in range(cols):
            l = xs[j]+(half if j else 0)
            r = xs[j+1]-(half if j+1 < cols else 0)
            parts.box(name, frame, l, r, front+.011, front+.040, z-half, z+half, turn)
    if coarse:
        # Outer shape and glazing bars keep their real projected widths. A
        # single thin sheet behind them replaces the separately beaded panes.
        parts.box(name + ' glazing', glass, a, b, front+.0415, front+.047, low, high, turn)
    else:
        for i in range(rows):
            for j in range(cols):
                l, r = xs[j]+(half if j else 0), xs[j+1]-(half if j+1<cols else 0)
                d, t = zs[i]+(half if i else 0), zs[i+1]-(half if i+1<rows else 0)
                parts.box(name + ' glazing', glass, l, r, front+.032, front+.038, d, t, turn)


def single(parts, spec, a, b, low, high, recess, coarse):
    pattern, frame, glass, angles, tilt = spec
    jamb = min(.052, (b-a)*.08, (high-low)*.045)
    transom = low+(high-low)*pattern.transom
    static_front = recess
    rim(parts, 'fixed jamb and head', frame, a, b, low, high,
        static_front, recess+.079, jamb, static)
    a += jamb
    b -= jamb
    low += jamb
    high -= jamb
    rail = min(.062, (high-low)*.07)
    parts.box('transom rail', frame, a, b, recess, recess+.071,
              transom-rail/2, transom+rail/2, static)
    front = recess+.014
    upper = top_hinge(high, front, tilt)
    glazed_leaf(parts, 'upper light', frame, glass, a, b, transom+rail/2, high,
                front, pattern.upper_columns, pattern.upper_rows, upper, coarse)
    mid = (a+b)/2
    if pattern is OPEN_WITH_INNER_POST:
        # Both contemporary photographs retain the inner stile after the two
        # wings swing out. It also crosses the exposed back of the upper light.
        parts.box('fixed interior centre stile', GREEN, mid-.013, mid+.013,
                  recess+.075, recess+.105, low, high, static)
    intervals = ((a,b),) if len(angles)==1 else ((a,mid-.0015),(mid+.0015,b))
    for j, ((l,r), degrees) in enumerate(zip(intervals, angles)):
        hinge = side_hinge(l if j == 0 else r, front, degrees if j == 0 else -degrees)
        glazed_leaf(parts, 'lower leaf '+str(j+1), frame, glass, l, r, low,
                    transom-rail/2, front, pattern.lower_columns[j], pattern.lower_rows, hinge, coarse)


def add_sash(builder, lod, point, bay, floor, leaf_index, u0, u1, z0, z1, recess=.10,
             *, strip_index=None, stone_mullions=None):
    """Fit the given opening. Supply all lengths and optional stone intervals in metres.

    For bays 0, 5 and 10, pass a single broad opening and optional two stone
    intervals, or call once per net opening with strip_index=0, 1, 2.
    """
    if bay not in range(11) or floor not in (2,3,4) or min(u1-u0,z1-z0) <= .18:
        raise ValueError('Invalid street bay, storey or clear opening')
    if bay in BROAD and strip_index is None:
        if stone_mullions is None:
            w = u1-u0
            stone_mullions = [(u0+w*t-w*.036, u0+w*t+w*.036) for t in (1/3,2/3)]
        (l0,r0),(l1,r1) = stone_mullions
        if not u0 < l0 < r0 < l1 < r1 < u1:
            raise ValueError('Stone intervals must lie inside the broad opening in order')
        for j,(a,b) in enumerate(((u0,l0),(r0,l1),(r1,u1))):
            add_sash(builder, lod, point, bay, floor, j, a,b,z0,z1,recess,strip_index=j)
        return
    index = strip_index if bay in BROAD else leaf_index
    if index not in (range(3) if bay in BROAD else range(2)):
        raise ValueError('Invalid index for the physical opening')
    parts = WindowParts(point, f'Street window B{bay:02d} F{floor} opening {index+1}')
    single(parts, specification(bay, floor, index), u0,u1,z0,z1,recess,lod is True or lod=='lod')
    parts.write(builder)
