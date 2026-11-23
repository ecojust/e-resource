"""Lead cames follow two measured line families and remain open between diamonds."""
import math
import numpy as np
from shapely.geometry import LineString
from shapely.ops import unary_union
def leaded_field(builder,opening,face,material,period,mapper,lod):
    du,dz=period;x0,z0,x1,z1=opening.bounds;cut=opening.buffer(-.010)
    strips=[]
    # The horizontal projected spacing is du and the vertical spacing dz.
    for sign in [-1,1]:
        m=sign*dz/du
        lo=min(z-m*x for x in [x0,x1] for z in [z0,z1])
        hi=max(z-m*x for x in [x0,x1] for z in [z0,z1])
        for i in range(math.floor(lo/dz),math.ceil(hi/dz)+1):
            b=i*dz;line=LineString([(x0-.10,b+m*(x0-.10)),(x1+.10,b+m*(x1+.10))])
            strip=line.buffer(.0063 if lod else .0073,cap_style='flat').intersection(cut)
            if strip.is_empty or strip.area<=1e-7:continue
            if lod:
                # The far representation keeps the observed angular pitch. Opposing
                # lead runs sit on adjacent thin depth planes at their crossings.
                depth=-face-.138+(sign+1)*.0031
                builder.prism(strip,depth,depth+.0058,mapper,material,f'seven lights / lead direction {sign} strip {i}')
            else:strips.append(strip)
    # At a crossing only the exposed metal carries one skin. The two systems are
    # joined into a single watertight casting rather than doubled across one another.
    if lod:return
    mat=unary_union(strips)
    builder.prism(mat,-face-.140,-face-.127,mapper,material,'seven lights / continuous diamond lead lattice')
def cusp_ring(x,z,w,h,lod):
    outer=[];inner=[]
    for t in np.linspace(0,math.tau,28 if lod else 64,endpoint=False):
        ct,st=math.cos(t),math.sin(t)
        outer.append((x+w*ct,z+h*st*(1-.16*abs(ct))))
        scallop=.81-.075*math.cos(4*t)
        inner.append((x+w*scallop*ct,z+h*scallop*st*(1-.16*abs(ct))))
    from shapely.geometry import Polygon
    return Polygon(outer,[inner])
