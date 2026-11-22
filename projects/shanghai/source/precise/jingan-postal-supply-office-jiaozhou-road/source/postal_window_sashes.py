"""Editable west-facing windows at 322 Jiaozhou Road, Shanghai.

X runs along the frontage towards the south end, Y into the building, Z up.
The caller supplies the clear masonry opening and the depth of the front frame.
Each metal grille is a closed extrusion with actual rectangular pane cutouts.
"""
from pathlib import Path

from shapely.geometry import box
from shapely.ops import unary_union


FIXED = 'Postal office windows | painted fixed frame'
SASH = 'Postal office windows | dark glazing bars'
SHADE = 'Postal office windows | shaded glass'
PALE = 'Postal office windows | grey-green glass'
SKY = 'Postal office windows | sky-reflecting glass'


def finish(rgb, roughness, metallic):
    def linear(channel):
        c = channel / 255
        return c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4
    return dict(color=[linear(c) for c in rgb], roughness=roughness, metallic=metallic)


PALETTE = {
    FIXED: finish((48, 51, 49), .63, .20),
    SASH: finish((55, 61, 59), .52, .21),
    SHADE: finish((66, 70, 66), .28, .15),
    PALE: finish((114, 124, 113), .28, .12),
    SKY: finish((111, 134, 146), .22, .17),
}
for key in (SHADE, PALE, SKY):
    PALETTE[key]['texture'] = str(Path(__file__).with_name('postal-window-glass.png'))


def plane(x, z, outward):
    return x, -outward, z


def extrude(builder, polygon, face, thickness, material, name):
    builder.prism(polygon, -face-thickness, -face, plane, material, name)


def glass(builder, polygon, face, material, name):
    extrude(builder, polygon, face, .008, material, name)
    part = builder.parts[-1]
    # World-space frontage coordinates keep the reflection continuous across panes.
    part['texcoords'] = [(x*.48+y*.09, z*.56+y*.17) for x,y,z in part['vertices']]


def sash(builder, lod, name, bounds, face, dividers, rows, glass_material):
    l, b, r, t = bounds
    width, height = r-l, t-b
    edge = min(.024, width*.032, height*.052)
    muntin = min(.019, width*.026, height*.044)
    xx = [l+edge, *[l+u*width for u in dividers], r-edge]
    zz = [b+edge, *[b+height*j/rows for j in range(1,rows)], t-edge]
    holes = []
    for j, (z0, z1) in enumerate(zip(zz, zz[1:])):
        for i, (x0, x1) in enumerate(zip(xx, xx[1:])):
            holes.append(box(x0 + (muntin/2 if i else 0),
                             z0 + (muntin/2 if j else 0),
                             x1 - (muntin/2 if i+1 < len(xx)-1 else 0),
                             z1 - (muntin/2 if j+1 < len(zz)-1 else 0)))
    grille = box(l,b,r,t).difference(unary_union(holes))
    extrude(builder, grille, face, .039, SASH, name+' | sash and glazing bars')
    if lod is True or lod == 'lod':
        glass(builder, box(l+edge,b+edge,r-edge,t-edge), face+.040, glass_material, name+' | glazing')
    else:
        for i, pane in enumerate(holes):
            glass(builder, pane, face+.019, glass_material, name+f' | pane {i+1:02d}')


def add_window(builder, lod, label, x0, x1, z0, z1, front_y, *,
               family='narrow', glass_finish='grey', upper_rows=2, lower_rows=4):
    """Install one closed sash assembly in a clear opening, dimensions in metres.

    Each narrow member of a paired masonry opening is supplied separately.
    The broad stair windows each take one continuous frame, with three lights
    on the second floor and four on the third.
    upper_rows/lower_rows allow different, photographically measured rail counts.
    """
    if family not in ('single','narrow','wide','wide-four'):
        raise ValueError(f'Unknown postal office window family {family}')
    if min(x1-x0,z1-z0) <= .24 or min(upper_rows,lower_rows)<1:
        raise ValueError(f'Invalid opening or row count at {label}')
    glass_material = {'grey': PALE, 'shaded': SHADE, 'sky': SKY}[glass_finish]
    prefix = 'Postal | '+label
    w,h = x1-x0,z1-z0
    rim = min(.040,w*.059,h*.047)
    rail = min(.066,.033*h)
    cross = z0+h*(.65 if family in ('single','narrow') else .64)
    inner_l,inner_r=x0+rim,x1-rim
    lower = (inner_l,z0+rim,inner_r,cross-rail/2)
    upper = (inner_l,cross+rail/2,inner_r,z1-rim)
    fixed = box(x0,z0,x1,z1).difference(unary_union([box(*upper),box(*lower)]))
    extrude(builder, fixed, front_y, .078, FIXED, prefix+' | perimeter and transom')
    dividers = {'single': (), 'narrow': (.46,), 'wide': (1/3, 2/3),
                'wide-four': (.25, .50, .75)}[family]
    for name,(l,b,r,t),rows,material in (
            ('lower',lower,lower_rows,glass_material),
            ('upper',upper,upper_rows,PALE if glass_finish=='shaded' else glass_material)):
        # A two-millimetre fitting allowance keeps the sash edges distinct.
        sash(builder, lod, prefix+' | '+name, (l+.002,b+.002,r-.002,t-.002),
             front_y+.014, dividers, rows, material)
