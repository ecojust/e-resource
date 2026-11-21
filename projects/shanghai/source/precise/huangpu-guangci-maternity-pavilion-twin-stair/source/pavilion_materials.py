"""Stone, countersunk timber and brick finishes of the former maternity building."""
from pathlib import Path
import numpy as np

BRICK='Guangci running-bond facing'
CREAM='Limestone coloured render'
EDGE='Pale moulded cap'
CUT='Shade in recessed mouldings'
WOOD='Red brown painted frames'
GLASS='Blue grey courtyard glass'
REFLECT='Grey green casement'
DARK='Dark panelled timber'
TILE='Sienna roof tiles'
ROOF_SHADE='Roof tile underlap'
TIMBER='Stained projecting timber brackets'
BLACK='Enamelled dark metal'
MOSAIC='Moss grey ceramic tesserae'
MOSAIC_DARK='Charcoal patterned tesserae'
PLINTH='Cut stone plinth'
BRICK_EDGE='Radial lintel brick'
FLOOR='Warm grey cement'
FONT=Path(__file__).with_name('lettering')/'GuangciCourtyardRelief.otf'


def colour(rgb,rough=.8,metal=0):
    rgb=[v/255 for v in rgb]
    linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
    return dict(color=linear,roughness=rough,metallic=metal)


PALETTE={
    BRICK:dict(color=[1.,1.,1.],roughness=.9,texture=str(Path(__file__).with_name('brick-facing.png'))),
    CREAM:colour((202,196,174)),EDGE:colour((220,213,191)),CUT:colour((162,154,135)),
    WOOD:colour((81,54,48),.62),GLASS:colour((90,112,114),.31,.15),REFLECT:colour((109,124,118),.32,.16),
    DARK:colour((65,48,43),.76),TILE:colour((151,94,73)),ROOF_SHADE:colour((109,73,60)),
    TIMBER:colour((81,69,58)),BLACK:colour((65,65,59),.60,.22),
    MOSAIC:colour((127,137,122)),MOSAIC_DARK:colour((99,106,96)),PLINTH:colour((176,171,154)),
    BRICK_EDGE:colour((159,91,67)),FLOOR:colour((157,151,137))
}


def brick_coordinates(x,y,z,axis):
    # Vertical walls use level horizontal courses; top surfaces use their
    # plan coordinates. The convention follows the dominant face normal.
    if np.ndim(axis)==0:
        return (y if axis==0 else x)/.948,(y if axis==2 else z)/.52
    return np.where(axis==0,y,x)/.948,np.where(axis==2,y,z)/.52


def add_brick_uvs(builder):
    for part in builder.parts:
        if part['material']!=BRICK:
            continue
        vertices=np.asarray(part['vertices'])
        triangles=np.asarray(part['triangles'])
        xyz=vertices[triangles]
        normals=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0])
        axes=np.argmax(np.abs(normals),axis=1)
        uv_vertices=[];uvs=[];faces=[];by_corner={}
        for tri,axis in zip(triangles,axes):
            new=[]
            for index in tri:
                key=(int(index),int(axis))
                if key not in by_corner:
                    by_corner[key]=len(uvs)
                    point=part['vertices'][index]
                    u,v=brick_coordinates(*point,axis)
                    uvs.append((float(u),1-float(v)))
                    uv_vertices.append(point)
                new.append(by_corner[key])
            faces.append(tuple(new))
        part.update(vertices=uv_vertices,triangles=faces,texcoords=uvs)
