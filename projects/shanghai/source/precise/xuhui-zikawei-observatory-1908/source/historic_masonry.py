"""Original grey field brick with lime joints for the observatory's historical reconstruction."""
from pathlib import Path
import numpy as np
from PIL import Image

TEXTURE = Path(__file__).with_name('observatory-grey-brick.png')
MASONRY = 'Observatory grey brick'
WIDTH = 1.60
HEIGHT = .64


def create():
    rng = np.random.default_rng(19080391)
    field = np.zeros((256,640,3))
    for course in range(8):
        shift=40 if course%2 else 0
        for i in range(9):
            for x in ((i*80-shift)%640,):
                columns=(np.arange(80)+x)%640
                value=np.array([103,99,93])+rng.uniform(-11,11)+rng.normal(0,1.5,3)
                field[course*32:course*32+32,columns]=value
    yy,xx=np.indices(field.shape[:2])
    edge_x=(xx+((yy//32%2)*40))%80
    edge_y=yy%32
    mortar=(edge_x<3)|(edge_y<3)
    field[mortar]=[144,136,122]
    field[(edge_x==3)|(edge_y==3)]*=.84
    field+=rng.normal(0,4.,field.shape[:2])[:,:,None]
    Image.fromarray(np.clip(field,0,255).astype('uint8')).save(TEXTURE,optimize=True)


def map_bricks(builder):
    for part in builder.parts:
        if part['material'] != MASONRY:
            continue
        points=np.asarray(part['vertices'],dtype=float)
        if not len(points):continue
        # The underlying prism contains front, return and top faces together.
        # Assign UVs per corner so each visible return keeps a true metric bond.
        vertices=[];uvs=[];faces=[]
        for triangle in part['triangles']:
            face=points[np.asarray(triangle)]
            cross=np.cross(face[1]-face[0],face[2]-face[0])
            axis=int(np.argmax(np.abs(cross)))
            for x,y,z in face:
                u=y if axis==0 else x
                v=y if axis==2 else z
                vertices.append((float(x),float(y),float(z)))
                uvs.append((float(u/WIDTH),float(1-v/HEIGHT)))
            stop=len(vertices);faces.append((stop-3,stop-2,stop-1))
        part.update(vertices=vertices,triangles=faces,texcoords=uvs)


if __name__=='__main__':
    create()
