"""Three tapered stair tiers as one exposed boundary shell, no stacked caps.

Widths are photo-informed estimates. Heights and front depths retain frozen v1.
The occupied orthogonal cells are used only to determine the union boundary;
no interior cell, layer or overlapping-box faces are emitted.
"""
import numpy as np

def add_north_steps(builder, northfront, revision):
    widths=revision['step_widths_bottom_to_top_m']
    fronts=revision['step_fronts_from_facade_m']
    heights=revision['step_riser_heights_m']
    xs=sorted(set([-w/2 for w in widths]+[w/2 for w in widths]))
    ys=[northfront+v for v in sorted(set([0.]+fronts))]
    zs=[0.]+list(np.cumsum(heights))
    occupied=set()
    for iz in range(len(zs)-1):
        for iy in range(len(ys)-1):
            for ix in range(len(xs)-1):
                xm=(xs[ix]+xs[ix+1])/2;ym=(ys[iy]+ys[iy+1])/2-northfront
                if abs(xm)<widths[iz]/2 and ym<fronts[iz]:occupied.add((ix,iy,iz))
    # Corner order: lower CCW ring then upper CCW ring.
    sides=[((-1,0,0),(0,4,7,3)),((1,0,0),(1,2,6,5)),
           ((0,-1,0),(0,1,5,4)),((0,1,0),(3,7,6,2)),
           ((0,0,-1),(0,3,2,1)),((0,0,1),(4,5,6,7))]
    vertices=[];faces=[];lookup={}
    def index(v):
        key=tuple(float(x) for x in v)
        if key not in lookup:lookup[key]=len(vertices);vertices.append(key)
        return lookup[key]
    for ix,iy,iz in sorted(occupied):
        x0,x1=xs[ix:ix+2];y0,y1=ys[iy:iy+2];z0,z1=zs[iz:iz+2]
        corners=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
                 (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
        for delta,face in sides:
            neighbor=(ix+delta[0],iy+delta[1],iz+delta[2])
            if neighbor not in occupied:faces.append(tuple(index(corners[k]) for k in face))
    builder.add(vertices,faces,'stone plinth','north-entry-single-stepped-solid')
