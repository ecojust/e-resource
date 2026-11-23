"""Visible end walls and short roof of the four-storey block facing Wanping Road."""
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from placement import Facade
from street_materials import GLASS, LIME, SHADE, STEEL, STONE

LEFT = -11.46
RIGHT = 11.35
XY_SCALE = 0.9465478513722255
Z_SCALE = 1.009918699186992
DEPTH = 5.10 / XY_SCALE

# Each opening is (wall distance from the street, opening width, sill, head).
# Depth and height are measured metres. The window fabric was drawn from the
# winter 2020 southwest views. The top pair at the rear is distinctly smaller.
SOUTH_WINDOWS = (
    (1.11, .90, 4.04, 5.30, 2, 3),
    (1.12, .89, 7.47, 8.58, 2, 3),
    (1.04, .95, 10.76, 11.90, 2, 2),
    (4.25, .67, 11.48, 12.02, 2, 1),
    (4.29, .57, 13.50, 14.55, 2, 2),
)
# The street-side coping meets the rear face of the existing attic strip.
# The rear edges are obscured in some views. A shallow roof closes the short
# street block within the observed end walls.
FRONT_Z = 15.53
SOUTH_BACK_Z = 14.72
NORTH_BACK_Z = 15.16


def add_side_roofs(b, lod=False):
    south = Facade(b, (LEFT, DEPTH), (0, -1), 'Wanping 42 | south return')
    north = Facade(b, (RIGHT, 0), (0, 1), 'Wanping 42 | north return')
    back = Facade(b, (RIGHT, DEPTH), (-1, 0), 'Wanping 42 | rear closure')
    windows = []
    for setback, width, sill, head, cols, rows in SOUTH_WINDOWS:
        centre = DEPTH - setback / XY_SCALE
        half = width / (2 * XY_SCALE)
        opening = box(centre-half, sill/Z_SCALE, centre+half, head/Z_SCALE)
        windows.append((opening, cols, rows))
    outline = Polygon([(0, 0), (DEPTH, 0), (DEPTH, FRONT_Z), (0, SOUTH_BACK_Z)])
    south.solid(outline.difference(unary_union([w[0] for w in windows])),
                -.19, 0, LIME, 'rendered wall with five openings')
    for i, (opening, cols, rows) in enumerate(windows):
        u0, z0, u1, z1 = opening.bounds
        name = 'stacked sash '+str(i+1) if i < 3 else 'rear light '+str(i-2)
        frame = .043 if i < 3 else .032
        south.solid(opening.difference(opening.buffer(-frame, join_style=2)),
                    -.135, -.075, STEEL, name+' | perimeter')
        inner = opening.buffer(-frame, join_style=2)
        south.solid(inner, -.153, -.14, GLASS if i != 3 else SHADE, name+' | panes')
        for j in range(1, cols):
            u = u0+(u1-u0)*j/cols
            south.rect(u-.012, u+.012, z0+frame, z1-frame, -.132, -.084, STEEL,
                       name+' | vertical sash bar')
        for j in range(1, rows):
            z = z0+(z1-z0)*j/rows
            south.rect(u0+frame, u1-frame, z-.013, z+.013, -.131, -.084, STEEL,
                       name+' | horizontal sash bar')
        south.rect(u0-.017, u1+.017, z0-.031, z0, -.06, .018, STONE, name+' | sill')
    north.solid(Polygon([(0,0),(DEPTH,0),(DEPTH,NORTH_BACK_Z),(0,FRONT_Z)]),
                -.19, 0, LIME, 'high rendered plane')
    back.solid(Polygon([(0,0),(RIGHT-LEFT,0),(RIGHT-LEFT,SOUTH_BACK_Z),(0,NORTH_BACK_Z)]),
               -.15, 0, LIME, 'upper block plain closure')
    # Keep the street attic glazing clear. The deck meets behind the front
    # head and the grey roof is slightly below each visible coping.
    front_y = .20
    def surface(x, y):
        rear_z = SOUTH_BACK_Z+(NORTH_BACK_Z-SOUTH_BACK_Z)*(x-LEFT)/(RIGHT-LEFT)
        return FRONT_Z+(rear_z-FRONT_Z)*y/DEPTH-.13
    plan = box(LEFT+.10, front_y, RIGHT-.10, DEPTH-.10)
    # Split along a diagonal so each part is individually closed and has planar faces.
    x0,y0,x1,y1 = plan.bounds
    for idx, coords in enumerate([[(x0,y0),(x1,y0),(x1,y1)],[(x0,y0),(x1,y1),(x0,y1)]]):
        b.prism(Polygon(coords), -.13, 0, lambda x,y,d:(x,y,surface(x,y)+d),
                STONE, 'Wanping 42 | shallow grey roof '+str(idx+1))


add_side_and_roof = add_side_roofs
