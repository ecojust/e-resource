"""The inscribed portal and vertical staircase glazing of the York Building."""
from pathlib import Path
from math import cos, sin, radians
from shapely.geometry import box
from shapely import affinity
from shapely.ops import unary_union
from photo_architecture import Facade
from sign_lettering import lettering_shapes

STONE = 'ivory grooved render'
REVEAL = 'warm stone reveals'
CAP = 'pale cornice'
STEEL = 'black staircase steel'
GLASS = 'cool grey stair glass'
GREEN = 'green painted gate'
DARK = 'dark inner door'
BRASS = 'old gold letters'
PLAQUE = 'green address enamel'
WHITE = 'white enamel numerals'
PALETTE = {key:{'color':rgb,'roughness':rough} for key,rgb,rough in (
    (STONE,[.83,.80,.72],.86),(REVEAL,[.69,.65,.56],.93),(CAP,[.86,.84,.76],.82),
    (STEEL,[.17,.18,.19],.73),(GLASS,[.42,.47,.50],.38),(GREEN,[.22,.34,.30],.70),
    (DARK,[.14,.17,.16],.90),(BRASS,[.77,.58,.29],.48),
    (PLAQUE,[.19,.39,.31],.68),(WHITE,[.90,.91,.84],.71))}
FONT = Path(__file__).parent/'font/YorkNameplate.otf'
AXES = (-.94,0.,.94)
GLASS_BASE, GLASS_HEAD = 6.50,23.65
# Strong horizontal transoms in the rectified 2016 photo, top down on its 740 px scale.
TRANSOMS_PX = (0,16,59,103,147,191,241,281,326,374,418,464,510,557,603,650,699,740)

def rect(x0,z0,x1,z1):
    return box(x0,z0,x1,z1)

def put(f,shape,back,front,material,name):
    f.prism(shape,back,front,material,name)

def text(f,chars,x,z,width,height,back,front,mat,label,lod):
    for char,shape in lettering_shapes(chars,width,height,font=FONT):
        shape=shape.simplify(.0025 if lod else .00075,preserve_topology=True)
        put(f,affinity.translate(shape,xoff=x,yoff=z),back,front,mat,label+' '+char)

def open_light(builder,axis,z,width,height):
    # Two pivoted lights are visible in the north strip in the upward 2016 photograph.
    theta=radians(28)
    def tilted(u,v,d):
        return (axis+u*cos(theta)-d*sin(theta),.115-u*sin(theta)-d*cos(theta),z+v)
    outline=rect(0,0,width,height)
    cross=rect(0,height*.50-.012,width,height*.50+.012)
    inner=outline.buffer(-.021,join_style=2).difference(cross)
    builder.prism(inner,-.004,.004,tilted,GLASS,'north outward casement glazing')
    builder.prism(outline.difference(inner),.002,.027,tilted,STEEL,'north outward casement frame')

def stair_windows(builder,f,lod):
    outer=rect(-1.74,6.32,1.74,24.05)
    openings=[]
    for i,axis in enumerate(AXES):
        left,right=axis-.364,axis+.364
        hole=rect(left,GLASS_BASE,right,GLASS_HEAD);openings.append(hole)
        put(f,hole,-.17,-.141,GLASS,'stair glass '+str(i+1))
        steel=[rect(axis-.016,GLASS_BASE,axis+.016,GLASS_HEAD)]
        levels=[GLASS_HEAD-v/740*(GLASS_HEAD-GLASS_BASE) for v in TRANSOMS_PX]
        for top,bottom in zip(levels,levels[1:]):
            steel.append(rect(left,top-.030,right,top+.030))
            for k in (1,2):
                z=top+(bottom-top)*k/3
                steel.append(rect(left,z-.011,right,z+.011))
        inner=hole.buffer(-.035,join_style=2).difference(unary_union(steel))
        put(f,hole.difference(inner),-.141,-.091,STEEL,'stair steel grid '+str(i+1))
        if not lod:
            for z in levels[1:-1]:
                put(f,rect(left,z-.017,right,z+.017),-.091,-.057,STEEL,'projecting transom '+str(i+1))
    put(f,outer.difference(unary_union(openings)),-.175,.024,STONE,'three open stair reveals')
    for axis in (-.47,.47):
        put(f,rect(axis-.085,6.31,axis+.085,24.04),.022,.111,CAP,'cream stair mullion')
    if not lod:
        for top,bottom in [(levels[6],levels[7]),(levels[13],levels[14])]:
            open_light(builder,AXES[0]-.345,bottom+.035,.334,top-bottom-.06)
    put(f,rect(-1.73,GLASS_HEAD,1.73,23.80),.017,.096,CAP,'window head band')

