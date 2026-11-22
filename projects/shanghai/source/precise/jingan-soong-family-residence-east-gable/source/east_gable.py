"""The open balcony gable and adjoining garden bay of 369 North Shaanxi Road.

Photo-local coordinates are metres. X increases towards the north side of
the gable, Y into the house. The narrower model ends at the first roof join.
"""
from math import ceil, hypot
import sys
from render_finish import ATLAS, plaster_uv
from pathlib import Path
from shapely.geometry import Polygon, box

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Facade

PLASTER = 'warm pebble dash'
BASE = 'dusty rose brick'
JOINT = 'warm lime joint'
STONE = 'ivory rendered column'
TIMBER = 'weathered dark timber'
EDGE = 'grey painted verge'
GUTTER = 'green eaves and gutter'
ROOF = 'grey ribbed roof'
SEAM = 'raised roof seam'
SASH = 'green black shutter'
TILT = 'louvre leading edge'
GLASS = 'shaded window glass'
SILL = 'pale window sill'
CHIM = 'cream chimney stack'
PALETTE = {material: dict(color=list(rgb), roughness=roughness, metallic=metallic)
           for material, rgb, roughness, metallic in [
               (PLASTER, (.81, .755, .615), .95, 0), (BASE, (.75, .56, .475), .91, 0),
               (JOINT, (.67, .565, .49), .96, 0), (STONE, (.875, .835, .732), .84, 0),
               (TIMBER, (.167, .127, .107), .76, 0), (EDGE, (.315, .335, .337), .79, 0),
               (GUTTER, (.182, .273, .228), .67, .07), (ROOF, (.439, .447, .422), .86, .02),
               (SEAM, (.393, .404, .38), .85, .01), (SASH, (.132, .158, .142), .71, 0),
               (TILT, (.19, .212, .177), .75, 0), (GLASS, (.26, .35, .339), .31, .10),
               (SILL, (.85, .825, .74), .89, 0), (CHIM, (.796, .761, .638), .93, 0)]}

PALETTE[PLASTER].update(color=[1.,1.,1.],texture=str(ATLAS))

DECK, EAVE, RIDGE = 3.91, 6.54, 9.63
HALF, FRONT, BACK = 3.46, -.25, 7.55
BAY_WALL = [(-3.16, 7.40), (-4.39, 7.40), (-5.49, 6.35),
            (-5.49, 4.57), (-4.37, 3.49), (-3.16, 3.49)]


def slab(b, points, low, high, material, name):
    b.plan_prism(Polygon(points), low, high, material, name)


def plank(b, start, end, width, thickness, material, label):
    """Rectangular beam with its broad face in XZ for bargeboards and braces."""
    spread, rise = end[0] - start[0], end[2] - start[2]
    length = hypot(spread, rise)
    basis = [(spread / length, 0, rise / length), (0, 1, 0), (-rise / length, 0, spread / length)]
    b.box(tuple((p+q)/2 for p,q in zip(start, end)), (length, thickness, width), material, basis, label)


def roof_panel(b, points, material, label):
    n = len(points)
    vertices = list(points) + [(x, y, z-.105) for x, y, z in points]
    faces = [tuple(range(n)), tuple(reversed(range(n, 2*n)))]
    faces += [(i, i+n, (i+1)%n+n, (i+1)%n) for i in range(n)]
    b.add(vertices, faces, material, label)


def lean_sheet(b, left, right, tip, lod, label):
    roof_panel(b, [left, right, tip], ROOF, label+'/surface')
    if lod:
        return
    distance = hypot(right[0]-left[0], right[1]-left[1])
    for i in range(1, ceil(distance/.14)):
        s = i/ceil(distance/.14)
        foot = tuple(a+(c-a)*s for a,c in zip(left,right))
        start = tuple((1-.06)*v+.06*t for v,t in zip(foot,tip))
        end = tuple(.14*v+.86*t for v,t in zip(foot,tip))
        b.tube([start, end], .014, SEAM, 5, label+'/hip ribs')


def brick_base(face, top=1.23, lod=False):
    face.prism(box(-face.length/2, .05, face.length/2, top), -.18, .016, BASE, 'rose plinth')
    for j in range(1, round(top/.084)):
        z = .05+j*.084
        face.box(0, z, face.length, .009 if not lod else .012, .012, .022, JOINT, 'horizontal bed joints')
        if not lod:
            u = -face.length/2 + (.13 if j%2 else .25)
            while u < face.length/2-.02:
                face.box(u, z-.041, .007, .071, .009, .022, JOINT, 'staggered brick joint')
                u += .265


