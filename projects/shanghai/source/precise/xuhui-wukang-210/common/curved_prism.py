"""Curved-shell helper copied unchanged from published129 build_model.py (CC BY-SA4.0)."""
import math
import numpy as np
from shapely import constrained_delaunay_triangles, set_precision
from shapely.geometry import box
from shapely.geometry.polygon import orient
from photo_architecture import pieces

def curved_prism(builder, polygon, low, high, mapper, material, label, step=.12):
    """Continuous bent shell: band skins, shared boundary reveals, no internal caps."""
    verts=[];faces=[];lookup={}
    def index(x,z,d):
        key=(round(float(x),8),round(float(z),8),round(float(d),8))
        if key not in lookup:
            lookup[key]=len(verts);verts.append(mapper(*key))
        return lookup[key]
    normalized=set_precision(polygon,1e-8)
    assert normalized.symmetric_difference(polygon).area<1e-6
    for poly in pieces(normalized):
        x0,z0,x1,z1=poly.bounds
        regular=np.linspace(x0,x1,max(1,math.ceil((x1-x0)/step))+1)
        # Include all hole corner abscissae so both skins and jambs share cuts.
        corners=sorted(set(round(float(q[0]),8) for ring in [poly.exterior,*poly.interiors] for q in ring.coords))
        cuts=sorted(set(corners+[round(float(v),8) for v in regular if min(abs(v-x) for x in corners)>1e-7]))
        for a,b in zip(cuts,cuts[1:]):
            region=poly.intersection(box(a,z0-1,b,z1+1))
            for piece in pieces(region):
                for tri in constrained_delaunay_triangles(piece).geoms:
                    pts=list(orient(tri,1).exterior.coords)[:3]
                    faces.append(tuple(index(x,z,high) for x,z in pts));faces.append(tuple(index(x,z,low) for x,z in reversed(pts)))
        for ring in [poly.exterior,*poly.interiors]:
            coords=list(ring.coords)
            for a,b in zip(coords,coords[1:]):
                ts=[0.,1.]
                if abs(b[0]-a[0])>1e-12:
                    ts += [(x-a[0])/(b[0]-a[0]) for x in cuts if min(a[0],b[0])<x<max(a[0],b[0])]
                ts=sorted(set(ts))
                for lo,hi in zip(ts,ts[1:]):
                    p=np.asarray(a)+(np.asarray(b)-a)*lo;q=np.asarray(a)+(np.asarray(b)-a)*hi
                    faces.append((index(*p,low),index(*q,low),index(*q,high),index(*p,high)))
    builder.add(verts,faces,material,label)

