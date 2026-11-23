"""The photographed lane elevation of Nos. 3–4, with the No. 3 entrance.

Axes and materials use placement.Facade. Source dimensions are recorded in
house-three-two-registered-views.json. The permanent wall and 2013 gate are
shown, with the later canopy documented separately in the measurement notes.
"""
from math import cos, radians, sin
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from materials import BOARD, BRICK, CREAM, DARK, DOOR, GLASS, IRON, LETTER, OAK, SASH, SILL, STEP
from joinery import segmental, window

BIG = (-1.24, 6.32, 7.60, 10.64, 0.00)
SMALL = (2.75, 6.85, 5.73, 8.22, 0.96)
FLOOR = 3.65
# Window controls are the outer frame rectangles on the plaster or brick wall.
MAIN_LOWER = (1.28, 1.35, 2.13, 2.55)
MAIN_UPPER = [(0.18, 4.99, 1.07, 6.29), (1.31, 4.99, 2.11, 6.29),
              (2.40, 8.26, 3.04, 9.00)]
BAY_LOWER = [(3.39, 1.31, 3.97, 2.51), (4.58, 1.30, 5.26, 2.51),
             (5.91, 1.30, 6.48, 2.51)]
BAY_UPPER = [(3.23, 4.68, 4.10, 5.66), (4.80, 4.68, 5.55, 5.66)]


def _gable(f, bounds, windows, label, lod):
    a, b, eave, apex, front = bounds
    mid = (a + b) / 2
    shape = Polygon([(a, FLOOR), (b, FLOOR), (b, eave), (mid, apex), (a, eave)])
    web = shape.difference(unary_union([box(*v) for v in windows]))
    f.solid(web, front - .245, front, CREAM, label + ' plaster panels')

    def strip(points, width, name):
        f.band(points, width, front + .002, front + .065, OAK, label + ' ' + name, web)

    main = bounds == BIG
    lower_rail = 4.97 if main else 4.66
    for level, width in [(FLOOR + .10, .20), (lower_rail, .14), (eave - .065, .14)]:
        strip([(a, level), (b, level)], width, 'timber rail')
    posts = ([a+.07, .11, 1.22, 2.21, 3.18, 4.0, b-.07] if main
             else [a+.08, 3.18, 4.29, 4.73, 5.60, b-.07])
    for post in posts:
        strip([(post, FLOOR), (post, apex+.01)], .14, 'upright')
    strip([(a, eave-.03), (mid, apex-.025), (b, eave-.03)], .18, 'sloping verge timber')
    for x0,z0,x1,z1,cols,rows in [(*v, 2, 4 if main and i < 2 else 2)
                                     for i,v in enumerate(windows)]:
        window(f,x0,x1,z0,z1,front,cols,rows,label+' casement',lod,False)
    if main:
        strip([(.14,6.34),(2.23,6.34)],.15,'paired window lintel')
        strip([(1.09,9.12),(3.91,9.12)],.13,'attic lintel')
        strip([(1.36,9.03),(1.70,8.36),(2.19,7.63)],.135,'attic brace left')
        strip([(3.92,9.01),(3.66,8.48),(3.16,7.67)],.135,'attic brace right')
        strip([(a+.11,4.89),(a+.42,4.75),(a+.65,4.50),(a+.87,4.16),(a+.98,3.77)],.14,'lower curved brace')
        strip([(1.22,3.79),(1.47,4.22),(1.76,4.55),(2.14,4.82)],.14,'lower rising brace')
        strip([(2.19,8.25),(3.20,8.25)],.12,'attic sill')
    else:
        strip([(a+.39,6.57),(a+.82,6.18),(a+1.22,5.77)],.13,'upper diagonal')
        strip([(mid+.32,5.79),(mid+.66,6.20),(mid+1.03,6.58)],.13,'upper answering brace')


