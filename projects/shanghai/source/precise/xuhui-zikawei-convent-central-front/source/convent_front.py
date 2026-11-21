"""Garden front of the Xujiahui convent, following the August 2016 photograph."""
import math

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade

WHITE = 'warm lime render'
TRIM = 'pale molded plaster'
SHUTTER = 'dark green shutters'
LOUVER = 'green blade highlights'
GLASS = 'shadowed historic glazing'
WOOD = 'painted window joinery'
RED = 'weathered terracotta tiles'
RIDGE = 'terracotta hips and ridges'
IRON = 'dark iron railing'

PALETTE = {
    WHITE: {'color': [.819,.805,.731], 'roughness':.94},
    TRIM: {'color': [.905,.885,.804], 'roughness':.89},
    SHUTTER: {'color': [.165,.225,.177], 'roughness':.81},
    LOUVER: {'color': [.227,.295,.237], 'roughness':.87},
    WOOD: {'color': [.52,.54,.47], 'roughness':.83},
    GLASS: {'color': [.170,.215,.216], 'roughness':.45},
    RED: {'color': [.595,.310,.221], 'roughness':.91},
    RIDGE: {'color': [.706,.425,.311], 'roughness':.90},
    IRON: {'color': [.235,.225,.2], 'roughness':.77},
}
AXES = (-4.86,-1.62,1.62,4.86)
HALF = 6.76
EAVE = 12.82
PEAK = 16.68

def rounded_light(x,z,width,straight):
    r=width/2
    curve=[(x+r*math.cos(i*math.pi/28),z+straight+r*math.sin(i*math.pi/28)) for i in range(29)]
    return Polygon([(x-r,z),(x+r,z),*curve])

def shuttered_window(f,x,z,w,h,lod):
    opening=box(x-w/2,z,x+w/2,z+h)
    f.prism(opening,-.22,-.18,GLASS,'window glazing')
    rim=opening.difference(opening.buffer(-.075,join_style=2))
    f.prism(rim,-.16,-.055,WOOD,'sash frame')
    for side in (-1,1):
        cx=x+side*w*.245
        f.box(cx,z+h/2,w*.463,h-.16,.055,-.13,SHUTTER,'paired shutter leaves')
        count=8 if lod else 23
        for j in range(count):
            f.box(cx,z+.14+(h-.28)*(j+.5)/count,w*.407,.024 if lod else .021,.029,-.088,LOUVER,'slatted shutter blades')
    f.box(x,z-.11,w+.28,.17,.39,.075,TRIM,'plaster sill')
    return opening

def panel(f,lod):
    openings=[]
    for x in AXES:
        for z in (6.25,9.66):
            openings.append(shuttered_window(f,x,z,1.44,2.09,lod))
    low,high=5.55,EAVE-.03
    f.wall(low,high,openings,.48,WHITE)
    for x in [-6.54,-3.24,0,3.24,6.54]:
        f.box(x,9.22,.28,7.26,.24,.055,TRIM,'four-bay pier')
        for z in [5.71,9.31,12.53]:
            f.box(x,z,.49,.16,.38,.12,TRIM,'pier moulding')
    for z in [5.66,9.28,12.62]:
        f.box(0,z,13.62,.15,.38,.04,TRIM,'horizontal stringcourse')

def attic(f,lod):
    shell=Polygon([(-HALF,EAVE),(HALF,EAVE),(0,PEAK)])
    center=rounded_light(0,13.55,1.07,.69)
    lights=[center,box(-2.28,13.53,-1.61,14.19),box(1.61,13.53,2.28,14.19),rounded_light(0,15.20,.41,.32)]
    f.prism(shell.difference(unary_union(lights)),-.52,0,WHITE,'vented triangular attic')
    for light in lights:
        f.prism(light,-.32,-.28,SHUTTER,'dark attic louver')
        f.prism(light.buffer(.085,join_style=2).difference(light),-.03,.13,TRIM,'attic window hood')
        x0,z0,x1,z1=light.bounds
        for j in range(2 if lod else 7):
            z=z0+(z1-z0)*(j+1)/(3 if lod else 8)
            strip=light.intersection(box(x0,z-.013,x1,z+.013))
            f.prism(strip,-.265,-.245,LOUVER,'attic vent slats')
    for a,b in [((-6.92,EAVE),(0,PEAK+.10)),((0,PEAK+.10),(6.92,EAVE))]:
        f.line((*a,.13),(*b,.13),.13,TRIM,6 if lod else 10,'raking gable moulding')
    f.box(0,EAVE-.04,13.93,.24,.58,.10,TRIM,'gable base cornice')
    for x in (-6.75,6.75):
        prof=[(EAVE,.21),(EAVE+.17,.19),(EAVE+.21,.15),(EAVE+.29,.20),(EAVE+.41,.22),(EAVE+.49,.13),(EAVE+.58,.055)]
        f.builder.lathe((x,-.02),prof,TRIM,10 if lod else 18,'Garden gable / finials')