def entrance(f,lod):
    door=rect(-1.56,0,1.56,3.11);overlight=rect(-1.53,4.06,1.53,4.96)
    portal=rect(-3.05,0,3.05,6.28)
    put(f,portal.difference(unary_union([door,overlight])),-.48,.073,STONE,'recessed stone portal')
    put(f,rect(-1.51,.035,1.51,3.07),-.505,-.487,DARK,'closed inner gate')
    # The gate has four linked vertical fret panels, and a fixed horizontal grille above.
    gate=rect(-1.50,.045,1.50,2.42);cuts=[]
    for j in range(4):
        left=-1.47+.74*j;right=left+.72
        for k in range(5):
            x=left+.049+k*.133
            cuts.append(rect(x,.22,x+.087,2.29))
        cuts.append(rect(left+.065,.080,right-.065,.139))
    put(f,gate.difference(unary_union(cuts)),-.477,-.437,GREEN,'four vertical iron gate panels')
    fixed=rect(-1.51,2.42,1.51,3.07)
    bars=[rect(-1.51,z-.016,1.51,z+.016)for z in (2.55,2.73,2.91)]
    bars += [rect(x-.018,2.42,x+.018,3.07)for x in (-.52,.52)]
    put(f,fixed.difference(fixed.buffer(-.040,join_style=2).difference(unary_union(bars))),-.47,-.425,GREEN,'gate fixed upper grille')
    if not lod:
        for j in range(4):
            left=-1.47+.74*j
            for k in (0,1,2):
                h=rect(left+.033+k*.017,.166+k*.019,left+.68-k*.017,2.35-k*.019)
                bead=h.difference(h.buffer(-.008,join_style=2))
                put(f,bead,-.436,-.424,GREEN,'gate stepped border')
    put(f,overlight,-.26,-.222,GLASS,'entrance overlight')
    bars=[rect(x-.017,4.06,x+.017,4.96) for x in (-1.06,-.70,-.34,.015,.38,.74,1.10)]
    bars.extend([rect(-1.53,4.18,1.53,4.20),rect(-1.53,4.87,1.53,4.90)])
    put(f,overlight.difference(overlight.buffer(-.038,join_style=2).difference(unary_union(bars))),-.221,-.172,STEEL,'eight overlight panes')
    put(f,rect(-1.57,3.11,1.57,4.04),.074,.101,CAP,'inscription stone')
    # The 2016 frontal portrait leaves almost a character's width between gold letters.
    for char,axis in zip('金陵大樓',(-.920,-.305,.305,.920)):
        text(f,char,axis,3.57,.308,.295,.101,.132,BRASS,'building inscription',lod)
    put(f,rect(1.60,3.08,1.91,3.31),.073,.112,PLAQUE,'address plate 29')
    text(f,'29',1.755,3.208,.188,.104,.112,.122,WHITE,'address',lod)
    put(f,rect(-3.06,6.14,3.06,6.32),.06,.173,CAP,'shop fascia above entrance')
    put(f,rect(-2.98,5.94,2.98,6.14),.054,.115,REVEAL,'fascia lower edge')
    # Closely spaced vertical grooves in the two outer jambs and their connecting lintel.
    grooves=[]
    for k in range(111):
        x=-2.99+k*.054
        bottom=0 if abs(x)>1.98 else 5.18
        grooves.append(rect(x,bottom,x+(.013 if not lod else .018),5.92))
    outer=rect(-3.00,0,3.00,5.94).difference(rect(-1.98,-.02,1.98,5.18))
    field=outer.difference(unary_union(grooves[::2] if lod else grooves))
    put(f,field,.074,.105,CAP,'scored U-shaped stone surround')

def add_building(builder,lod):
    f=Facade(builder,(-3.06,0),(3.06,0),'York')
    entrance(f,lod)
    stair_windows(builder,f,lod)
