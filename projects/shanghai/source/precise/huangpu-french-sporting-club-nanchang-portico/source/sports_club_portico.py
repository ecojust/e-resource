"""Original surface geometry of the Nanchang Road portico, in metres.

X increases to the right in the front photograph. The columns lie at y=0,
with the street toward negative y. The side and rear elevations stop at the
documented strip. The spandrel contains actual perforations.
"""
from math import sin, cos, pi, tau
from pathlib import Path
import json
from shapely.geometry import LineString, Point, Polygon, box, shape
from shapely.ops import unary_union
from photo_architecture import Facade, opening

WALL='Pebbled ochre render'
CREAM='Pale rendered concrete'
SILL='Grey limestone'
TILE='Red clay tiles'
LIGHT_TILE='Fired clay highlights'
WOOD='Dark painted frames'
GLASS='Recessed window glass'
IRON='Dark iron'
BRASS='Gold painted lettering'
SHADOW='Deep entrance shadow'
MATERIALS={name:dict(color=rgb,roughness=rough) for name,rgb,rough in [
    (WALL,[.568,.521,.408],.94),(CREAM,[.795,.781,.700],.86),(SILL,[.452,.449,.395],.88),
    (TILE,[.401,.179,.104],.87),(LIGHT_TILE,[.51,.247,.143],.82),
    (WOOD,[.197,.119,.096],.69),(GLASS,[.137,.181,.174],.38),
    (IRON,[.116,.119,.100],.66),(BRASS,[.60,.435,.192],.53),(SHADOW,[.084,.081,.069],.94)]}
WIDTH=7.36
COLUMN=1.421
HOUSE=1.55

def cuboid(b,x0,x1,y0,y1,z0,z1,material,name):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),material,label=name)

def bar(b,points,r,mat,name,lod=False):
    b.tube(points,r,mat,5 if lod else 8,name)

def profile(b,p,z0,z1,m,n):
    b.prism(p,z0,z1,lambda x,y,z:(x,y,z),m,n)

def glazed(f,opening_shape,arch=False):
    x0,z0,x1,z1=opening_shape.bounds
    f.prism(opening_shape,-.229,-.206,GLASS,'recessed panes')
    x=(x0+x1)/2
    perimeter=opening_shape.difference(opening_shape.buffer(-.058,join_style=2))
    bars=[perimeter,box(x-.026,z0,x+.026,z1)]
    for z in ([z0+(z1-z0)*.48,z1-(x1-x0)/2] if arch else [z0+(z1-z0)*.69]):
        bars.append(box(x0,z-.025,x1,z+.025))
    if arch:
        spring=z1-(x1-x0)/2; radius=(x1-x0)/2
        for u in [-.25,.25]:
            bars.append(box(x+u*(x1-x0)-.016,z0,x+u*(x1-x0)+.016,spring))
        for a in [pi/4,3*pi/4]:
            bars.append(LineString([(x,spring),(x+radius*cos(a),spring+radius*sin(a))]).buffer(.017,cap_style=2))
    f.prism(unary_union(bars).intersection(opening_shape),-.185,-.11,WOOD,'wood sash')
    f.prism(box(x0-.085,z0-.08,x1+.085,z0),.004,.10,CREAM,'sill')

def shaft(b,x,lod):
    bands=[(.19,.365),(.27,.365),(.30,.340),(.36,.325),(3.25,.315),(3.31,.337),(3.38,.351)]
    sides=40 if lod else 128
    verts=[]
    for j,(z,r) in enumerate(bands):
        for i in range(sides):
            a=tau*i/sides
            flute=0 if j in (0,1,5,6) else (.012 if lod else .018)*(.5+.5*cos(16*a))
            verts.append((x+(r-flute)*cos(a),-(r-flute)*sin(a),z))
    faces=[]
    for j in range(len(bands)-1):
        for i in range(sides):
            p=j*sides+i;q=j*sides+(i+1)%sides
            faces.append((p,p+sides,q+sides,q))
    faces.extend([tuple(range(sides)),tuple(reversed(range((len(bands)-1)*sides,len(bands)*sides)))])
    b.add(verts,faces,CREAM,'Fluted gate columns')
    cuboid(b,x-.39,x+.39,-.39,.39,.05,.19,SILL,'Square column plinths')