def shutter(face, u, z0, w, h, lod, name):
    """Two closed shutter leaves under a shallow reveal, with sloping louvers."""
    shape = box(u-w/2, z0, u+w/2, z0+h)
    face.prism(shape, -.172, -.146, GLASS, name+'/shadow glass')
    face.prism(shape.difference(shape.buffer(-.052, join_style=2)), -.14, -.04, SASH, name+'/jambs')
    half = (w-.117)/2
    for sign in (-1,1):
        center = u+sign*(half/2+.006)
        face.box(center, z0+h/2, half, h-.112, .044, -.105, SASH, name+'/leaf')
        if not lod:
            blade_count = max(6, int(h/.072))
            for j in range(blade_count):
                # A triangular lip leaves a dark line below each higher edge.
                z = z0+.085+(h-.17)*(j+.5)/blade_count
                face.box(center, z, half-.046, .018, .052, -.066, TILT, name+'/louvre lips')
    face.box(u, z0-.058, min(face.length-.018, w+.145), .120, .26, .016, SILL, name+'/sill')
    return shape


def window_wall(face, windows, height, lod):
    cuts = [box(u-w/2, z, u+w/2, z+h) for u,z,w,h in windows]
    face.wall(0, height, cuts, .23, PLASTER)
    brick_base(face, 1.19, lod)
    for i,(u,z,w,h) in enumerate(windows,1):
        shutter(face,u,z,w,h,lod,'closed shutter '+str(i))


def gabled_roof(b,lod):
    for side in (-1,1):
        edge = side*(HALF+.13)
        e,y0,y1 = EAVE+.07, FRONT-.20, BACK+.06
        points = [(edge,y0,e), (edge,y1,e), (0,y1,RIDGE), (0,y0,RIDGE)]
        roof_panel(b, points if side<0 else list(reversed(points)), ROOF, 'east roof/grey sheet')
        b.tube([(edge,y0,e-.03),(edge,y1,e-.03)], .071, GUTTER, 7 if lod else 12, 'east roof/gutter')
        rib_count = 22 if lod else 68
        for j in range(1,rib_count):
            y = y0+(y1-y0)*j/rib_count
            b.tube([(edge*.98,y,e+.065),(edge*.035,y,RIDGE-.04)], .016, SEAM, 4 if lod else 6, 'east roof/standing ribs')
        plank(b,(0,y0-.054,RIDGE),(edge,y0-.054,e),.254,.157,EDGE,'east gable/raised verge')
        count = 8 if lod else 15
        for j in range(1,count):
            t = j/count
            b.box((t*edge,y0-.151,RIDGE+(e-RIDGE)*t-.023),(.060,.038,.069),TIMBER,label='east gable/square verge studs')
    b.tube([(0,FRONT-.21,RIDGE+.02),(0,BACK+.06,RIDGE+.02)],.065,GUTTER,8,'east roof/ridge cap')
    outline=Polygon([(-HALF,EAVE-.04),(0,RIDGE-.11),(HALF,EAVE-.04)])
    face=Facade(b,(-HALF,FRONT),(HALF,FRONT),'east gable')
    face.prism(outline,-.16,.015,PLASTER,'half timbered tympanum')
    for x in (-2.05,-1.12,0,1.12,2.05):
        z = RIDGE-.16-(RIDGE-EAVE)*abs(x)/HALF
        face.box(x,(EAVE+z)/2,.145,z-EAVE,.12,.05,TIMBER,'gable verticals')
    for s in (-1,1):
        plank(b,(s*.48,FRONT-.083,EAVE+.04),(s*1.87,FRONT-.083,EAVE+1.18),.125,.092,TIMBER,'east gable/diagonal brace')
    b.box((0,FRONT-.04,EAVE-.03),(2*HALF,.26,.24),TIMBER,label='east balcony/lintel')


