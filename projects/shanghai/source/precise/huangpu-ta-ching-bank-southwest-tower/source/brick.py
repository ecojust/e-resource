"""Meter-based running bond for the restored street brickwork."""
from pathlib import Path
import math
from random import Random


def wall_uv(x,y,z):
    a=2.66215;c=a*(math.sqrt(2)-1)
    points=[(-a-.5275*3.65,.84955*3.65),(-a,0),(-c,c-a),(c,c-a),(a,0),(a+.84201*3.65,.53946*3.65)]
    closest=float('inf');along=0.;offset=0.
    for (u,v),(m,n) in zip(points,points[1:]):
        dx=m-u;dy=n-v;length=math.hypot(dx,dy)
        t=max(0.,min(1.,((x-u)*dx+(y-v)*dy)/length**2))
        dist=math.hypot(x-u-t*dx,y-v-t*dy)
        if dist<closest:closest=dist;along=offset+t*length
        offset+=length
    return along/1.92,-z/.52

def generate(target):
    from PIL import Image
    rng=Random(1908050);im=Image.new('RGB',(256,64));px=im.load()
    colors={(row,col):rng.randint(-8,8)for row in range(8)for col in range(8)}
    for j in range(64):
        course=j//8
        for i in range(256):
            u=(i+16*(course%2))%256;v=j%8
            tone=colors[course,u//32]+rng.randint(-6,6)
            if v==0 or u%32==0:px[i,j]=(143+tone,113+tone,91+tone)
            else:px[i,j]=(149+tone,77+tone,55+tone)
    im.save(target,optimize=True)
if __name__=='__main__':generate(Path(__file__).with_name('bond.png'))
