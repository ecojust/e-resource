"""Two banks of steel windows on the river elevation, after the individually captioned exterior close-up."""
from math import sin, cos, pi
from pathlib import Path
from shapely.geometry import box,Polygon,Point
from shapely.ops import unary_union
from profile_tools import BRICK,cb,slab,bricks_uv
import numpy as np

GRAY='Aggregate ledge';EDGE='Pale stone edge';RECESS='Weathered recess';STEEL='Dark blue steel';BEAD='Steel glazing bead';GLASS='Reflected blue glazing';OPEN='Pale reflected open pane';SWING='Sky blue reflected in a tilted pane';RELIEF='Faceted carved stone';DARK='Recess in relief'
colors={BRICK:(255,255,255),GRAY:(151,148,143),EDGE:(182,176,160),RECESS:(132,129,123),STEEL:(49,61,67),BEAD:(59,76,83),GLASS:(70,105,126),OPEN:(176,191,196),SWING:(64,125,155),RELIEF:(174,170,157),DARK:(114,111,104)}
PALETTE={k:{'color':[(n/255)**2.2 for n in v],'roughness':.86}for k,v in colors.items()};PALETTE[BRICK]['texture']=str(Path(__file__).with_name('finish.png'))
HALF=2.18
LEVELS=[(1.18,3.61),(5.36,7.30)]
def leaf(b,x,z,width,height,angle,lod,upper):
    start=len(b.parts)
    def rect(a,c,y0,y1,lo,hi,mat,name):cb(b,a,c,y0,y1,lo,hi,mat,name)
    edge=.039
    rect(0,width,.165,.205,z,z+edge,STEEL,'Bottom rail of opening casement')
    rect(0,width,.165,.205,z+height-edge,z+height,STEEL,'Top rail of opening casement')
    for a in (0,width-edge):rect(a,a+edge,.165,.205,z+edge,z+height-edge,STEEL,'Opening steel stile')
    for j in range(1,3):rect(edge,width-edge,.182,.211,z+height*j/3-.013,z+height*j/3+.013,BEAD,'Opening horizontal glazing bar')
    for j in range(3):rect(edge,width-edge,.219,.230,z+max(edge,height*j/3),z+min(height-edge,height*(j+1)/3),upper,'Glazing in hinged leaf')
    # Rotate the actual framed sash and its glass about the outer hinge.
    for obj in b.parts[start:]:
        verts=np.asarray(obj['vertices'],dtype=float);u=verts[:,0].copy();v=verts[:,1]-.195
        verts[:,0]=x+u*cos(angle)-v*sin(angle);verts[:,1]=.195+u*sin(angle)+v*cos(angle);obj['vertices']=verts.tolist()
def face(b,points,mat,label):
    b.parts.append(dict(label=label,material=mat,vertices=[tuple(v)for v in points],triangles=[(0,2,1)]))
def model(b,lod=False):
    openings=[box(-HALF,lo,HALF,hi) for lo,hi in LEVELS]
    slab(b,box(-2.68,.0,2.68,8.23).difference(unary_union(openings)),.04,.58,BRICK,'Recessed river-facing bay')
    for side in [-1,1]:
        a,c=sorted((side*2.68,side*3.04));cb(b,a,c,-.11,.59,0,8.48,BRICK,'Stepped vertical pier')
        a,c=sorted((side*2.55,side*2.68));cb(b,a,c,-.04,.59,0,8.48,BRICK,'Slender return at inner pier')
    cb(b,-2.68,2.68,-.105,.58,8.23,8.50,GRAY,'Projecting top band above the lintel')
    for k,(lo,hi) in enumerate(LEVELS):
        cb(b,-2.25,2.25,-.126,.28,lo-.074,lo,EDGE,'Narrow projecting sill')
        cb(b,-2.22,2.22,.005,.26,hi,hi+.047,RECESS,'Dark lintel return')
        cols=5;wid=2*HALF/cols;transom=lo+.76*(hi-lo) if k==0 else hi
        for j in range(cols):
            x0=-HALF+j*wid;x1=x0+wid
            cb(b,x0,x0+.054,.154,.24,lo,hi,STEEL,'Major horizontal-window mullion')
            if j==cols-1:cb(b,x1-.04,x1,.154,.24,lo,hi,STEEL,'Closing jamb')
            cb(b,x0,x1,.157,.24,lo,lo+.045,STEEL,'Fixed bottom rail')
            cb(b,x0,x1,.157,.24,hi-.045,hi,STEEL,'Fixed top rail')
            if k==0:
                cb(b,x0,x1,.156,.238,transom-.023,transom+.024,STEEL,'Deep continuous transom of lower window')
                cb(b,x0+.055,x1-.008,.253,.267,transom+.024,hi-.045,GLASS,'Fixed upper light')
                cb(b,x0+wid/2-.016,x0+wid/2+.016,.20,.253,transom+.024,hi-.045,BEAD,'Upper-light glazing bar')
            choose=(j==0 if k==0 else j in (0,1,4))
            if choose:
                hinge=x0+.055;angle=-(52 if j==0 else 24 if j==1 else 35)*pi/180
                leaf(b,hinge,lo+.046,wid-.084,transom-lo-.09,angle,lod,OPEN if j==0 else SWING)
                cb(b,x0+.054,x1-.01,.575,.592,lo+.048,transom-.044,DARK,'Recess visible behind open pane')
            else:
                cb(b,x0+.054,x1-.01,.253,.267,lo+.045,transom-.043,GLASS,'Recessed fixed glazing')
                cb(b,x0+wid/2-.016,x0+wid/2+.016,.197,.257,lo+.045,transom-.041,BEAD,'Vertical glazing bar')
                for jz in [1,2]:
                    z=lo+(transom-lo)*jz/3;cb(b,x0+.052,x1-.008,.194,.257,z-.014,z+.014,BEAD,'Horizontal glazing bar')
    for bottom,top in [(0.10,1.04),(3.76,5.22)]:
        for left,right in [(-1.99,-.98),(-.85,.75),(.90,1.99)]:
            outer=box(left,bottom,right,top);inner=box(left+.048,bottom+.048,right-.048,top-.048)
            slab(b,outer.difference(inner),-.041,.06,GRAY,'Raised border of rectangular spandrel panel')
            slab(b,inner,.013,.046,RECESS,'Inset centre of spandrel panel')
    # Two carved fields and a round boss separate the paired repeated angular folds.
    for sign in [-1,1]:
        a,c=sorted((sign*.245,sign*2.09));cb(b,a,c,-.045,.055,7.39,7.98,GRAY,'Rectangular relief stone')
        for j in range(4):
            cx=a+(j+.5)*(c-a)/4;hz=.23;hx=(c-a)/8*.95
            rim=[(cx-hx,-.059,7.695),(cx,-.059,7.695+hz),(cx+hx,-.059,7.695),(cx,-.059,7.695-hz)]
            apex=(cx+.12*hx,-.166,7.695+.03)
            for i in range(4):face(b,[rim[i],rim[(i+1)%4],apex],RELIEF,'Four planes of a single folded ornament')
            if not lod:cb(b,cx-.012,cx+.012,-.065,-.042,7.405,7.43,DARK,'Shadow below the carved tip')
    for radius,y0,mat in [(.18,-.094,DARK),(.133,-.135,GRAY),(.089,-.178,RELIEF)]:
        slab(b,Point(0,7.67).buffer(radius,quad_segs=10 if lod else 24),y0,.055,mat,'Circular centre of the lintel rosette')
    bricks_uv(b)
