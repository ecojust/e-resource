"""Masonry, shafts and Gothic openings used at the Cathedral's garden end and flanks."""
from math import acos,atan2,cos,pi,sin
import numpy as np
from shapely.geometry import Polygon,box,Point
from shapely.ops import unary_union

RED='red face brick'
DARK='dark arch brick'
PALE='granite trim'
GLASS='church glazing'
FRAME='lead and iron'
BASE='granite shaft'


def arch(u,bottom,w,h,rise,round_head,lod):
    """Shape and ordered intrados. For pointed arches two circular arcs meet."""
    a=w/2; spring=bottom+h-rise
    count=10 if lod else 20
    if round_head:
        path=[(u+a*cos(t),spring+rise*sin(t)) for t in np.linspace(pi,0,count*2+1)]
    else:
        center=(rise*rise-a*a)/(2*a)
        radius=a+center
        theta=acos(-center/radius)
        left=[(u+center+radius*cos(t),spring+radius*sin(t)) for t in np.linspace(pi,theta,count+1)]
        path=left+[(2*u-x,z) for x,z in reversed(left[:-1])]
    return Polygon([(u-a,bottom),(u+a,bottom),*reversed(path)]),path,spring


def voussoirs(f,curve,lod,thickness=.17,front=.12):
    """Extruded alternating brick segments normal to the measured curve."""
    coords=np.asarray(curve)
    step=2 if lod else 2
    for j in range(0,len(coords)-1,step):
        k=min(j+step,len(coords)-1)
        p=coords[j:k+1]
        tangents=np.gradient(coords,axis=0)[j:k+1]
        normals=np.column_stack((-tangents[:,1],tangents[:,0]))
        normals/=np.linalg.norm(normals,axis=1)[:,None]
        polygon=Polygon(np.vstack((p,(p+thickness*normals)[::-1])))
        f.prism(polygon,-.028,front,DARK if (j//step)%2==0 else RED,'banded arch bricks')


def light(f,u,z,w,h,lod,*,round_head=False,rise=None,columns=2):
    rise=rise or w*.70
    hole,curve,_=arch(u,z,w,h,rise,round_head,lod)
    f.prism(hole.buffer(.009,join_style=2),-.33,-.315,GLASS,'recessed window glass')
    pane=hole.buffer(-.055,join_style=2)
    bars=[]
    for k in range(1,columns):
        x=u-w/2+w*k/columns;bars.append(box(x-.023,z,x+.023,z+h))
    for k in range(1,2 if lod else 4):
        level=z+h*k/(2 if lod else 4)
        bars.append(box(u-w/2,level-.022,u+w/2,level+.022))
    f.prism(hole.buffer(-.014,join_style=2).difference(pane.difference(unary_union(bars))),
            -.29,-.235,FRAME,'iron sash')
    voussoirs(f,curve,lod,.11 if w<1.3 else .19,.08)
    f.box(u,z-.05,w+.16,.105,.22,.025,PALE,'slender window ledge')
    return hole


def shaft(f,u,height,lod,radius=.30):
    profile=[(.0,radius*1.66),(.19,radius*1.66),(.22,radius*1.38),(.38,radius*1.22),
             (.45,radius), (height-.37,radius*.87),(height-.31,radius*1.11),
             (height-.19,radius*1.37),(height-.11,radius*1.48),(height,radius*1.50)]
    f.builder.lathe(f.point(u,0,-.15)[:2],profile,BASE,10 if lod else 18,f.label+'/granite columns')
    f.box(u,height-.015,radius*3.20,.15,.71,-.14,PALE,'impost block')


def colonnade(f,widths,lod,*,top,spring,round_flags=(),end_piers=.55,shaft_radius=.29):
    """Open arcade with freestanding shafts beneath the brick spandrel."""
    available=f.length-2*end_piers;scale=available/sum(widths);u=-available/2
    holes=[];positions=[u]
    for j,w in enumerate(widths):
        bay=w*scale;cw=bay-2*shaft_radius*.97;mid=u+bay/2
        rounded=j in round_flags;rise=cw*(.50 if rounded else .62)
        hole,curve,_=arch(mid,spring-.025,cw,rise+.025,rise,rounded,lod)
        holes.append(hole);voussoirs(f,curve,lod,.19 if bay>2.4 else .14,.118)
        positions.append(u+bay);u+=bay
    f.wall(spring,top,holes,.63,RED)
    for u in positions[1:-1]:shaft(f,u,spring,lod,shaft_radius)
    for u in (-f.length/2+(end_piers+shaft_radius)/2,f.length/2-(end_piers+shaft_radius)/2):
        f.box(u,spring/2,end_piers+shaft_radius,spring,.70,-.14,RED,'square corner pier')
        f.box(u,.22,end_piers+shaft_radius+.16,.44,.86,-.14,BASE,'corner pier plinth')
        f.box(u,spring-.06,end_piers+shaft_radius+.16,.18,.85,-.14,PALE,'pier impost')
    f.beam(top-.055,.12,.12,PALE,width=f.length,label='coping')
