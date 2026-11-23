"""The projecting street window from the third floor upward.

The local origin is on the existing wall, below the bay axis. X is horizontal,
Y increases into the building and Z is height above street level. The optional
second-floor window remains on the main wall. Supply the host's floor levels in
floor_z, including the terminal height, or use z_base/storey_height.
"""
from shapely.geometry import Polygon, box
from materials import STUCCO, BAND, PALE, GLASS, FRAME

DEFAULT_FLOORS = (5.622, 9.132, 12.718, 16.40)


def _levels(layout):
    rows = int(layout.get('window_rows', 3))
    if not 1 <= rows <= 3:
        raise ValueError('window_rows must be one, two or three')
    if 'floor_z' in layout:
        levels = list(layout['floor_z'][:rows + 1])
    elif 'z_base' in layout or 'storey_height' in layout:
        base = layout.get('z_base', DEFAULT_FLOORS[0])
        rise = layout.get('storey_height', 3.51)
        levels = [base + k * rise for k in range(rows + 1)]
    else:
        levels = list(DEFAULT_FLOORS[:rows + 1])
    if len(levels) != rows + 1 or any(high <= low for low, high in zip(levels, levels[1:])):
        raise ValueError('floor_z must include all floor starts and the terminal height')
    return levels


def _dimensions(layout):
    width = float(layout.get('width', 3.05))
    projection = float(layout.get('projection', .822))
    if width <= 1 or projection <= .20:
        raise ValueError('the window bay needs a positive clear span and return')
    centre = float(layout.get('x_center', 0.))
    return centre - width / 2, centre + width / 2, projection


def openings(layout):
    """Front and main-wall clear openings; the caller cuts the supporting shell."""
    left, right, proj = _dimensions(layout)
    width = right - left
    levels = _levels(layout)
    jamb = layout.get('jamb', .112 * width)
    clear = []
    if layout.get('lower_window', False):
        foot = layout.get('lower_sill_z', levels[0] - 1.402)
        head = layout.get('lower_head_z', levels[0] - .332)
        lower_jamb = layout.get('lower_jamb', .18 * width)
        clear.append(dict(floor=2, x0=left+lower_jamb, x1=right-lower_jamb,
                          z0=foot, z1=head, face_y=0.))
    for floor, (base, top) in enumerate(zip(levels, levels[1:]), 3):
        sill, head = ((.247,.842), (.350,.837), (.321,.790))[floor-3]
        clear.append(dict(floor=floor, x0=left+jamb, x1=right-jamb,
                          z0=base + sill*(top-base), z1=base + head*(top-base),
                          face_y=-proj))
    return clear


def _box(b, x0, x1, y0, y1, z0, z1, material, name):
    b.box(((x0+x1)/2, (y0+y1)/2, (z0+z1)/2),
          (x1-x0, y1-y0, z1-z0), material, label=name)


def _section(b, left, right, y, span, rise, down, lod, name):
    """A single water-shedding four-step console; its two sides use one outline."""
    # Each step has one tall riser and a small second rectangular bead at its foot.
    # In the photograph the feet converge on the original second-floor wall.
    z = rise
    edge = [(0., z + .022), (y, z + .022)]
    for step in range(4):
        nose = y + step * span/4
        z = rise - step*down/3
        edge.append((nose, z))
        if not lod:
            edge.extend([(nose + .145*span, z),
                         (nose + .145*span, z - .025),
                         (nose + .196*span, z - .025),
                         (nose + .196*span, z - .049)])
        edge.append((nose + span/4, z - (.049 if not lod else 0.)))
    shape = Polygon(list(dict.fromkeys(edge)))
    b.prism(shape, left, right, lambda yy, zz, xx: (xx, yy, zz), STUCCO, name)


