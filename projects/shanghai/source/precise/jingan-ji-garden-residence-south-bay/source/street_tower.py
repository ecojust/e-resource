"""South street-facing polygonal window tower of 1510 West Beijing Road.

The face widths come from the four south OSM vertices. The photograph supplies
the four storeys, window divisions, foliate wreath, cornice and shallow red cap.
Only the street-facing walls and their immediate returns are reconstructed.
"""
from math import cos, sin, pi, ceil, hypot
from pathlib import Path
import sys
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Facade, opening
from render_finish import ATLAS, stone_uv

STONE='grey bush-hammered render'
CARVING='carved pale stone'
EDGE='weathered projecting cornice'
JOINT='scored stone joint'
FRAME='charcoal steel sash'
GLASS='cool recessed glass'
ROOF='weathered red tile'
HIP='red hip tiles'
SHADE='window reveal shadow'
PALETTE={name:dict(color=list(rgb),roughness=rough,metallic=metal) for name,rgb,rough,metal in [
 (STONE,(.707,.695,.659),.87,0),(CARVING,(.755,.738,.692),.87,0),(EDGE,(.626,.603,.551),.87,0),
 (JOINT,(.512,.503,.479),.91,0),(FRAME,(.285,.274,.251),.59,.14),(GLASS,(.314,.382,.405),.31,.11),
 (ROOF,(.565,.271,.211),.88,0),(HIP,(.616,.321,.246),.83,0),(SHADE,(.143,.15,.143),.95,0)]}

PALETTE[STONE].update(color=[1.,1.,1.],texture=str(ATLAS))

# The last two points enclose the construction joint with the retained house.
A=(-3.011,2.955); B=(-1.482,0); C=(1.482,0); D=(4.102,2.060)
RING=(A,B,C,D,(3.75,5.08),(-2.91,5.38))
OUTLINE=Polygon(RING)
WINDOW_LEVELS=((.72,2.60),(4.77,2.70),(9.64,2.60),(13.65,1.69))
CORNICE=13.10
EAVES=15.88
APEX_HEIGHT=17.36

def moulded_layer(builder,projection,low,high,material,label):
    boundary=OUTLINE.buffer(projection,join_style=2)
    builder.plan_prism(boundary,low,high,material,label)

def window(face,u,z,w,h,arched,lod,label):
    shape=opening(u,z,w,h,.54 if arched else 0,12 if lod else 32)
    # The top lights have closely spaced horizontal muntins below the fan head.
    face.prism(shape.buffer(.009,join_style=2),-.275,-.262,GLASS,label+'/glass')
    inner=shape.buffer(-.07,join_style=2)
    bars=[]
    if arched:
        spring=z+h-.54
        for t in (.22,.47,.72,1.):
            bar=spring-(1-t)*(spring-z)
            bars.append(box(-w/2,bar-.016,w/2,bar+.016))
        for x in (-w/6,w/6):bars.append(box(x-.017,z,x+.017,spring))
        if not lod:
            for sign in (-1,1):
                face.line((0,spring,-.16),(sign*w*.32,spring+.365,-.16),.021,FRAME,8,label+'/fan slant')
    else:
        for i in range(1,4):bars.append(box(-w/2+i*w/4-.022,z,-w/2+i*w/4+.022,z+h))
        for f in (.54,.82):bars.append(box(-w/2,z+h*f-.022,w/2,z+h*f+.022))
    frame=shape.buffer(-.012,join_style=2).difference(inner.difference(unary_union(bars)))
    face.prism(frame,-.24,-.16,FRAME,label+'/metal divisions')
    lip=shape.buffer(.075,join_style=2).difference(shape)
    face.prism(lip,-.02,.043,CARVING,label+'/opening edge')
    face.box(0,z-.051,min(face.length-.09,w+.22),.1,.21,.045,EDGE,label+'/sill')
    return shape

def spandrel(face,lower,upper,width):
    height=upper-lower
    outer=box(-width/2,lower,width/2,upper)
    face.prism(outer,-.026,.021,STONE,'recessed spandrel field')
    ring=outer.difference(outer.buffer(-.067,join_style=2))
    face.prism(ring,.021,.064,EDGE,'raised spandrel border')
    inner=outer.buffer(-.128,join_style=2)
    face.prism(inner.difference(inner.buffer(-.024,join_style=2)),.022,.044,CARVING,'fine inner border')

