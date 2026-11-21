"""Savoy Apartments' two street elevations, photographed in 2016 and 2021."""
import math
from pathlib import Path
import sys
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Facade

FRONT = [(-38.1624596,23.1245058),(-5.0305363,0),(5.0305363,0),(33.9747491,38.3314848)]
GROUND = 3.66
FLOOR = 3.16
CORNICE = GROUND + FLOOR * 7
DEPTH = 3.10
WALL,WHITE,STONE,SASH,GLASS,SHADE,ROOF,METAL,BACK = ('pebbled cement','ivory moulding','base stone','painted steel','grey blue glass','sheltered stucco','roof finish','ribbed metal','section finish')
PALETTE={name:dict(color=list(rgb),roughness=r,metallic=m) for name,rgb,r,m in [
    (WALL,(.594,.555,.485),.91,0),(WHITE,(.870,.846,.764),.85,0),(STONE,(.53,.50,.43),.88,0),
    (SASH,(.126,.145,.139),.55,.20),(GLASS,(.288,.364,.383),.29,.20),(SHADE,(.290,.276,.250),.94,0),
    (ROOF,(.402,.399,.373),.91,0),(METAL,(.491,.455,.389),.68,.24),(BACK,(.585,.57,.53),.90,0)]}

def panel(f,u,z,w,h,d0,d1,mat,label):
    f.box(u,z,w,h,d1-d0,(d0+d1)/2,mat,label)

def glazed(f,u,z,w,h,lod,holes,cols=3,rows=4,d=-.18):
    opening=box(u-w/2,z,u+w/2,z+h);holes.append(opening)
    f.prism(opening.buffer(.006,join_style=2),d-.045,d,GLASS,'steel casement glass')
    rails=[box(u-w/2+j*w/cols-.024,z,u-w/2+j*w/cols+.024,z+h)for j in range(1,cols)]
    levels=[1] if lod and rows==4 else range(1,rows)
    for j in levels:
        zmid=z+h*j/(2 if lod and rows==4 else rows)
        rails.append(box(u-w/2,zmid-.023,u+w/2,zmid+.023))
    frame=opening.difference(opening.buffer(-.052,join_style=2).difference(unary_union(rails)))
    f.prism(frame,d+.007,d+.063,SASH,'steel casement frames')

def ribbed_box(f,u,z,lod):
    panel(f,u,z,1.11,.61,.016,.31,METAL,'window sill box')
    for j in range(3 if lod else 6):
        dz=(j-(1 if lod else 2.5))*(.168 if lod else .083)
        panel(f,u,z+dz,1.18,.044,.30,.39,METAL,'ventilated metal blades')

def folded_plan(f,coords):
    return Polygon([f.point(x,0,d)[:2] for x,d in coords])

def shopfront(f,lod):
    holes=[];count=max(2,round(f.length/4.18));width=f.length/count
    for j in range(count):
        u=(j+.5)*width-f.length/2
        glazed(f,u,.19,width-.41,2.48,lod,holes,3,rows=2,d=-.30)
    f.wall(0,GROUND,holes,.29,WALL)
    panel(f,0,3.13,f.length,.93,-.025,.13,WHITE,'shop fascia')
    panel(f,0,3.61,f.length,.105,-.01,.235,WHITE,'shop fascia cap')
    panel(f,0,.11,f.length,.17,-.006,.042,STONE,'shop stone base')

