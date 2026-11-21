"""Street-front fragment of No.9 Shaoxing Road, documented in October 2026."""
import math
from pathlib import Path
from random import Random
from shapely import affinity
from shapely.geometry import Point, Polygon, box, LineString
from photo_architecture import Facade
from sign_lettering import add_facade_lettering

HERE = Path(__file__).resolve().parent
WIDTH, BODY_DEPTH, WALL_HEAD = 5.74, 2.03, 10.27
SILL, CROWN, ARCH_WIDTH = 4.90, 8.95, 1.71
DOOR_WIDTH, DOOR_HEAD = 1.56, 2.86
WALL = 'Buff precast render'
JOINT = 'Fine sandy joints'
STONE = 'Rounded arch trim'
SHADOW = 'Dark opening backs'
PLATE = 'Silver-grey canopy edge'
UNDERSIDE = 'Pale canopy soffit'
IRON = 'Charcoal arch frames'
GLASS = 'Smoky pebbled glazing'
SPECK = 'Pressed-glass highlights'
RED = 'Muted red lozenges'
DOOR = 'Dark timber door frame'
LAMP = 'Pale-grey relief'
COPPER = 'Patinated dark lettering'
PALETTE = {name: {'color': colour, 'roughness': roughness} for name, colour, roughness in [
    (WALL,[.63,.555,.425],.85),(JOINT,[.46,.414,.32],.88),(STONE,[.70,.625,.490],.78),
    (SHADOW,[.067,.065,.058],.96),(PLATE,[.45,.47,.475],.72),(UNDERSIDE,[.57,.575,.555],.84),
    (IRON,[.125,.133,.135],.56),(GLASS,[.235,.259,.268],.39),(SPECK,[.36,.375,.39],.49),
    (RED,[.49,.205,.23],.53),(DOOR,[.144,.105,.082],.67),(LAMP,[.51,.524,.503],.69),
    (COPPER,[.16,.125,.105],.68)]}

def rounded_head(width, bottom, top, segments):
    r=width/2
    return Polygon([(-r,bottom),(r,bottom),*[(r*math.cos(k*math.pi/segments),
        top-r+r*math.sin(k*math.pi/segments)) for k in range(segments+1)]])

def clipped_bar(f, outline, a, b, thickness, depth, material, label):
    bar=LineString([a,b]).buffer(thickness/2, cap_style='flat', join_style='mitre').intersection(outline)
    if not bar.is_empty:
        f.prism(bar,depth-.016,depth,material,label)