def _sashes(b, row, layout, prefix):
    x0,x1,z0,z1=(row[k] for k in ('x0','x1','z0','z1'))
    face = row['face_y'] + .087
    width, height = x1-x0, z1-z0
    rim = min(.048, .025*width)
    cross = min(.050, .028*width)
    blades = int(layout.get('lower_lights' if row['floor']==2 else 'upper_lights', 3))
    if blades < 1:
        raise ValueError('a window requires at least one light')
    prefix += f" F{row['floor']}"
    # The photographic window is a continuous steel sash within one masonry aperture.
    for side,x in enumerate((x0,x1-rim)):
        _box(b,x,x+rim,face,face+.064,z0,z1,FRAME,f'{prefix} jamb {side+1}')
    for side,z in enumerate((z0,z1-rim)):
        _box(b,x0+rim,x1-rim,face,face+.064,z,z+rim,FRAME,f'{prefix} rail {side+1}')
    inside0, inside1 = x0+rim, x1-rim
    stride = (inside1-inside0)/blades
    transom_fraction = {2:.47, 3:.36, 4:.54, 5:.54}[row['floor']]
    division = z0 + transom_fraction*height
    for col in range(blades):
        a = inside0 + col*stride + (cross/2 if col else 0.)
        c = inside0 + (col+1)*stride - (cross/2 if col+1<blades else 0.)
        if col:
            _box(b,a-cross,a,face+.001,face+.062,z0+rim,z1-rim,FRAME,
                 f'{prefix} mullion {col}')
        _box(b,a,c,face+.005,face+.058,division-.016,division+.016,FRAME,
             f'{prefix} transom {col+1}')
        for idx,(low,high) in enumerate(((z0+rim,division-.016),(division+.016,z1-rim))):
            _box(b,a,c,face+.035,face+.047,low,high,GLASS,
                 f'{prefix} light {col+1}.{idx+1}')


def add_corbel_bay(b, layout, lod=False):
    """Create a bay at local X centre, including both consoles and optional F2 sash."""
    left,right,proj = _dimensions(layout)
    width = right-left
    levels = _levels(layout)
    base,top = levels[0],levels[-1]
    name = layout.get('label','Wing bay')
    if len(name.encode('utf-8')) > 28:
        raise ValueError('use a short unique bay label')
    plate = float(layout.get('plate', .148))
    drop = float(layout.get('corbel_drop', 1.104))
    thick = float(layout.get('corbel_width', .074*width))
    clear = openings(layout)
    _box(b,left,right,-proj,0.,base-plate,base,PALE,f'{name} exposed soffit')
    for side,(a,c) in enumerate(((left,left+thick),(right-thick,right))):
        _section(b,a,c,-proj,proj,base-plate,drop,lod,f'{name} four-step console {side+1}')
        # The side cheeks close the projection and stop on the original façade plane.
        t = min(.14, .05*width)
        x = left if side==0 else right-t
        _box(b,x,x+t,-proj+.15,0.,base,top,STUCCO,f'{name} return {side+1}')
    wall = box(left,base,right,top)
    for row in clear:
        if row['floor'] >= 3:
            wall = wall.difference(box(row['x0'],row['z0'],row['x1'],row['z1']))
        _sashes(b,row,layout,name)
    b.prism(wall,proj-.15,proj,lambda x,z,d:(x,-d,z),STUCCO,f'{name} pierced front')
    mid = (left+right)/2
    for row in clear:
        if row['floor'] < 3:
            continue
        floor = row['floor']
        bottom = levels[floor-3]
        # The paired vertical returns at the ends of the opening have a shallow
        # raised arris. They end at the horizontal belt rather than the glass.
        for side,x in enumerate((row['x0']-.082, row['x1']+.038)):
            _box(b,x,x+.044,-proj-.019,-proj,bottom+.053,levels[floor-2]-.018,
                 PALE,f'{name} F{floor} jamb arris {side+1}')
        _box(b,left,right,-proj-.027,-proj,bottom,bottom+.053,BAND,f'{name} F{floor} drip')
        _box(b,row['x0']-.045,row['x1']+.045,-proj-.055,-proj,row['z0']-.048,row['z0'],
             BAND,f'{name} F{floor} sill')
        # A narrow fluted vertical panel divides the unpierced sill field in photo 08.
        panel = .181*width
        _box(b,mid-panel/2,mid+panel/2,-proj-.026,-proj,bottom+.054,row['z0']-.049,
             BAND,f'{name} F{floor} fluted panel')
        for idx in range(3):
            x = mid + (idx-1)*panel*.28
            _box(b,x-.009,x+.009,-proj-.039,-proj-.026,bottom+.054,row['z0']-.049,
                 PALE,f'{name} F{floor} flute {idx+1}')
    return clear
