"""Procedural roughcast and scale-preserving planar coordinates for the paired terraces."""
from pathlib import Path
import numpy as np

STONE = 'Green grey roughcast'
PERIOD = .42


def dominant_axis(normal):
    # At a 45-degree arch facet the float mesh and Blender can round in opposite directions.
    # Break geometric ties by X, Y, Z order on both sides of serialization.
    components = [abs(v) for v in normal]
    threshold = max(components) * (1 - 1e-5)
    return next(i for i, value in enumerate(components) if value >= threshold)


def uv(x, y, z, axis):
    return (y if axis == 0 else x) / PERIOD, (y if axis == 2 else z) / PERIOD


def texture_coordinates(builder):
    for part in builder.parts:
        if part['material'] != STONE:
            continue
        points, texcoords, triangles, lookup = [], [], [], {}
        for triangle in part['triangles']:
            a, b, c = (np.asarray(part['vertices'][i]) for i in triangle)
            axis = dominant_axis(np.cross(b-a,c-a))
            mapped=[]
            for index in triangle:
                key=(index,axis)
                if key not in lookup:
                    position=part['vertices'][index]
                    u,v=uv(*position,axis)
                    lookup[key]=len(points)
                    points.append(position)
                    texcoords.append((u,1-v))
                mapped.append(lookup[key])
            triangles.append(mapped)
        part.update(vertices=points,texcoords=texcoords,triangles=triangles)


def create():
    """Light lime wash over small pieces of aggregate, sampled onto an original repeating material."""
    from PIL import Image,ImageDraw
    size=192
    rng=np.random.default_rng(3001202)
    base=np.zeros((size,size,3))+[150.,152.,133.]
    base+=rng.normal(0.,6.,(size,size,1))
    result=Image.fromarray(np.uint8(base.clip(0,255)))
    draw=ImageDraw.Draw(result)
    for j in range(2700):
        x,y=rng.integers(0,size,2)
        rx=int(rng.integers(1,4)); ry=int(rng.integers(1,3))
        tone=int(rng.integers(-24,23))
        colour=tuple(int(c+tone)for c in (149,151,134))
        for dx in (-size,0,size):
            for dy in (-size,0,size):
                xx,yy=x+dx,y+dy
                if -rx<xx<size+rx and -ry<yy<size+ry:
                    draw.line([(xx-rx,yy-1),(xx,yy+ry),(xx+rx,yy+1)],fill=colour,width=1)
    result.save(Path(__file__).with_name('green-grey-roughcast.png'),optimize=True)


if __name__=='__main__':
    create()
