"""Generic closed periodic wall shell reused from Great World, not its building geometry."""
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

