"""Entrance arch, clock drum, pediments and enclosed upper watch room in the 1908 plate."""
import math
import numpy as np
from shapely.geometry import LineString,Point,Polygon,box
from shapely.ops import unary_union
from photo_architecture import Facade
from elevation import arch,rim,sash,RED,STONE,IVORY,GLASS,FRAME,JOINT,MASONRY,DARK

CLOCK='Weathered ivory clock dial'
METAL='Dark metal clock and rail'
WALL='Ochre entrance masonry'


def pediment(f,z,h,lod):
    half=f.length/2+.18
    pts=[(x,z+h*(1-(x/half)**2))for x in np.linspace(-half,half,15 if lod else 37)]
    shell=Polygon([(-half,z-.20),(half,z-.20),*pts[::-1]])
    f.prism(shell,-.32,.20,MASONRY,'Pediment / tympanum')
    curved=LineString(pts).buffer(.155,cap_style='flat',join_style='round')
    f.prism(curved,.08,.38,STONE,'Pediment / architrave')
    f.beam(z-.16,.27,.42,STONE,label='Pediment / lower ledge')
    raised=LineString([(a*.84,z+.16+(b-z)*.70)for a,b in pts]).buffer(.065)
    f.prism(raised,.215,.269,RED,'Pediment / inner moulding')
    f.prism(Point(0,z+.88).buffer(.22,quad_segs=6),.19,.265,DARK,'Pediment / centre vent')


def dial(f,z,size,lod,with_hands=True):
    n=16 if lod else 39
    outer=Point(0,z).buffer(size+.19,quad_segs=n)
    circle=Point(0,z).buffer(size,quad_segs=n)
    f.prism(outer,-.013,.108,STONE,'Clock / surround')
    f.prism(outer.buffer(-.065).difference(circle),.107,.22,METAL,'Clock / bezel')
    f.prism(circle,.108,.154,CLOCK if with_hands else STONE,'Clock / face')
    if not with_hands:return
    for i in range(12 if lod else 60):
        angle=i*2*math.pi/(12 if lod else 60);major=lod or i%5==0
        direction=np.array([math.sin(angle),math.cos(angle)])
        # The index positions are more legible in the book than any printed numerals.
        start=direction*(size-(.23 if major else .13))+[0,z]
        end=direction*(size-.068)+[0,z]
        f.prism(LineString([start,end]).buffer(.035 if major else .016,cap_style='flat'),
                .153,.172,METAL,'Clock / hour and minute indices')
    for degrees,length,width in [(134,.58,.067),(218,.83,.048)]:
        angle=math.radians(degrees);direction=np.array([math.sin(angle),math.cos(angle)])
        left=np.array([-direction[1],direction[0]])
        path=Polygon([tuple(-direction*.16+left*width+[0,z]),
                      tuple(direction*(size*length)+[0,z]),tuple(-direction*.16-left*width+[0,z])])
        f.prism(path,.171,.212,METAL,'Clock / metal hands')
    f.prism(Point(0,z).buffer(.112,quad_segs=10),.210,.245,METAL,'Clock / centre pin')


def rails(b,start,end,height,lod,label,post_count=None):
    start=np.asarray(start,dtype=float);end=np.asarray(end,dtype=float)
    unit=end-start;n=post_count or max(3,int(np.linalg.norm(unit[:2])/.53))
    b.tube([start+[0,0,height],end+[0,0,height]],.095,STONE,8 if lod else 12,label+' / handrail')
    for t in np.linspace(0,1,n):
        p=start+t*unit
        if lod:
            b.tube([p,p+[0,0,height]],.064,STONE,6,label+' / balusters')
        else:
            levels=[(0,.111),(.08,.125),(.16,.070),(.27,.084),(.40,.110),(.58,.067),(.79,.074),(.85,.11)]
            points=[];faces=[];sides=8
            for z,r in levels:
                for a in np.arange(sides)*2*np.pi/sides:
                    points.append(p+[r*math.cos(a),r*math.sin(a),z*height/.85])
            for row in range(len(levels)-1):
                for i in range(sides):
                    a=row*sides+i;c=row*sides+(i+1)%sides
                    faces.append((a,c,c+sides,a+sides))
            faces.extend([tuple(range(sides-1,-1,-1)),tuple(range(len(points)-sides,len(points)))])
            b.add(points,faces,STONE,label+' / balusters')