def _entrance(f,lod):
    # The 2013 camera sees the brick reveal, inset single grilled leaf and three treads.
    arch=segmental(0,1.0,.46,2.56,.12)
    left,right=BIG[:2]
    wall=box(left,.015,right,FLOOR).difference(unary_union([arch,box(*MAIN_LOWER)]))
    f.solid(wall,-.26,0,BRICK,'No 3 main red brick and arch reveal')
    f.solid(arch,-.31,-.295,DARK,'No 3 entrance shadow')
    f.rect(-.54,.58,.44,2.57,-.296,-.27,DARK,'No 3 recessed backing at jambs')
    # The door's central bar and closely spaced rods are visible through the segmental opening.
    frame=arch.difference(arch.buffer(-.052,join_style=2))
    f.solid(frame,-.231,-.179,IRON,'No 3 metal outer grille frame')
    f.solid(arch.buffer(-.054,join_style=2),-.29,-.265,DOOR,'No 3 shaded door backing')
    for h in [.55,.98,1.66,1.84,2.22,2.54]:
        width=.068 if 1.60<h<1.9 else .039
        f.rect(-.445,.445,h-width/2,h+width/2,-.218,-.168,IRON,'No 3 gate transverse rail')
    for n in range(1,8):
        x=-.45+n*.1125
        f.rect(x-.010,x+.010,.55,2.59,-.216,-.187,IRON,'No 3 gate iron rods')
    outer=segmental(0,1.31,.46,2.60,.22)
    zone=outer.difference(arch).intersection(box(-.68,2.55,.68,2.86))
    f.solid(zone,.002,.012,BRICK,'No 3 low segmental arch ring')
    if not lod:
        for n in range(1,13):
            x=-.59+n*.09
            f.band([(x,2.52),(x*1.13,2.85)],.009,.014,.016,SILL,'No 3 arch voussoir joint',zone)
    for level,foot0,foot1,extent in [(.15,-.89,.89,.91),(.30,-.83,.83,.64),(.46,-.70,.70,.33)]:
        bottom={.15:.012,.30:.15,.46:.30}[level]
        f.rect(foot0,foot1,bottom,level,-.02,extent,STEP,'No 3 brick entrance step')
    # Rounded numeral traced from the green plate. The small street text is below legible scale.
    cx,cz=-.70,2.40
    f.rect(cx-.113,cx+.113,cz-.108,cz+.108,.001,.017,BOARD,'No 3 green enamel address plate')
    outline=[(-.036,.039),(-.020,.066),(.012,.071),(.037,.054),(.036,.028),
             (.016,.008),(-.006,.005),(.016,.002),(.037,-.018),(.037,-.047),
             (.020,-.066),(-.010,-.071),(-.032,-.056),(-.038,-.039)]
    f.band([(cx+x,cz+z) for x,z in outline],.014,.018,.021,LETTER,'No 3 enamel numeral')
    x,z,xx,zz=MAIN_LOWER
    window(f,x,xx,z,zz,0,2,3,'No 3 adjacent ground casement',lod,False)
    f.rect(x-.08,xx+.08,1.175,1.338,-.1,.104,SILL,'No 3 full-height moulded brick sill')


def _projected_bay(f,lod):
    a,b,eave,apex,front=SMALL
    # Both returns meet the primary exterior without making a second solid wall at d0.
    for u, direction, base in [(a,-1,0),(b,1,front)]:
        side=f.face(u,-base,0,direction)
        side.rect(0,front,.015,FLOOR,-.19,-.001,BRICK,'small gable brick return')
        side.rect(0,front,FLOOR,eave,-.19,-.001,CREAM,'small gable plaster return')
        for level,width in [(FLOOR+.09,.17),(eave-.07,.14)]:
            side.rect(0,front,level-width/2,level+width/2,0,.057,OAK,'small gable return rail')
        side.band([(.09,FLOOR+.14),(.63,eave-.12)],.14,0,.057,OAK,'small gable return angle brace')
    base=box(a,.015,b,FLOOR).difference(unary_union([box(*v) for v in BAY_LOWER]))
    f.solid(base,front-.24,front,BRICK,'small gable projecting lower brick front')
    _gable(f,SMALL,BAY_UPPER,'small gable',lod)
    for i,(x,z,xx,zz) in enumerate(BAY_LOWER):
        if i:
            window(f,x,xx,z,zz,front,2,3,'projected bay lower light '+str(i+1),lod)
            continue
        # A full-height casement leaf stands open in Gao 08. Its steel dividers
        # split the leaf into two columns and four rows. The later photo shows a different leaf position.
        hole=box(x,z,xx,zz)
        f.solid(hole,front-.27,front-.25,DARK,'projected bay first window interior shade')
        f.solid(hole.difference(hole.buffer(-.044,join_style=2)),front-.23,front-.12,SASH,'projected bay first jamb')
        f.rect(x-.045,xx+.05,z-.066,z-.012,front-.12,front+.065,SILL,'projected bay red window sill')
        angle=radians(69)
        leaf=f.face(xx-.034,-front,-cos(angle),-sin(angle))
        w=xx-x-.068
        pane=box(0,z+.04,w,zz-.04)
        leaf.solid(pane,-.026,-.015,GLASS,'open casement four rows of glass')
        leaf.solid(pane.difference(pane.buffer(-.027,join_style=2)),0,.031,SASH,'open casement frame')
        leaf.rect(w/2-.011,w/2+.011,z+.06,zz-.06,.002,.031,SASH,'open casement central glazing bar')
        for k in (1,2,3):
            h=z+.04+(zz-z-.08)*k/4
            leaf.rect(.02,w-.02,h-.013,h+.013,.002,.029,SASH,'open casement transverse glazing bar')


def add_three_four(f,lod=False):
    _entrance(f,lod)
    _gable(f,BIG,MAIN_UPPER,'No 3 main gable',lod)
    _projected_bay(f,lod)