def stair_bay(f,u,width,lod,openings,descending):
    # Both sides of each photographed landing return to the street wall in plan.
    # Behind the faceted parapets, pitched solid strings cross the openings.
    a,b=u-width/2,u+width/2;clip=.16*width
    for j in range(7):
        z=GROUND+FLOOR*j;top=z+FLOOR-.16
        if j==6:
            shoulder=width*.18
            opening=Polygon([(a,z+.09),(b,z+.09),(b,top-.84),(b-shoulder,top),(a+shoulder,top),(a,top-.84)])
        else:
            opening=box(a,z+.09,b,top)
        openings.append(opening)
        panel(f,u,z+FLOOR*.54,width-.03,FLOOR-.12,-2.51,-2.45,SHADE,'stair bay back')
        for side in [a+.05,b-.05]:
            panel(f,side,z+FLOOR*.5,.10,FLOOR+.01,-2.47,.015,SHADE,'stair returns')
        end_depth=-.27 if j==6 else .13
        middle=.33 if j==6 else .73
        walk=folded_plan(f,[(a,-2.46),(b,-2.46),(b,end_depth),(b-clip,middle),(a+clip,middle),(a,end_depth)])
        f.builder.plan_prism(walk,z+.04,z+.19,STONE,f.label+'/stair landing floor')
        lips=[(a,end_depth),(a+clip,middle),(b-clip,middle),(b,end_depth)]
        width_lip=.15
        wall=folded_plan(f,lips+[(x,d-width_lip)for x,d in reversed(lips)])
        f.builder.plan_prism(wall,z+.14,z+1.06,WALL,f.label+'/folded landing parapets')
        f.builder.plan_prism(wall.buffer(.025,join_style=2),z+1.055,z+1.13,WHITE,f.label+'/light landing rims')
        for sign in [-1,1]:
            panel(f,u+sign*.21*width,z+1.69,.17,2.98,-1.29,-1.05,WHITE,'landing supports')
        # The street photos show the diagonal strings behind the open landing;
        # their hidden flights and disposition behind the wall are unverified.
        x0,x1=a+.16*width,b-.16*width;z0,z1=z+.40,z+2.85
        if descending:z0,z1=z1,z0
        diag=Polygon([(x0,z0),(x1,z1),(x1,z1+.32),(x0,z0+.32)])
        f.prism(diag,-1.22,-.93,WHITE,'exposed diagonal stair string')
        if not lod:
            for k in range(1,9):
                t=k/9;x=x0+(x1-x0)*t;zz=z0+(z1-z0)*t
                panel(f,x,zz+.25,(x1-x0)/8.6,.07,-1.21,-.90,WHITE,'exposed step noses')

def roof_rooms(f):
    for p,w,h in [(.15,3.42,2.50),(.51,3.07,2.08),(.83,3.57,2.46)]:
        u=f.length*(p-.50);z=CORNICE+.36
        panel(f,u,z+h/2,w,h,-3.13,-1.2,WALL,'set back rooftop room')
        panel(f,u,z+h,w+.26,.15,-3.22,-1.08,WHITE,'rooftop room cap')
        for t in [-.60,.60]:panel(f,u+t,z+h-.68,.59,.41,-1.20,-1.155,SHADE,'roof room vent')

def wing(f,lod,corner_sign):
    shopfront(f,lod);holes=[]
    # Side-on district photograph constrains two open stair stacks with two
    # casement lines in the pier between them and one at each extreme.
    for frac in [.264,.730]:
        stair_bay(f,corner_sign*(frac-.5)*f.length,f.length*.228,lod,holes,descending=(frac>.5)==(corner_sign>0))
    for frac in [.084,.463,.562,.920]:
        x=corner_sign*(frac-.50)*f.length
        for level in range(7):
            z=GROUND+FLOOR*level+.57
            glazed(f,x,z,1.23,1.43,lod,holes,2,rows=3)
            if level>0:ribbed_box(f,x,z-.37,lod)
    # Place the top frieze with the same openings as the main wall.
    basewall=box(-f.length/2,GROUND,f.length/2,CORNICE)
    cut=unary_union(holes)
    f.prism(basewall.difference(cut),-.22,.006,WALL,'street wall with real openings')
    trim=box(-f.length/2,CORNICE-1.92,f.length/2,CORNICE).difference(cut)
    f.prism(trim,.011,.029,WHITE,'upper frieze with open windows')
    for z,d,h in [(CORNICE-.08,.16,.18),(CORNICE+.10,.46,.20),(CORNICE+.28,.64,.18)]:
        panel(f,0,z,f.length,h,-.12,d,WHITE,'projecting roof cornice')
    roof_rooms(f)