def stairs(b,center_y,lod):
    landing=3.18;span=2.42;y=center_y-1.21
    b.box((0,y,landing-.19),(6.5,span,.38),STONE,label='Entrance / landing')
    b.box((0,y,.15),(6.5,span,.30),STONE,label='Entrance / plinth')
    for x in [-2.73,0,2.73]:
        b.box((x,y,landing/2),(.55,span-.28,landing),MASONRY,label='Entrance / landing piers')
    # Each symmetrical flight runs out to the side of the upper terrace.
    for sign in [-1,1]:
        count=22;run=6.18
        for i in range(count):
            h=landing*(count-i)/count
            x=sign*(3.25+run*(i+.5)/count)
            b.box((x,y,h/2),(run/count+.002,span,h),STONE,label='Entrance / stair treads')
        for side in [-1,1]:
            Y=y+side*(span/2-.16)
            rails(b,(sign*3.25,Y,landing+.02),(sign*(3.25+run),Y,landing/count+.02),
                  .89,lod,'Entrance / stair rail')
        b.box((sign*(3.25+run),y-span/2+.16,.66),(.44,.44,1.32),STONE,label='Entrance / lower newels')
    rails(b,(-3.19,y-span/2+.15,landing),(3.19,y-span/2+.15,landing),.94,lod,'Entrance / front balustrade')


def faces(b,x0,x1,y0,y1,title):
    corners=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
    return [Facade(b,a,c,title+' / '+n)for a,c,n in zip(corners,corners[1:]+corners[:1],['Front','Right','Back','Left'])]


def column_edges(f,bottom,top,width,label,lod):
    for sign in (-1,1):
        u=sign*(f.length/2-width/2)
        f.box(u,(bottom+top)/2,width,top-bottom,.22,.11,RED,label+' / shaft')
        f.box(u,bottom+.26,width+.19,.52,.32,.15,STONE,label+' / base')
        f.box(u,top-.19,width+.24,.38,.34,.16,STONE,label+' / capital')
        if not lod:
            for z in np.arange(bottom+.8,top-.4,.39):
                f.box(u,z,width+.05,.051,.25,.123,JOINT,label+' / coursing')


