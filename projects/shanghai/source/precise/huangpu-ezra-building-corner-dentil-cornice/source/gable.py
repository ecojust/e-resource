"""Model a single cut corner with two sashes, a three-sided projecting cornice and a festoon."""
from pathlib import Path
from math import pi,cos,sin
from shapely.geometry import box,Polygon,Point
from shapely.ops import unary_union
import numpy as np
from profile_tools import BRICK,cb,slab,bricks_uv
COVE='Shaded undercut';CORNICE='Pale cornice stone';STONE='Cut pale window trim';SASH='Reddish timber';GLASS='Dark reflected glazing';FLOWER='Weathered garland';JOINT='Dark ashlar bedding';FIELD='Pale festoon panel'
colors={BRICK:(255,255,255),COVE:(110,112,106),CORNICE:(189,187,176),STONE:(205,198,181),SASH:(105,68,56),GLASS:(82,92,93),FLOWER:(170,162,145),JOINT:(124,126,119),FIELD:(193,190,178)}
PALETTE={k:{'color':[(i/255)**2.2 for i in v],'roughness':.92}for k,v in colors.items()};PALETTE[BRICK]['texture']=str(Path(__file__).with_name('finish.png'))
LEVELS=[(.62,2.49,.64),(3.48,4.85,.60)]
def rosette(b,cx,z,r,lod):
    count=6 if lod else 9;points=[]
    for i in range(count*2):
        t=i*pi/count;p=r*(1 if i%2==0 else .57);points.append((cx+p*cos(t),z+p*sin(t)))
    slab(b,Polygon(points),-.184,-.116,FLOWER,'Carved flower in festoon')
    slab(b,Point(cx,z).buffer(.26*r,quad_segs=2 if lod else 4),-.202,-.177,STONE,'Raised centre of flower')
def bay(b,lod):
    field=box(-1.46,.0,1.46,7.44);holes=[box(-rad,low,rad,hi)for low,hi,rad in LEVELS]
    slab(b,field.difference(unary_union(holes)),0,.46,BRICK,'Cut-corner bay wall')
    for i,(low,hi,r)in enumerate(LEVELS):
        cb(b,-r-.12,r+.12,-.188,.11,low-.095,low+.022,STONE,'Projecting window sill')
        for side in [-1,1]:
            x=side*(r+.071);cb(b,x-.064,x+.064,-.115,.22,low,hi+.09,STONE,'Straight moulded window jamb')
        cb(b,-r-.13,r+.13,-.115,.20,hi,hi+.092,STONE,'Square window head')
        cb(b,-r,r,.271,.295,low,hi,GLASS,'Dark recessed glazing')
        for j in [-1,0,1]:
            x=j*(r-.032);cb(b,x-.026,x+.026,.18,.264,low+.03,hi-.02,SASH,'Reddish vertical sash member')
        for z in [low+.024,low+(hi-low)*.70,hi-.031]:
            cb(b,-r,r,.162,.258,z-.027,z+.027,SASH,'Reddish horizontal sash member')
        if i==0:
            cb(b,-r-.24,r+.24,-.284,.10,hi+.48,hi+.61,CORNICE,'Head cornice above lower sash')
            cb(b,-r-.17,r+.17,-.21,.03,hi+.418,hi+.484,STONE,'Under edge of lower window cap')
            cap=Polygon([(-.21,hi+.105),(.21,hi+.105),(.27,hi+.417),(-.27,hi+.417)])
            slab(b,cap,-.19,-.03,STONE,'Broad central tab beneath lower window cap')
            for side in [-1,1]:
                x=side*.55;cb(b,x-.084,x+.084,-.178,-.02,hi+.14,hi+.412,STONE,'Carved shoulder beneath cap')
                for k in range(3):cb(b,x-.081,x+.081,-.195+.014*k,-.168,hi+.168+.065*k,hi+.195+.065*k,COVE,'Horizontal cut in the carved shoulder')
    cb(b,-1.42,1.42,-.052,.11,6.28,7.39,FIELD,'Festoon field above the cornice')
    for side in [-1,1]:
        x=side*.91
        cb(b,x-.088,x+.088,-.132,-.01,6.63,7.23,STONE,'Hanging end of garland')
        rosette(b,x,6.59,.094,lod);rosette(b,x,7.17,.12,lod)
    xs=np.linspace(-.83,.83,10)
    for i,x in enumerate(xs):
        z=6.82+.30*(x/.84)**2
        rosette(b,float(x),float(z),.130 if i%2==0 else .111,lod)
def panel(b,lo,hi,lod,side):
    before=len(b.parts)
    if side:
        cb(b,lo,hi,.004,.43,.0,7.38,BRICK,'Short return of channelled ashlar')
    # The belt courses and dentils run across the flat and turn at both junctions.
    for z0,z1,depth,mat,name in [(5.10,5.16,-.084,STONE,'Lower bead beneath cornice'),(5.16,5.25,-.132,STONE,'Broad bed moulding'),(5.25,5.32,-.174,CORNICE,'Second outward step'),(5.32,5.51,-.125,COVE,'Cornice shadow'),(5.51,5.62,-.207,CORNICE,'Cornice soffit'),(5.93,6.04,-.527,STONE,'Top horizontal dentil fascia'),(6.04,6.13,-.595,CORNICE,'Projecting drip edge'),(6.13,6.22,-.455,STONE,'Setback on top of cornice')]:
        cb(b,lo,hi,depth,.46,z0,z1,mat,name)
    cb(b,lo,hi,-.124,.10,5.61,5.92,COVE,'Recess behind the visible cornice blocks')
    n=max(1,round((hi-lo)/.26))
    for j in range(n):
        x=lo+(j+.5)*(hi-lo)/n;cb(b,x-.08,x+.08,-.418,-.10,5.657,5.928,CORNICE,'Projecting rectangular dentil')
    if side:
        for z in np.arange(.24,5.09,.35):cb(b,lo,hi,-.016,.01,float(z),float(z+.023),JOINT,'Girth joint in the channelled side return')
        for item in b.parts[before:]:
            v=np.array(item['vertices'],float);x=v[:,0].copy();yy=v[:,1].copy();axis=lo if side>0 else hi;t=side*30*pi/180
            v[:,0]=axis+(x-axis)*cos(t)-yy*sin(t);v[:,1]=(x-axis)*sin(t)+yy*cos(t);item['vertices']=v.tolist()
def model(b,lod=False):
    bay(b,lod)
    panel(b,-1.46,1.46,lod,0);panel(b,-2.82,-1.46,lod,-1);panel(b,1.46,2.82,lod,1)
    bricks_uv(b)