def fan_relief(f,x,z,lod,sign):
    # The pale top panel has shell-like radiating ornament beside the attic light.
    disk=Point(x,z+.10).buffer(.53,quad_segs=6 if lod else 12)
    shape=disk.intersection(box(x-.60,z-.38,x+.60,z+.47))
    f.prism(shape,.034,.093,WHITE,'top shell relief')
    n=5 if lod else 9
    for k in range(n):
        theta=(34+112*k/(n-1))*math.pi/180
        dx=sign*.46*math.cos(theta);dz=.52*math.sin(theta)
        pts=[f.point(x,z-.24,.102),f.point(x+dx,z-.24+dz,.102)]
        f.builder.tube(pts,.023,WHITE,5 if lod else 8,f.label+'/radiating ornament')

def corner(f,lod):
    shopfront(f,lod);holes=[];w=f.length
    for level in range(7):
        z=GROUND+level*FLOOR+.57
        for x in [-w*.387,w*.387]:
            glazed(f,x,z,1.13,1.43,lod,holes,2,rows=3)
            if level:ribbed_box(f,x,z-.37,lod)
        if level in (0,6):
            glazed(f,0,z,2.35 if level==6 else 1.51,1.50,lod,holes,3)
    zb=GROUND+FLOOR-.13;zt=GROUND+6*FLOOR+.02
    xs=[(-2.04,0),(-1.36,.78),(1.36,.78),(2.04,0)]
    holes.append(box(-2.032,zb+.01,2.032,zt-.01))
    for j,(a,b) in enumerate(zip(xs,xs[1:])):
        edge=Facade(f.builder,f.point(a[0],0,a[1])[:2],f.point(b[0],0,b[1])[:2],f.label+' oriel')
        gl=[]
        for level in range(1,6):
            z=GROUND+FLOOR*level+.57
            glazed(edge,0,z,edge.length-.064,1.51,lod,gl,4 if j==1 else 1,d=-.078)
        edge.wall(zb,zt,gl,.11,WALL)
        for level in range(1,6):
            panel(edge,0,GROUND+FLOOR*level+.55,edge.length,.104,-.012,.098,WHITE,'faceted oriel sills')
    cap=folded_plan(f,[(-2.04,-.1),(2.04,-.1),(2.04,0),(1.36,.78),(-1.36,.78),(-2.04,0)])
    f.builder.plan_prism(cap,zt-.05,zt+.078,WHITE,f.label+'/oriel parapet')
    for j in range(4):
        f.builder.plan_prism(cap.buffer(-j*.072,join_style=2),zb-.115*j-.06,zb-.115*j+.068,STONE,f.label+'/stepped oriel corbel')
    whole=box(-w/2,GROUND,w/2,CORNICE);cut=unary_union(holes)
    f.prism(whole.difference(cut),-.22,0,WALL,'corner wall')
    f.prism(box(-w/2,CORNICE-1.94,w/2,CORNICE).difference(cut),.012,.031,WHITE,'ornamented attic frieze')
    for sign in [-1,1]:fan_relief(f,sign*2.08,CORNICE-1.22,lod,sign)
    for z,d,h in [(CORNICE-.08,.16,.18),(CORNICE+.10,.46,.20),(CORNICE+.28,.64,.18)]:
        panel(f,0,z,w,h,-.12,d,WHITE,'corner cornice')
    for x in [-2.62,2.65]:
        panel(f,x,CORNICE+1.86,2.90,3.05,-3.11,-1.51,WALL,'paired junction rooftop rooms')
        panel(f,x,CORNICE+3.39,3.19,.17,-3.21,-1.37,WHITE,'junction rooftop room cap')

def add_savoy(builder,lod):
    left=Facade(builder,FRONT[0],FRONT[1],'Yanqing Road')
    right=Facade(builder,FRONT[2],FRONT[3],'Changshu Road')
    wing(left,lod,-1);wing(right,lod,1)
    corner(Facade(builder,FRONT[1],FRONT[2],'north-west chamfer'),lod)
    strip=LineString(FRONT).buffer(DEPTH,single_sided=True,join_style=2)
    builder.plan_prism(strip,CORNICE+.19,CORNICE+.31,ROOF,'limited street roof return')
    back=LineString(FRONT)
    edges=list(strip.exterior.coords)
    for a,b in zip(edges,edges[1:]):
        if back.distance(Point((a[0]+b[0])/2,(a[1]+b[1])/2))<.025:continue
        Facade(builder,a,b,'unobserved section').wall(0,CORNICE+.20,thickness=.04,material=BACK)
