"""Keep the photographed wall coordinates and give the masonry edges their own UV faces."""
import numpy as np
from garden_bay import BRICK

def map_masonry_returns(builder):
    for part in builder.parts:
        if part['material']!=BRICK:
            continue
        xyz=np.asarray(part['vertices'],dtype=float)
        uv=np.asarray(part['texcoords'],dtype=float)
        triangles=np.asarray(part['triangles'],dtype=int)
        points=[];coords=[];indices=[]
        for face in triangles:
            f=xyz[face]
            t=uv[face].copy()
            if abs(np.linalg.det(t[1:]-t[0]))<1.e-10:
                normal=np.cross(f[1]-f[0],f[2]-f[0])
                if abs(normal[2])>np.linalg.norm(normal[:2]):
                    t=np.column_stack((f[:,0]/3.06,1.-f[:,1]/7.58))
                else:
                    horizontal=np.array([-normal[1],normal[0]])
                    horizontal/=np.linalg.norm(horizontal)
                    t=np.column_stack((f[:,:2]@horizontal/3.06,1.-f[:,2]/7.58))
            first=len(points)
            points.extend(f.tolist());coords.extend(t.tolist())
            indices.append((first,first+1,first+2))
        part.update(vertices=points,triangles=indices,texcoords=coords)
