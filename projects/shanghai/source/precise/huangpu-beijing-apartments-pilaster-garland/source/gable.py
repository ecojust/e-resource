"""A two-storey Beijing Apartments window bay with its floral pilaster and iron guard."""
from pathlib import Path
from math import pi,sin,cos
from shapely.geometry import Point,Polygon,LineString,box
from shapely.affinity import scale
from shapely.ops import unary_union
import numpy as np
from profile_tools import BRICK,cb,slab,bricks_uv
LIME='Pale dressed stone';SASH='Painted sash';PANE='Shaded glazing';RAIL='Black iron guard';PETAL='Ochre raised wreath';RED='Red brick trim';SHADE='Shadow under coping'
PALETTE={}
for name,rgb in [(BRICK,(255,255,255)),(LIME,(193,189,181)),(SASH,(148,147,134)),(PANE,(73,80,78)),(RAIL,(46,45,43)),(PETAL,(139,71,56)),(RED,(154,89,73)),(SHADE,(122,119,111))]:
    PALETTE[name]=dict(color=[(v/255)**2.2 for v in rgb],roughness=.9)
PALETTE[BRICK]['texture']=str(Path(__file__).with_name('finish.png'))
X=-.39;C=1.085
def oval(x,z,a,b,n):return scale(Point(x,z).buffer(1,quad_segs=n),a,b,origin=(x,z))
def raised_line(b,pts,rad,y,mat,name,n):
    slab(b,LineString(pts).buffer(rad,cap_style=1,join_style=1,quad_segs=n),y,y+.035,mat,name)
def model(b,lod=False):
    n=4 if lod else 8;rad=.77;head=5.01
    crown=lambda u:head+.13*(1-(u/rad)**2)
    path=[(X+u,crown(u))for u in np.linspace(rad,-rad,n*2+1)]
    openings=[box(X-rad,0,X+rad,1.91),Polygon([(X-rad,2.96),(X+rad,2.96),*path])]
    slab(b,box(-1.72,0,1.63,6.16).difference(unary_union(openings)),0,.39,BRICK,'Red brick around two windows')
    for low,high in [(0.,1.91),(2.96,head)]:
        cb(b,X-rad,X+rad,.286,.33,low,high,PANE,'Glass in recessed window')
        for xx in [-rad+.025,0,rad-.025]:cb(b,X+xx-.022,X+xx+.022,.198,.273,low,high,SASH,'Window stile')
        for h in [low+.04,high-.39,high-.05]:cb(b,X-rad,X+rad,.182,.27,h-.022,h+.022,SASH,'Window transom')
    slab(b,Polygon([(X-rad,head),(X+rad,head),*path[1:-1]]),.286,.33,PANE,'Curved glass behind upper head')
    us=np.linspace(-rad,rad,n*2+1)
    for a,c in zip(us,us[1:]):
        a+=.002;c-=.002
        slab(b,Polygon([(X+a,crown(a)),(X+c,crown(c)),(X+c*1.1,crown(c)+.20),(X+a*1.1,crown(a)+.20)]),-.106,.11,RED,'Segmental brick voussoir')
    slab(b,Polygon([(X-.09,5.066),(X+.09,5.066),(X+.15,5.98),(X-.15,5.98)]),-.212,.04,LIME,'Upper vertical keystone')
    slab(b,Polygon([(X-.95,2.005),(X,2.412),(X+.95,2.005),(X+.95,2.102),(X,2.54),(X-.95,2.102)]),-.19,.04,LIME,'Lower triangular pediment')
    cb(b,X-.97,X+.97,-.153,.05,1.989,2.04,LIME,'Level bottom of pediment')
    slab(b,Polygon([(X-.106,1.799),(X+.106,1.799),(X+.169,2.373),(X-.169,2.373)]),-.24,0,LIME,'Long tapered pendant stone')
    for cen,rr in [(-1.51,.105),(C,.37)]:
        cb(b,cen-rr,cen+rr,-.127,.23,0,5.77,LIME,'Full height pilaster')
        for lo,hi,y,e in [(5.71,5.76,-.157,.035),(5.76,5.80,-.181,.06),(5.80,5.87,-.205,.08),(5.87,5.96,-.224,.092)]:
            cb(b,cen-rr-e,cen+rr+e,y,.29,lo,hi,LIME,'Stepped capital')
    slab(b,oval(C,5.11,.205,.315,n).difference(oval(C,5.11,.134,.232,n)),-.185,-.12,PETAL,'Raised oval wreath')
    for a in np.linspace(0,2*pi,9,endpoint=False):
        slab(b,oval(C+.18*cos(a),5.11+.272*sin(a),.051,.056,n),-.202,-.165,PETAL,'Petal on oval wreath')
    for side in [-1,1]:
        pts=[(C+side*dx,z)for dx,z in [(.079,4.84),(.112,4.76),(.145,4.73),(.119,4.66),(.066,4.69),(.073,4.742)]]
        raised_line(b,pts,.021,-.199,PETAL,'Ribbon below oval',1 if lod else 2)
    for i,(z,rr)in enumerate([(4.60,.092),(4.52,.072),(4.445,.050),(4.382,.029)]):
        slab(b,oval(C,z,rr,.033,n),-.195+i*.012,-.12,PETAL,'Beaded drop under floral cartouche')
    cb(b,X-.827,X+.827,-.214,-.135,2.892,2.975,LIME,'Stone sill of iron guard')
    for z in [3.015,3.669,3.718]:cb(b,X-.79,X+.79,-.191,-.135,z-.017,z+.017,RAIL,'Horizontal iron guard rail')
    for k in range(12):
        x=X-.737+k*1.474/11;cb(b,x-.0105,x+.0105,-.179,-.15,3.02,3.716,RAIL,'Iron picket')
    for side in [-1,1]:
        knots=[(.25,3.06),(.206,3.18),(.112,3.245),(.099,3.318),(.131,3.351),(.169,3.326),(.160,3.291)]
        for mirror in [False,True]:
            pts=[(X+side*u,6.72-z if mirror else z)for u,z in knots]
            raised_line(b,pts,.012,-.193,RAIL,'Reversed iron scroll',1 if lod else 2)
    for lo,hi,y,mat in [(5.96,6.024,-.243,LIME),(6.024,6.082,-.194,SHADE),(6.082,6.162,-.265,LIME),(6.162,6.29,-.160,RED),(6.29,6.344,-.256,RED),(6.344,6.414,-.288,LIME)]:
        cb(b,-1.73,1.64,y,.44,lo,hi,mat,'Continuous brick and stone top moulding')
    for cx in np.arange(-1.58,1.61,.26):cb(b,cx-.067,cx+.067,-.235,-.10,6.156,6.25,RED,'Brick lookout beneath coping')
    bricks_uv(b)