def loggia(b,lod):
    xy=[(-3.19,-.22),(3.19,-.22),(3.19,1.94),(-3.19,1.94)]
    slab(b,xy,DECK-.19,DECK,SILL,'east balcony/projecting floor')
    for x in (-2.92,2.92):
        b.box((x,.035,.617),(.60,.61,1.234),BASE,label='east portico/rose pedestal')
        b.box((x,.035,1.25),(.68,.69,.10),SILL,label='east portico/pedestal cap')
        profile=[(1.30,.262),(1.37,.28),(1.41,.225),(1.54,.217),(3.43,.185),
                 (3.49,.216),(3.52,.241),(3.57,.248),(3.60,.274),(3.64,.286),(3.70,.29)]
        b.lathe((x,.035),profile,STONE,12 if lod else 28,'east portico/turned column')
        b.box((x,.035,3.724),(.63,.63,.09),SILL,label='east portico/square capital')
        for y in (FRONT+.18,1.80):
            b.box((x,y,(DECK+EAVE)/2),(.178,.17,EAVE-DECK),TIMBER,label='east balcony/posts')
    runs=[((-2.94,-.085),(2.94,-.085)),((-2.94,1.84),(-2.94,-.085)),((2.94,-.085),(2.94,1.84))]
    for a,c in runs:
        f=Facade(b,a,c,'east balcony')
        for z,h,depth in ((DECK+.13,.115,.12),(DECK+1.02,.116,.16)):
            f.box(0,z,f.length,h,depth,0,TIMBER,'balcony rails')
        n=max(3,round(f.length/.242))
        for j in range(1,n):
            f.box(-f.length/2+f.length*j/n,DECK+.575,.052,.83,.064,0,TIMBER,'open balusters')
    east=Facade(b,(-3.06,1.77),(3.06,1.77),'rear of east balcony')
    east.wall(DECK,EAVE,[box(-1.10,DECK+.06,1.10,DECK+2.02)],.22,PLASTER)
    east.window(box(-1.10,DECK+.06,1.10,DECK+2.02),2,3,TIMBER,False,GLASS,'shaded opening')
    # The column arcade encloses a second, shallow faceted window at ground level.
    a=[(-3.13,1.75),(-1.78,.83),(1.78,.83),(3.13,1.75)]
    for i,(p,q) in enumerate(zip(a,a[1:])):
        f=Facade(b,p,q,'east portico bay '+str(i+1))
        w=(.95 if i!=1 else 1.24)
        window_wall(f,[(0,1.39,w,2.0)],DECK-.17,lod)
    for x in (-3.15,3.15):
        b.box((x,4.63,DECK/2),(.20,5.78,DECK),PLASTER,label='east side/short return')
        b.box((x,4.65,(DECK+EAVE)/2),(.20,5.80,EAVE-DECK),PLASTER,label='east side/upper return')
    b.box((0,BACK-.09,EAVE/2),(6.34,.18,EAVE),PLASTER,label='rear/concealed join')
    for side in (-1,1):
        b.box((side*(HALF-.14),3.63,EAVE-.07),(.50,7.82,.15),TIMBER,label='east roof/timber soffits')


def garden_bay(b,lod):
    for i,(a,c) in enumerate(zip(BAY_WALL,BAY_WALL[1:])):
        f=Facade(b,a,c,'garden canted bay '+str(i+1))
        openings=[(0,1.36,min(f.length-.20,1.07),2.07)] if i in (1,2,3) else []
        window_wall(f,openings,4.14,lod)
    slab(b,BAY_WALL,4.12,4.26,GUTTER,'garden bay/eaves')
    apex=(-3.31,5.46,8.78)
    for i,(a,c) in enumerate(zip(BAY_WALL,BAY_WALL[1:])):
        lean_sheet(b,(*a,4.27),(*c,4.27),apex,lod,'garden bay/hip '+str(i+1))
    b.lathe(apex[:2],[(8.77,.09),(8.91,.073),(8.99,.048),(9.24,.023),(9.31,.014)],GUTTER,8 if lod else 14,'garden bay/hip finial')
    # A broad dormer breaks the slope over the three faceted shuttered windows.
    a=(-4.96,6.27);c=(-4.96,4.66)
    face=Facade(b,a,c,'garden dormer')
    cut=box(-.67,5.25,.67,6.26);face.wall(5.05,6.43,[cut],.13,PLASTER)
    shutter(face,0,5.25,1.34,1.01,lod,'dormer louvers')
    for y in (4.62,6.31):
        roof_panel(b,[(-4.98,y,5.05),(-3.31,y,6.04),(-3.31,y,7.31),(-4.98,y,6.44)],TIMBER,'garden dormer/cheeks')
    roof_panel(b,[(-5.12,4.52,6.47),(-3.24,4.52,7.41),(-3.24,6.40,7.41),(-5.12,6.40,6.47)],ROOF,'garden dormer/sloping lid')
    b.tube([(-5.12,4.52,6.47),(-5.12,6.40,6.47)],.05,GUTTER,8,'garden dormer/gutter')
    b.box((.86,6.48,8.64),(.92,.65,2.72),CHIM,label='shared roof/cream stack')
    b.box((.86,6.48,9.98),(1.00,.75,.16),SILL,label='shared roof/coping')
    for x in (.57,.85,1.13):
        b.box((x,6.48,10.13),(.15,.34,.17),CHIM,label='shared roof/crown details')


def add_geometry(builder,lod):
    loggia(builder,lod)
    gabled_roof(builder,lod)
    garden_bay(builder,lod)
    for part in builder.parts:
        if part['material'] == PLASTER:
            part['texcoords'] = [(u,1-v) for u,v in (plaster_uv(*p) for p in part['vertices'])]