def window_wall(b,lod):
    f=Facade(b,(-WIDTH/2,HOUSE),(WIDTH/2,HOUSE),'Street')
    door=box(-1.17,.18,1.17,3.23)
    arch=opening(0,5.36,1.78,2.43,.89,16 if lod else 36)
    side=[box(c-.50,.73,c+.50,2.99) for c in (-2.62,2.62)]
    upper=[box(c-.46,5.58,c+.46,6.94) for c in (-2.62,2.62)]
    # The 2015 winter view separates the horizontal eave from the central
    # parapet beyond it. The street wall remains continuous below that eave.
    outline=box(-WIDTH/2,.02,WIDTH/2,8.11)
    f.wall(.02,8.11,[door,arch,*side,*upper],.29,WALL,outline=outline)
    parapet=Polygon([(-2.01,8.04),(2.01,8.04),(2.01,8.23),(1.34,8.25),
                     (.94,8.39),(.70,8.66),(.37,8.88),(0,8.94),(-.37,8.88),
                     (-.70,8.66),(-.94,8.39),(-1.34,8.25),(-2.01,8.23)])
    f.prism(parapet,-.55,-.29,WALL,'Setback shaped parapet')
    f.prism(box(-WIDTH/2,8.01,WIDTH/2,8.13),.010,.21,TILE,'Continuous eave')
    f.prism(box(-WIDTH/2,7.91,WIDTH/2,7.99),.009,.117,WALL,'Course below eave')
    for i in range(42 if lod else 72):
        x=-WIDTH/2+(i+.5)*(WIDTH/(42 if lod else 72))
        f.prism(box(x-.024,7.83,x+.024,7.91),.012,.076,TILE,'Under-eave brick corbels')
    for g in side+upper:glazed(f,g)
    glazed(f,arch,True)
    surround=arch.buffer(.125,join_style=2).difference(arch)
    f.prism(surround,.002,.082,CREAM,'Broad upper arch frame')
    # The darker brick door lining stands behind the freestanding street gate.
    f.prism(door,-.69,-.65,SHADOW,'Entrance backing')
    glazed(f,door.buffer(-.10,join_style=2))
    for x in (-1.20,1.20):
        f.prism(box(x-.038,.20,x+.038,3.24),-.18,.048,WOOD,'Door casing')
    for s in (-1,1):
        cuboid(b,s*WIDTH/2-.10,s*WIDTH/2+.10,HOUSE,HOUSE+.74,.03,7.78,WALL,'Cut wall return')
    # Subtle irregular aggregate relief, restricted to areas of real exposed wall.
    if not lod:
        import random
        rng=random.Random(57);tris=[];points=[];visible=outline.difference(unary_union([door,arch,*side,*upper]).buffer(.07))
        for _ in range(980):
            x=rng.uniform(-WIDTH/2+.05,WIDTH/2-.05);z=rng.uniform(.16,8.55)
            if not visible.contains(Point(x,z)): continue
            dx=rng.uniform(.009,.022);dz=rng.uniform(.008,.017);i=len(points)
            points.extend([(x-dx,HOUSE-.002,z-dz),(x+dx,HOUSE-.002,z-dz*.35),(x,HOUSE-.004,z+dz),(x-dx*.2,HOUSE-rng.uniform(.011,.022),z)])
            tris.extend([(i,i+1,i+3),(i+1,i+2,i+3),(i+2,i,i+3)])
        b.add(points,tris,WALL,'Shallow roughcast aggregate')

def canopy(b,lod):
    # Three visible planes meet toward the backing wall. The frontage photo
    # shows a single central hip peak, not a ridge running along the street.
    xh,front,back=2.23,-.67,1.60
    rise=.68;z=3.59
    cuboid(b,-xh,xh,front,back,3.38,z-.08,CREAM,'Portico soffit')
    cuboid(b,-xh-.02,xh+.02,front-.02,back,z-.10,z+.018,WOOD,'Red fascia')
    a=(-xh,front,z);c=(xh,front,z);d=(xh,back,z);e=(-xh,back,z);peak=(0,back,z+rise)
    b.add([a,c,d,e,peak],[(0,1,4),(1,2,4),(3,0,4)],TILE,'Three hip slopes')
    def tiled(start,end,material):
        dx,dy,dz=[e-s for s,e in zip(start,end)]
        length=(dx*dx+dy*dy+dz*dz)**.5
        if length<.045:return
        courses=1 if lod else max(1,round(length/.34))
        for k in range(courses):
            s=k/courses;t=(k+1)/courses
            p=(start[0]+s*dx,start[1]+s*dy,start[2]+s*dz+.012)
            q=(start[0]+t*dx,start[1]+t*dy,start[2]+t*dz+.030)
            bar(b,[p,q],.046,material,'Curved tile courses',lod)
    n=19 if lod else 32
    for i in range(n):
        x=-xh+2*xh*(i+.5)/n
        part=1-abs(x)/xh
        tiled((x,front,z),(x,front+part*(back-front),z+rise*part),LIGHT_TILE if i%4==0 else TILE)
    n=8 if lod else 16
    for side in [-1,1]:
        for i in range(n):
            part=(i+.5)/n;y=front+(back-front)*part
            tiled((side*xh,y,z),(side*xh*(1-part),y,z+rise*part),LIGHT_TILE if i%5==0 else TILE)
        bar(b,[(side*xh,front,z+.045),(0,back,z+rise+.055)],.075,TILE,'Diagonal hip rolls',lod)

