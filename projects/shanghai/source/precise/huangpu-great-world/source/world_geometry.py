"""Closed geometry utilities for the Great World exterior, ENU metres.

The sampled rectangular opening shell adapts the aviation building's generic
surface-grid method. Great World plans, heights, ornaments and facade rhythms
are authored separately in build_model.py.
"""
import math
import numpy as np
from shapely.geometry import Polygon, Point, LineString, box
from shapely.geometry.polygon import orient
from common.photo_architecture import Facade, opening


def perimeter_mapper(polygon):
    poly = orient(polygon, sign=1.)
    xy = np.array(poly.exterior.coords[:-1], float)
    edges = np.roll(xy, -1, axis=0)-xy
    lengths = np.linalg.norm(edges, axis=1)
    tangents = edges/lengths[:, None]
    normals = np.stack([tangents[:, 1], -tangents[:, 0]], axis=1)
    offsets = np.array([(normals[j-1]+normals[j])/(1+np.dot(normals[j-1], normals[j])) for j in range(len(xy))])
    starts = np.r_[0, np.cumsum(lengths)]
    total = starts[-1]
    def mapper(u, z, d=0):
        u = float(u) % total
        i = min(len(lengths)-1, int(np.searchsorted(starts, u, side='right')-1))
        f = (u-starts[i])/lengths[i]
        j = (i+1) % len(xy)
        p = xy[i]*(1-f)+xy[j]*f+d*(offsets[i]*(1-f)+offsets[j]*f)
        return np.array([p[0], p[1], z])
    return mapper, starts, LineString(poly.exterior.coords)


def rectangular_shell(builder, mapper, us, zs, holes, back=-.4, material='warm stone', label='perimeter wall', periodic=False):
    us = sorted(set(round(float(v), 7) for v in us)); zs = sorted(set(round(float(v), 7) for v in zs))
    um = (np.array(us[:-1])+us[1:])/2; zm = (np.array(zs[:-1])+zs[1:])/2
    valid = np.ones((len(um), len(zm)), bool)
    for hole in holes:
        a,b,c,d = hole.bounds
        valid[(um>a)&(um<c), :] &= ~((zm>b)&(zm<d))[None, :]
    vertices=[]; faces=[]; indices={}
    def ix(i,j,depth):
        k=(0 if periodic and i==len(us)-1 else i, j, depth)
        if k not in indices:
            indices[k]=len(vertices); vertices.append(mapper(us[k[0]],zs[j],depth))
        return indices[k]
    def exists(i,j):
        if periodic:i%=len(us)-1
        return 0<=i<len(us)-1 and 0<=j<len(zs)-1 and valid[i,j]
    for i in range(len(us)-1):
        for j in range(len(zs)-1):
            if not valid[i,j]:continue
            points=[(i,j),(i+1,j),(i+1,j+1),(i,j+1)]
            faces.append(tuple(ix(a,b,0) for a,b in points)); faces.append(tuple(ix(a,b,back) for a,b in reversed(points)))
            for k,neighbor in enumerate([(i,j-1),(i+1,j),(i,j+1),(i-1,j)]):
                if exists(*neighbor):continue
                a,b=points[k];c,d=points[(k+1)%4]
                faces.append((ix(a,b,back),ix(c,d,back),ix(c,d,0),ix(a,b,0)))
    builder.add(vertices,faces,material,label)


def regular_polygon(center, radius, sides=6, angle=math.pi/6):
    x,y=center
    return Polygon([(x+radius*math.cos(angle+j*math.tau/sides),y+radius*math.sin(angle+j*math.tau/sides)) for j in range(sides)])


def band(builder, polygon, z, height, projection=.2, depth=.25, material='pale dressed stone', label='cornice', exclusion=None):
    ring=polygon.buffer(projection,join_style=2).difference(polygon.buffer(-depth,join_style=2))
    if exclusion is not None:ring=ring.difference(exclusion)
    builder.plan_prism(ring,z,z+height,material,label)


def stone_column(builder, center, bottom, top, radius=.35, detail=True, label='column'):
    h=top-bottom
    p=[(bottom,radius*1.28),(bottom+.08,radius*1.28),(bottom+.16,radius*1.06),(bottom+.25,radius*.94),(top-.25,radius*.84),(top-.19,radius*1.10),(top-.08,radius*1.28),(top,radius*1.28)]
    if h<1.0:
        p=[(bottom,radius*1.25),(bottom+h*.2,radius*.85),(bottom+h*.7,radius*.68),(top,radius*1.16)]
    builder.lathe(center,p,'pale dressed stone',16 if detail else 8,label)
    if detail and h>2:
        # Simple volute outline, not a claim of exact Corinthian foliage.
        x,y=center
        for a in [0,math.pi/2,math.pi,3*math.pi/2]:
            t=np.linspace(0,math.tau*1.15,22);r=radius*.24*(1-t/(math.tau*1.3))
            pts=[(x+(radius*1.10+rr*math.cos(v))*math.cos(a),y+(radius*1.10+rr*math.cos(v))*math.sin(a),top-.20+rr*math.sin(v)) for v,rr in zip(t,r)]
            builder.tube(pts,.025,'pale dressed stone',5,label+' simplified volute')


def balustrade(builder, a, b, z, detail=True, outward=.18, label='stone balustrade'):
    f=Facade(builder,a,b,label)
    if f.length<.5:return
    f.box(0,z+.12,f.length,.16,.30,outward,'pale dressed stone','lower rail')
    f.box(0,z+.94,f.length,.14,.36,outward,'pale dressed stone','upper rail')
    count=max(2,round(f.length/(.57 if detail else 1.0)))
    for u in np.linspace(-f.length/2+.15,f.length/2-.15,count):
        c=f.point(u,0,outward)
        profile=[(z+.2,.095),(z+.28,.13),(z+.36,.075),(z+.70,.075),(z+.82,.12),(z+.87,.10)] if detail else [(z+.2,.11),(z+.45,.07),(z+.87,.11)]
        builder.lathe(c[:2],profile,'pale dressed stone',6 if detail else 4,label+' vase baluster')


def pediment(facade, u, top, width, style, detail=True):
    if style=='triangle':
        p=Polygon([(u-width*.64,top+.12),(u+width*.64,top+.12),(u,top+.65)])
        inner=Polygon([(u-width*.45,top+.22),(u+width*.45,top+.22),(u,top+.48)])
        facade.prism(p.difference(inner),.02,.19,'pale dressed stone','triangular window pediment')
    elif style=='segment':
        p=opening(u,top+.06,width*1.23,.52,.40,16 if detail else 8)
        inner=opening(u,top+.08,width*.91,.32,.25,16 if detail else 8)
        facade.prism(p.difference(inner),.02,.19,'pale dressed stone','segmental window pediment')
    else:
        facade.box(u,top+.17,width*1.23,.18,.22,.10,'pale dressed stone','flat window hood')
    if detail:
        facade.prism(Point(u,top+.62 if style!='flat' else top+.35).buffer(.12,resolution=6),.02,.18,'pale dressed stone','simplified centre ornament')