def wing(b,x,lod):
    f=Facade(b,(x-1.62,.7),(x+1.62,.7),'Recessed flank')
    holes=[shuttered_window(f,0,z,1.25,2.04,lod) for z in (6.19,9.63)]
    f.wall(5.55,EAVE-.37,holes,.42,WHITE)
    f.box(0,EAVE-.35,3.30,.23,.47,.10,TRIM,'return eave')
    # The two short returns stop before the smaller end gables.
    for y in (1.0,1.52,2.04,2.56,3.08,3.6):
        z=EAVE-.37+(y-.70)*.46
        b.box((x,y,z),(3.21,.59,.16),RED,label='Flanking red tiles / stepped plane')
        if not lod:b.tube([(x-1.58,y,z+.04),(x+1.58,y,z+.04)],.035,RIDGE,5,'Flanking tiles / courses')

def roof(b,lod):
    depth=3.60
    for side in (-1,1):
        x=side*HALF
        corners=[(0,-.06,PEAK+.02),(x,-.06,EAVE+.05),(x,depth,EAVE+.05),(0,depth,PEAK+.02)]
        points=corners+[(a,c,z-.15)for a,c,z in corners]
        faces=[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
        if side<0:faces=[tuple(reversed(face)) for face in faces]
        b.add(points,faces,RED,'Garden gable / pitched roof')
        for i in range(1,13 if lod else 30):
            t=i/(13 if lod else 30);xx=x*t;z=PEAK+.04+(EAVE-PEAK+.03)*t
            b.tube([(xx,.05,z),(xx,depth-.02,z)],.035,RIDGE,5,'Garden roof / curved tile courses')
    b.tube([(0,-.11,PEAK+.07),(0,depth,PEAK+.07)],.09,RIDGE,8,'Garden roof / ridge')

def porch(b,lod):
    # The garden photograph exposes the two western axes of the glazed porch.
    # Tree-covered eastern glazing and its supports are outside this component.
    f=Facade(b,(-6.62,-1.77),(-.25,-1.77),'Visible west porch')
    for x in (-1.57,1.57):
        for z in (.30,3.03):
            pane=box(x-1.41,z,x+1.41,z+2.36)
            f.prism(pane,-.14,-.11,GLASS,'porch window')
            for u in (x-1.42,x,x+1.42):
                f.box(u,z+1.18,.093,2.4,.16,.007,WOOD,'porch glazing posts')
            for v in (z,z+.77,z+2.36):
                f.box(x,v,2.87,.075,.17,.005,WOOD,'porch transom')
    for x in (-3.12,0,3.12):f.box(x,2.72,.21,5.44,.31,.022,TRIM,'porch uprights')
    for z in (.14,2.80,5.54):f.box(0,z,6.46,.25,.46,.033,TRIM,'porch floor and cornice')
    b.box((-3.435,-.74,5.52),(6.42,2.23,.21),WHITE,label='Garden porch / terrace')
    f.box(0,6.16,6.45,.06,.057,-.01,IRON,'terrace handrail')
    for i in range(11 if lod else 21):
        x=-3.11+6.22*i/(10 if lod else 20)
        f.box(x,5.90,.035,.52,.043,-.01,IRON,'terrace balusters')

def facade(b,lod=False):
    f=Facade(b,(-HALF,0),(HALF,0),'Garden centre')
    panel(f,lod)
    attic(f,lod)
    roof(b,lod)
    wing(b,-8.38,lod)
    wing(b,8.38,lod)
    porch(b,lod)
