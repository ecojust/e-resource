"""The relocated Bund signal station, its quay-side station house and signal mast."""
from math import cos, sin, pi, hypot
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade

WALL='cream mineral render';BRICK='red brown brick';TRIM='pale dressed stone';GLASS='smoky window glass';IRON='black painted iron';BRONZE='brown door framing';ROOF='weathered terrace';BASE='grey granite';SIGN='pale register plaque'
PALETTE={n:dict(color=c,roughness=r)for n,c,r in [(WALL,[.87,.83,.73],.89),(BRICK,[.46,.207,.155],.88),(TRIM,[.92,.9,.84],.84),(GLASS,[.19,.255,.27],.32),(IRON,[.09,.094,.091],.57),(BRONZE,[.205,.17,.146],.71),(ROOF,[.245,.225,.20],.93),(BASE,[.54,.51,.46],.91),(SIGN,[.70,.68,.61],.83)]}
CY=6.35

def arch(u,sill,w,top):
    radius=w/2; spring=top-radius
    return box(u-radius,sill,u+radius,spring).union(Point(u,spring).buffer(radius,quad_segs=12))

def masonry(b,a,c,windows,door=None,crests=(),cornice=True):
    f=Facade(b,a,c,'station house');holes=[]
    for u,z,width,top,rounded in windows:
        p=arch(u,z,width,top) if rounded else box(u-width/2,z,u+width/2,top)
        holes.append(p);f.window(p,columns=2,rows=3,frame=BRONZE,glass=GLASS,trim=False,label='recessed casement');b.parts.pop();f.box(u,z-.065,width+.17,.14,.31,-.02,TRIM,'short stone sill')
    if door:
        u,width,top=door;p=arch(u,.17,width,top);holes.append(p)
        f.prism(p,-.27,-.23,BRONZE,'arched double leaf door');reveal=p.buffer(.14,join_style=2).difference(p);f.prism(reveal,-.025,.075,TRIM,'architrave around doorway')
        spring=top-width/2;transom=p.intersection(box(u-width/2+.10,spring-.13,u+width/2-.10,top-.10));f.prism(transom,-.225,-.19,GLASS,'fanlight');f.box(u,(spring+.17)/2,.055,spring-.17,.05,-.17,IRON,'meeting stile')
        for x in [u-width*.24,u+width*.24]:
            f.box(x,1.83,width*.37,1.95,.036,-.18,GLASS,'door leaf glass');f.line((x+.12,.92,-.14),(x+.12,1.17,-.14),.023,BRONZE,7,'pull handle')
    blank=unary_union(holes);f.wall(.16,9.73,holes,thickness=.28,material=WALL);f.beam(.24,.43,.12,BASE)
    for row in range(16):
        z=.70+row*.52
        band=box(-f.length/2+.035,z,f.length/2-.035,z+.22).difference(blank.buffer(.085));f.prism(band,.006,.024,BRICK,'recessed red brick band')
    if cornice:
        for z,h,deep in [(4.45,.23,.12),(4.70,.12,.21),(9.48,.22,.16),(9.72,.18,.25),(9.89,.12,.32)]:f.beam(z,h,deep,TRIM)
    for u in crests:
        arc=arch(u,9.66,1.8,10.55);f.prism(arc,-.20,.12,TRIM,'curved parapet crest');recess=arch(u,9.78,1.38,10.36);f.prism(recess,.13,.145,ROOF,'inset tympanum')
    return f

def circle(x,y,z,r,n):return [(x+r*cos(2*pi*i/n),y+r*sin(2*pi*i/n),z)for i in range(n+1)]

def gallery_rail(b,z,r,h,lod,small=False):
    n=(26 if lod else 44) if not small else (12 if lod else 20)
    for ht in [.10,h*.55,h]:b.tube(circle(0,CY,z+ht,r,48 if lod else 72),.026 if small else .039,IRON,5,'circular gallery rail')
    for i in range(n):
        t=2*pi*i/n;x,y=r*cos(t),CY+r*sin(t);b.tube([(x,y,z),(x,y,z+h)],.026 if small else .038,IRON,5,'gallery upright')

def drum(b,lod):
    # Eight wall faces and radial pilasters frame the tall glazed openings at the north end.
    n=16;r=3.62;pts=[(r*cos(2*pi*i/n-pi/16),CY+r*sin(2*pi*i/n-pi/16))for i in range(n+1)]
    for i,(a,c)in enumerate(zip(pts,pts[1:])):
        f=Facade(b,a,c,'tower base');front=(i in [0,2,4,6,8]);holes=[]
        if front:
            p=arch(0,3.28,.88,8.39);holes.append(p);f.window(p,columns=1,rows=3,frame=IRON,glass=GLASS,trim=False,label='tower narrow window');b.parts.pop()
            lower=box(-.48,.17,.48,2.84);holes.append(lower);f.prism(lower,-.20,-.16,BRONZE,'recess under tower window');f.box(0,1.80,.65,1.48,.03,-.145,GLASS,'lower door light')
        f.wall(.12,9.94,holes,thickness=.30,material=WALL)
        if i%2==1:
            for k in range(12):f.box(0,.65+k*.73,.88,.23,.08,.016,BRICK,'striped inset between pilasters')
        for z,width,proj in [(3.00,.18,.20),(9.32,.28,.22),(9.69,.17,.32)]:f.beam(z,width,proj,TRIM)
        if i%2==0:
            for z,h,w in [(.26,.34,.44),(.60,.30,.38),(4.68,7.88,.29),(8.77,.30,.38),(9.08,.32,.45)]:f.box(-f.length*.47,z,w,h,.35,.07,TRIM,'raised pilaster')
    seg=40 if lod else 64
    for profile,mat,label in [([(.0,3.85),(.18,3.85),(.37,3.71)],BASE,'rotunda plinth'), ([(9.86,3.61),(10.03,3.81),(10.20,3.87),(10.31,3.73),(10.56,3.73),(10.71,3.92),(10.90,3.92)],TRIM,'ringed platform over tower base')]:b.lathe((0,CY),profile,mat,seg,label=label)
    gallery_rail(b,10.9,3.78,1.03,lod)