def arch_glazing(f,opening,lod):
    f.prism(opening,-.31,-.274,SHADOW,'Arch opaque back')
    f.prism(opening.buffer(-.028),-.239,-.208,GLASS,'Recessed arch glass')
    f.prism(opening.difference(opening.buffer(-.044)), -.226,-.116,IRON,'Heavy arch frame')
    spring=CROWN-ARCH_WIDTH/2
    apron=SILL+.82
    rail=SILL+2.12
    panel_top=spring-.13
    col=ARCH_WIDTH/4
    for i in range(4):
        cx=-ARCH_WIDTH/2+col*(i+.5)
        for j,(low,high) in enumerate([(SILL,apron),(apron,rail),(rail,panel_top)]):
            panel=box(cx-col*.5+.014,low+.014,cx+col*.5-.014,high-.014)
            inner=panel.buffer(-(.030 if lod else .038),join_style=2)
            f.prism(panel.difference(inner),-.196,-.125,IRON,f'Arch panel {i+1}.{j+1}')
            clipped_bar(f,inner,(cx,low),(cx,high),.020,-.149,IRON,'Vertical casement muntin')
            bars=1 if j==0 else 3
            for k in range(1,bars+1):
                z=low+(high-low)*k/(bars+1)
                clipped_bar(f,inner,(cx-col/2,z),(cx+col/2,z),.022,-.15,IRON,'Horizontal casement muntin')
        ruby_z=(SILL+apron)/2
        ruby=Polygon([(cx-.098,ruby_z),(cx,ruby_z+.126),(cx+.098,ruby_z),(cx,ruby_z-.126)])
        f.prism(ruby,-.181,-.162,RED,'Red glass diamond')
    fan=opening.intersection(box(-ARCH_WIDTH,panel_top,ARCH_WIDTH,CROWN))
    for i in range(1,8):
        cx=-ARCH_WIDTH/2+i*ARCH_WIDTH/8
        clipped_bar(f,fan,(cx,panel_top),(cx,CROWN+.02),.023,-.147,IRON,'Fanlight upright')
    for k in range(4):
        z=panel_top+(CROWN-panel_top)*k/4
        clipped_bar(f,fan,(-ARCH_WIDTH,z),(ARCH_WIDTH,z),.029,-.142,IRON,'Fanlight rail')
    outer=rounded_head(ARCH_WIDTH+.27,SILL-.045,CROWN+.155,26 if lod else 56)
    lip=outer.difference(opening)
    f.prism(lip,-.032,.049,STONE,'Arch double reveal')
    inner=rounded_head(ARCH_WIDTH+.113,SILL-.027,CROWN+.066,26 if lod else 54)
    f.prism(inner.difference(opening.buffer(.013)),-.015,.083,WALL,'Inner raised arch moulding')
    if lod:return
    rng=Random(347)
    verts=[];tris=[]
    for _ in range(1100):
        x=rng.uniform(-ARCH_WIDTH/2+.045,ARCH_WIDTH/2-.045);z=rng.uniform(SILL+.04,CROWN-.04)
        if not opening.contains(Point(x,z)):continue
        r=rng.uniform(.004,.013);k=len(verts)
        verts.extend([f.point(x-r,z,.0-.207),f.point(x+.32*r,z-r,-.204),f.point(x+r,z+.32*r,-.204)])
        tris.append([k,k+1,k+2])
    f.builder.add(verts,tris,SPECK,f.label+'/Glass grain')

def recessed_door(f):
    outer=box(-1.19,0,1.19,4.22)
    portal=box(-DOOR_WIDTH/2,.045,DOOR_WIDTH/2,DOOR_HEAD)
    f.prism(outer,-.70,-.655,SHADOW,'Sheltered hole lining')
    plane=outer.difference(portal)
    f.prism(plane,-.605,-.543,WALL,'Sheltered entrance wall')
    f.prism(portal.buffer(.074,join_style=2).difference(portal),-.548,-.478,STONE,'Door head and stiles')
    for side in (-1,1):
        cx=side*DOOR_WIDTH/4
        leaf=box(cx-DOOR_WIDTH/4+.012,.065,cx+DOOR_WIDTH/4-.012,DOOR_HEAD-.026)
        inner=leaf.buffer(-.067,join_style=2)
        f.prism(leaf,-.652,-.623,GLASS,'Textured glass in door')
        f.prism(leaf.difference(inner),-.624,-.546,DOOR,'Door leaf perimeter')
        for bottom in (.30,.89,1.48,2.06,2.66):
            clipped_bar(f,inner,(side*.015,bottom),(side*(DOOR_WIDTH/2-.05),bottom+.545),
                        .054,-.575,DOOR,'Rising diagonal on door')
        f.box(side*.061,1.23,.024,.21,.064,-.515,IRON,'Pull by door meeting edge')
    f.box(0,.041,DOOR_WIDTH+.12,.080,.72,-.330,PLATE,'Entrance threshold')
    return outer