def wreath(face,z,lod):
    rx,rz=.47,.50
    def tube(points,r,label):
        face.builder.tube([face.point(u,h,d) for u,h,d in points],r,CARVING,5 if lod else 9,face.label+'/'+label)
    # Open upper part, where the two stalks meet two ribbons and a central bow.
    steps=23 if lod else 45
    ring=[(rx*cos(a),z+rz*sin(a),.1) for a in [1.88+(7.52-1.88)*i/steps for i in range(steps+1)]]
    tube(ring,.053,'wreath stalk')
    for side in (-1,1):
        for j in range(5 if lod else 9):
            t=(j+.4)/(5 if lod else 9)
            angle=-pi/2 + (pi*.87)*t
            u=side*rx*cos(angle); h=z+rz*sin(angle)
            for branch in (-1,1):
                along=(side*-sin(angle),cos(angle))
                radial=(side*cos(angle)*branch,sin(angle)*branch)
                start=(u,h);tip=(u+.145*along[0]+.075*radial[0],h+.145*along[1]+.075*radial[1])
                middle=((start[0]+tip[0])/2,(start[1]+tip[1])/2)
                dx,dz=tip[0]-start[0],tip[1]-start[1];length=hypot(dx,dz)
                wing=(.048*-dz/length,.048*dx/length)
                pts=[start,(middle[0]+wing[0],middle[1]+wing[1]),tip,(middle[0]-wing[0],middle[1]-wing[1])]
                vert=[face.point(x,y,.133)for x,y in pts]+[face.point(*middle,.219)]
                face.builder.add(vert,[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],CARVING,face.label+'/carved leaves')
        tube([(0,z+.48,.132),(side*.12,z+.60,.143),(side*.27,z+.66,.152),
              (side*.31,z+.59,.144),(side*.23,z+.52,.143),(side*.13,z+.56,.143),(0,z+.48,.132)],.038,'ribbon knot')
    face.box(0,z+.49,.16,.115,.11,.135,CARVING,'bow centre')

def build_face(builder,i,lod):
    face=Facade(builder,RING[i],RING[(i+1)%len(RING)],('west canted','central street','east canted','east return','house joint','west return')[i])
    if i>2:
        face.wall(0,EAVES,(),.21,STONE)
        return
    widths=(2.10 if i==1 else 1.62)
    openings=[]
    for floor,(z,h) in enumerate(WINDOW_LEVELS):
        w=widths*(1.04 if floor==3 else 1)
        openings.append(opening(0,z,w,h,.54 if floor==3 else 0,12 if lod else 32))
        window(face,0,z,w,h,floor==3,lod,('ground','first','second','attic')[floor])
    face.wall(0,EAVES,openings,.225,STONE)
    for low,high in [(3.57,4.51),(7.70,9.41)]:
        spandrel(face,low,high,widths+.16)
    if i==1:wreath(face,8.48,lod)
    for side in (-1,1):
        jamb=side*(face.length/2-.12)
        face.box(jamb,6.62,.225,12.68,.087,.036,CARVING,'end strip')
        for n in range(1,18 if not lod else 9):
            z=n*(.72 if not lod else 1.44)
            face.box(jamb,z,.214,.013,.012,.083,JOINT,'coursing across end strip')
    for j in range(1,round(face.length/.31)):
        u=-face.length/2+j*face.length/round(face.length/.31)
        face.box(u,CORNICE-.105,.148,.24,.255,.17,EDGE,'corbel beneath cornice')

def roof(builder,lod):
    outline=list(OUTLINE.buffer(.12,join_style=2).exterior.coords)[:-1]
    apex=(.35,2.72,APEX_HEIGHT)
    for j,(a,b) in enumerate(zip(outline,outline[1:]+outline[:1])):
        points=[(*a,EAVES+.21),(*b,EAVES+.21),apex]
        # The buffered polygon is clockwise.
        builder.add(points,[(2,1,0)],ROOF,'roof/red hip')
        builder.tube([points[0],apex],.047,HIP,6 if lod else 9,'roof/raised hips')
        pitches=4 if lod else 13
        for k in range(1,pitches):
            t=k/pitches
            lo=tuple((1-t)*a+t*b for a,b in zip(points[0],apex))
            hi=tuple((1-t)*a+t*b for a,b in zip(points[1],apex))
            builder.tube([lo,hi],.014 if lod else .022,HIP,4 if lod else 6,'roof/tile courses')

def add_geometry(builder,lod):
    for n in range(len(RING)):build_face(builder,n,lod)
    for p,lo,hi,material,name in [(0,0,.17,EDGE,'base'),(.10,12.80,12.91,CARVING,'cornice lower fillet'),
        (.21,12.91,13.04,EDGE,'cornice stepped soffit'),(.36,13.06,13.20,EDGE,'cornice shelf'),
        (.39,13.20,13.31,CARVING,'cornice rim'),(.24,13.31,13.39,EDGE,'cornice crown'),
        (.13,15.73,15.82,CARVING,'attic eaves fillet'),(.22,15.82,15.96,EDGE,'attic coping'),
        (.13,15.96,16.09,CARVING,'attic parapet top')]:
        moulded_layer(builder,p,lo,hi,material,name)
    roof(builder,lod)

    for part in builder.parts:
        if part["material"]==STONE:
            part["texcoords"]=[(u,1-v)for u,v in (stone_uv(*p) for p in part["vertices"])]