def shaft(b,lod):
    n=40 if lod else 64
    # Three red gauge bands mark the shaft, each with a recessed-looking inspection light.
    profile=[(10.88,1.58),(11.28,1.52),(17.18,1.42),(17.73,1.41),(24.25,1.32),(24.82,1.31),(31.77,1.20),(32.32,1.19),(33.77,1.17)]
    for k,(a,c) in enumerate(zip(profile,profile[1:])):b.lathe((0,CY),[a,c],BRICK if k in (2,4,6)else WALL,n,label='signal shaft red band'if k in (2,4,6)else'tapered signal shaft')
    for z,r in [(17.4,1.425),(24.5,1.325),(32.,1.205)]:
        for ang in [0,pi]:
            x,y=r*cos(ang),CY+r*sin(ang);f=Facade(b,(x-.35*sin(ang),y+.35*cos(ang)),(x+.35*sin(ang),y-.35*cos(ang)),'inspection aperture');f.box(0,z,.56,.76,.12,-.11,TRIM,'inspection frame');f.box(0,z,.32,.47,.15,-.15,GLASS,'dark inspection window')
    b.lathe((0,CY),[(33.75,1.17),(34.03,1.25),(34.25,1.43),(34.39,1.44),(34.56,1.32),(34.83,1.48),(35.08,1.48),(35.23,1.37),(35.49,1.58),(35.68,1.60)],BRICK,n,label='upper signal crown')
    for i in range(16):
        t=2*pi*i/16;b.box((1.23*cos(t),CY+1.23*sin(t),33.78),(.17,.17,.52),BRICK,label='corbel under crown')
    b.lathe((0,CY),[(35.64,1.58),(35.76,1.68),(35.86,1.68),(36.01,1.42)],TRIM,n,label='upper instrument deck');gallery_rail(b,36.01,1.44,.79,lod,True)
    b.lathe((0,CY),[(35.97,.30),(36.25,.25),(41,.18),(45.28,.13),(47.40,.073)],IRON,12 if lod else 20,label='flagstaff')
    for axis in [(1,0),(0,1)]:
        dx,dy=axis;b.tube([(-3.02*dx,CY-3.02*dy,44.54),(3.02*dx,CY+3.02*dy,44.54)],.076,IRON,8,'crossed signal yard');
        for sign in [-1,1]:
            x,y=sign*2.93*dx,CY+sign*2.93*dy;b.tube([(x,y,44.54),(0,CY,46.72)],.027,IRON,5,'yardarm brace');b.tube([(x,y,44.54),(x,y,36.15)],.014 if not lod else .023,IRON,4,'signal halyard')
    b.tube([(.07,CY,40.38),(1.91,CY,40.38),(.12,CY,41.63)],.052,IRON,6,'lower signal bracket');b.tube([(-.56,CY,46.84),(.68,CY,46.84)],.048,IRON,7,'weather vane spindle');b.add([(.58,CY,46.84),(.16,CY,47.11),(.16,CY,46.60),(.58,CY+.045,46.84),(.16,CY+.045,47.11),(.16,CY+.045,46.60)],[(0,1,2),(5,4,3),(0,3,4,1),(1,4,5,2),(2,5,3,0)],IRON,'weather vane arrow')

def add_building(b,lod):
    x=3.62;y0=-9.98;y1=5.49
    b.plan_prism(box(-x,y0,x,y1),0,.18,BASE,'station house foundation');b.plan_prism(box(-x,y0,x,y1),9.64,9.87,ROOF,'flat roof');b.plan_prism(box(-x+.23,y0+.23,x-.23,y1-.23),9.87,9.94,ROOF,'roof walking surface')
    end=masonry(b,(-x,y0),(x,y0),[(0,5.24,1.50,8.64,False)],(0,1.78,3.95),[0]);end.box(-1.54,2.76,.58,.41,.07,.10,SIGN,'heritage plaque');end.beam(4.44,.20,.63,TRIM,width=5.45)
    for a,c in [((x,y0),(x,y1)),((-x,y1),(-x,y0))]:
        wins=[(u,z,1.22,hi,False)for u in [-5.22,-2.12,1.02,4.03]for z,hi in [(1.03,3.75),(5.20,8.75)]];f=masonry(b,a,c,wins,crests=[-5.22,1.02]);
        for u in [-6.86,-3.7,-.56,2.57,5.83]:f.box(u,4.96,.30,9.46,.34,.12,TRIM,'side pilaster')
    masonry(b,(x,y1),(-x,y1),[],cornice=False)
    # Pale quoins tie the two red-banded corner faces into a continuous jamb.
    for edge in (-x,x):
        b.box((edge,y0,4.91),(.36,.36,9.50),TRIM,label='continuous station corner pier')
        b.box((edge,y0,.30),(.48,.48,.54),BASE,label='station corner plinth')
        for z in (4.42,4.64,9.38,9.59):
            b.box((edge,y0,z),(.49,.49,.13),TRIM,label='corner moulding return')
    drum(b,lod);shaft(b,lod)