def build_tower(b,x0,x1,y0,y1,lod):
    width=x1-x0; cx=(x1+x0)/2;cy=y0+width*.52
    lower=faces(b,x0,x1,y0,y1,'Entry block')
    face=lower[0]
    shape=arch(0,3.18,3.10,5.42,14 if lod else 32)
    face.wall(.04,11.84,[shape],.60,WALL)
    face.prism(shape.buffer(.04),-2.20,-2.05,DARK,'Portal / deep inner arch')
    rim(face,0,3.18,3.10,5.42,IVORY,'Portal',lod,.25)
    segments=11
    for i in range(segments):
        angle=np.linspace(i*math.pi/segments+.006,(i+1)*math.pi/segments-.006,3 if lod else 6)
        inner,outer=1.59,2.27 if i==segments//2 else 2.19
        coords=[(r*math.cos(h),5.42+r*math.sin(h)) for r,hs in [(inner,angle),(outer,angle[::-1])]for h in hs]
        face.prism(Polygon(coords),.06,.19 if i!=segments//2 else .27,
                   IVORY if i%3 else STONE,'Portal / radiating stone voussoirs')
    for hand in (-1,1):
        for i in range(7):
            face.box(hand*1.91,3.28+i*.35,.58,.304,.17,.14,
                     IVORY if i%3 else STONE,'Portal / graded jamb stones')
    face.box(0,9.58,width-1.63,.23,.37,.18,STONE,'Portal / pediment shelf')
    for u in np.linspace(-width/2+1.03,width/2-1.03,17 if not lod else 11):
        face.box(u,9.83,.12,.29,.27,.13,IVORY,'Portal / frieze dentils')
    face.box(0,10.08,width-1.27,.22,.57,.21,STONE,'Portal / hood moulding')
    for k in range(6):
        face.box(0,7.94+k*.31,width-1.82,.085,.10,.057,STONE,'Portal / ashlar bands')
    for f in lower:
        column_edges(f,.04,11.27,.79,'Entry quoins',lod)
        f.beam(11.46,.58,.38,STONE,label='Deep bracketed cornice')
        f.beam(11.84,.23,.53,IVORY,label='Cornice coping')
    # Short flanks are visible above the recessed central wings. They repeat
    # the surviving framed operable windows visible on the side of the portal.
    lower[2].wall(.04,11.84,(),.43,MASONRY)
    for f in [lower[1],lower[3]]:
        u=-f.length*.30 if f is lower[1] else f.length*.30
        levels=[(3.43,4.72),(7.76,9.45)]
        windows=[arch(u,sill,1.52,spring,12 if lod else 24)for sill,spring in levels]
        f.wall(.04,11.84,windows,.43,MASONRY)
        for shape,(sill,spring) in zip(windows,levels):
            sash(f,shape,u,sill,spring,1.52,24,lod,'Portal side window')
            rim(f,u,sill,1.52,spring,RED,'Side / brick rim',lod)
    stairs(b,y0,lod)
    # The tower above the roof is square. All four faces have curved pediments.
    stages=[(width*.47,11.96,21.41,'Clock drum'),(width*.392,25.48,31.88,'Upper lookout')]
    # The 1908 close-up shows a continuous square shoulder behind the
    # four curved pediments. It supports the enclosed room above their crests.
    neck_half=width*.405
    b.box((cx,cy,(21.40+25.55)/2),(2*neck_half,2*neck_half,25.55-21.40),
          MASONRY,label='Upper lookout / masonry neck behind pediments')
    b.box((cx,cy,25.30),(2*neck_half+.21,2*neck_half+.21,.23),
          STONE,label='Upper lookout / supporting ledge')
    b.box((cx,cy,25.47),(2*neck_half+.32,2*neck_half+.32,.13),
          RED,label='Upper lookout / supporting brick course')
    for idx,(half,lo,hi,title) in enumerate(stages):
        radius_y=half
        fs=faces(b,cx-half,cx+half,cy-radius_y,cy+radius_y,title)
        b.box((cx,cy,lo+.1),(2*half,2*radius_y,.20),STONE,label=title+' / floor')
        for i,f in enumerate(fs):
            sill,spring,w=(12.08,14.96,1.48) if idx==0 else (26.67,28.72,1.72)
            opening=arch(0,sill,w,spring,14 if lod else 30)
            f.wall(lo,hi,[opening],.4,MASONRY)
            sash(f,opening,0,sill,spring,w,24,lod,'Tower light')
            rim(f,0,sill,w,spring,IVORY,'Tower light',lod)
            column_edges(f,lo,hi,.48,'Corner pilasters',lod)
            f.beam(hi-.18,.37,.24,STONE,label='Tower stage cornice')
            if idx==0:
                if i in (0,1):dial(f,17.63,min(width*.186,1.43),lod,i==0)
                pediment(f,hi,3.10,lod)
            else:f.beam(hi+.19,.29,.39,IVORY,label='Lookout cap')
        b.box((cx,cy,hi+.02),(2*half+.19,2*radius_y+.19,.20),STONE,label=title+' / deck')
        if idx:
            for f in fs:
                f.beam(hi+.54,.31,.42,STONE,label='Lookout / rail footing')
                rails(b,f.point(-f.length/2,hi+.70,0),f.point(f.length/2,hi+.70,0),1.00,lod,
                      'Lookout / roof rail')
    b.box((cx,cy,33.72),(1.22,1.02,.17),FRAME,label='Lookout / instrument stand')
    for x in (-.49,.49):
        for y in (-.39,.39):
            b.box((cx+x,cy+y,34.78),(.13,.13,2.05),FRAME,label='Lookout / instrument frame')
    b.box((cx,cy,35.89),(1.49,1.27,.17),FRAME,label='Lookout / weather hood')
    b.tube([(cx,cy,35.97),(cx,cy,38.22)],.062,METAL,8,label='Lookout / top rod')
    b.tube([(cx-.34,cy,37.65),(cx+.32,cy,37.65)],.044,METAL,8,label='Lookout / vane')
