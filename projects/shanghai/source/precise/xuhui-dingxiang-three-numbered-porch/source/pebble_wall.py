"""Periodically repeating yellow-grey river pebbles on the wall of the numbered entrance."""
from pathlib import Path
import numpy as np

STONE = 'Warm exposed river pebbles'
PERIOD = .38


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
    from PIL import Image,ImageDraw
    size=288
    rng=np.random.default_rng(8490372)
    base=np.zeros((size,size,3))+np.array([155.,148.,128.])
    base+=rng.normal(0,6,(size,size,1))
    im=Image.fromarray(np.uint8(base.clip(0,255)))
    brush=ImageDraw.Draw(im)
    palette=[(176,162,122),(172,167,143),(199,188,153),(142,135,110),(119,116,100),(192,190,174),(148,140,123)]
    for _ in range(3800):
        x,y=rng.integers(0,size,2);rx,ry=rng.integers(1,4,2)
        tone=palette[rng.integers(len(palette))]
        for dx in (-size,0,size):
            for dy in (-size,0,size):
                xx=x+dx;yy=y+dy
                if -rx<=xx<size+rx and -ry<=yy<size+ry:
                    brush.ellipse((xx-rx,yy-ry,xx+rx,yy+ry),fill=tone)
                    brush.point((xx,yy-ry),fill=tuple(min(255,c+19)for c in tone))
    im.save(Path(__file__).with_name('river-pebble-wall.png'),optimize=True)

if __name__=='__main__':
    create()