def stepped_canopy(b,f,lod):
    # The street photograph sees the lower roof and both angled edges.
    front_y, back_y=-1.28,.10
    plan=Polygon([(-1.99,front_y),(1.99,front_y),(2.10,back_y),(-2.10,back_y)])
    def rise(x,y):return 4.205-.11*abs(x)/2.1+.046*(y-front_y)
    def convert(x,y,h):return (x,y,rise(x,y)+h)
    for label,lo,hi,material,inset in [
        ('Canopy folded soffit',-.086,.0,UNDERSIDE,.012),
        ('Main folded canopy plate',.0,.141,PLATE,0),
        ('Upper flashing seam',.141,.159,PLATE,.008)]:
        polygon=plan.buffer(-inset,join_style=2)
        # Each half is planar, with a real centre fold and a common seam.
        for side in (-1,1):
            piece=polygon.intersection(box(-3 if side==-1 else 0,-2,0 if side==-1 else 3,1))
            b.prism(piece,lo,hi,convert,material,label)
    shade=Point(0,-.67).buffer(.105,quad_segs=8 if lod else 16)
    b.prism(shade,3.99,4.085,lambda x,y,z:(x,y,z),LAMP,'Canopy/Central ceiling light')

def vertical_accents(f,lod):
    for direction in (-1,1):
        x=1.91*direction
        f.box(x,3.87,.088,7.74,.052,.030,LAMP,'Long applied metal strip')
        f.box(x-.052,3.87,.017,7.74,.033,.035,JOINT,'Recess beside applied strip')
        ornament=box(x-.119,7.63,x+.119,8.05)
        f.prism(ornament,.035,.105,LAMP,'Rectangular relief head')
        f.box(x,7.60,.23,.058,.085,.082,PLATE,'Relief neck')
        for i in range(3):
            # The inset has parallel, sweeping diagonal interruptions rising to the right.
            low=7.67+.095*i
            pts=[(x-.117,low-.035),(x-.064,low+.022),(x+.002,low+.094),(x+.118,low+.134)]
            line=LineString(pts).buffer(.009 if lod else .011,cap_style='flat',join_style='round')
            f.prism(line.intersection(ornament),.104,.115,IRON,'Curved relief line')

def add_building(builder,lod):
    half=WIDTH/2
    f=Facade(builder,(-half,0),(half,0),'Shaoxing No.9')
    door=recessed_door(f)
    arch=rounded_head(ARCH_WIDTH,SILL,CROWN,28 if lod else 64)
    actual=f.wall(0,WALL_HEAD,holes=[door,arch],thickness=.55,material=WALL)
    for i in range(1,19):
        z=i*.557
        strip=actual.intersection(box(-half,z-.006,half,z+.006))
        if not strip.is_empty:f.prism(strip,.0008,.0026,JOINT,'Fine render course')
    arch_glazing(f,arch,lod)
    stepped_canopy(builder,f,lod)
    vertical_accents(f,lod)
    font=HERE/'fonts/PoliceCercle.otf'
    add_facade_lettering(f,'CERCLE DE LA POLICE',0,3.59,1.65,.105,-.541,-.513,COPPER,label='French upper line',font=font)
    # The middle word of the second line is shaded. Use only independently read runs.
    for text,u,span in [('FOYER',-.65,.36),('& DU SOLDAT',.48,.67)]:
        add_facade_lettering(f,text,u,3.466,span,.096,-.541,-.516,COPPER,label='French lower line',font=font)
    # The top of the narrow central wall falls below the rear flanking towers.
    # The cornice carries through into the two original wings; both cut ends stop on the chosen study boundary.
    f.box(0,WALL_HEAD+.029,WIDTH,.079,.31,.007,STONE,'Central wall cap')
    f.box(0,WALL_HEAD+.105,WIDTH,.085,.40,.035,PLATE,'Upper lip of cornice')
    for a,b in [((half,0),(half,BODY_DEPTH)),((-half,BODY_DEPTH),(-half,0))]:
        face=Facade(builder,a,b,'Central entrance side');face.wall(0,WALL_HEAD,thickness=.14,material=WALL)
    builder.prism(box(-half,0,half,BODY_DEPTH),WALL_HEAD-.097,WALL_HEAD,
                  lambda x,y,z:(x,y,z),PLATE,'Central entrance/short roof cover')