def balcony(b,lod):
    bx=1.48;front=.29;back=HOUSE+.035;z0=4.28;z1=5.22
    slab=box(-bx-.07,front-.05,bx+.07,back)
    profile(b,slab,z0-.17,z0,CREAM,'Projecting balcony slab')
    segments=[((-bx,back),(-bx,front)),((-bx,front),(bx,front)),((bx,front),(bx,back))]
    for i,(start,end) in enumerate(segments):
        face=Facade(b,start,end,'Balcony '+str(i+1));span=face.length
        hwidth=span*(.32 if i==1 else .17)
        opening=box(-hwidth,z0+.26,hwidth,z1-.22)
        face.wall(z0,z1,[opening],.16,CREAM)
        # Small diagonally laid red clay units form the open inset panel.
        for slope in [-1,1]:
            width,height=2*hwidth,z1-z0-.48;spacing=.145 if lod else .103
            for j in range(int((width+height)/spacing)+3):
                left=-hwidth-height+j*spacing;y=z0+.26
                line=LineString([(left,y if slope==1 else y+height),(left+height,y+height if slope==1 else y)])
                inset=line.buffer(.021 if lod else .016,cap_style=2).intersection(opening)
                if inset.area>1e-7:face.prism(inset,-.09,-.047,TILE,'Perforated clay screen')
        face.prism(box(-span/2-.014,z1-.034,span/2+.014,z1+.032),-.15,.033,CREAM,'Coping')

def ironwork(b,lod):
    y=-.005
    def gate_top(x):return 2.14+.39*cos(pi*x/(2*1.1))
    for side in (-1,1):
        left,right=sorted([side*1.105,side*.023]);points=[]
        for i in range(15): 
            x=left+(right-left)*i/14;points.append((x,y,gate_top(x)))
        bar(b,points,.029,IRON,'Arched double gate',lod)
        for x in [left,right]:bar(b,[(x,y,.325),(x,y,gate_top(x))],.025,IRON,'Gate stiles',lod)
        for z in [.38,1.26]:bar(b,[(left,y,z),(right,y,z)],.023,IRON,'Gate rails',lod)
        for i in range(1,8 if lod else 12):
            x=left+(right-left)*i/(8 if lod else 12)
            bar(b,[(x,y,.39),(x,y,gate_top(x)-.015)],.012,IRON,'Vertical gate bars',lod)
            if not lod and i%2==0:
                pts=[(x+.043*sin(t*tau),y-.014,1.32+t*.61) for t in [j/12 for j in range(13)]]
                bar(b,pts,.009,IRON,'Gate scrolls',lod)
    # The date-specific sign hangs below the canopy with narrow open iron brackets.
    board_y=-.14
    cuboid(b,-.99,.99,board_y-.055,board_y+.055,2.78,3.23,IRON,'Exhibition hall sign')
    for side in (-1,1):
        outline=[(.99,2.75),(1.38,2.75),(1.28,2.85),(1.25,2.94),(1.27,3.04),(1.38,3.21),(.99,3.21)]
        bar(b,[(side*x,board_y,z)for x,z in outline],.016,IRON,'Sign side brackets',lod)
    for x in [-.86,.86]:bar(b,[(x,board_y,3.22),(x,board_y,3.39)],.016,IRON,'Hanging sign rods',lod)
    if not lod:
        page=Path(__file__).with_name('sign-contours.json')
        for item in json.loads(page.read_bytes()):
            g=shape(item['shape']);f=Facade(b,(-1,board_y-.055),(1,board_y-.055),'Sign')
            f.prism(g,.004,.013,BRASS,'Exhibition hall name')

def add_building(b,lod=False):
    window_wall(b,lod);canopy(b,lod);balcony(b,lod)
    for x in (-COLUMN,COLUMN):shaft(b,x,lod)
    # Thresholds project slightly toward the street. No adjoining fence is extended into the road.
    for i,(front,z) in enumerate([(-.48,.08),(-.26,.155),(-.05,.23)]):
        cuboid(b,-1.12,1.12,front,HOUSE+.13,.008+i*.074,z,SILL,'Entrance threshold')
    ironwork(b,lod)
