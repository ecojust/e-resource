"""Metric façade UVs and roof texture coordinates aligned with each pitched tile course."""
import numpy as np
from crown_builder import CrownBuilder
from changzhi_finish import TILE

class StreetBuilder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        super().add(vertices,faces,material,label)
        if material!=TILE:return
        part=self.parts[-1];v=np.asarray(part['vertices'])
        positions=[];uv=[];triangles=[];seen={}
        for face in part['triangles']:
            a,b,c=v[list(face)];n=np.cross(b-a,c-a);n/=np.linalg.norm(n)
            tangent=np.array([-n[1],n[0],0.]);length=np.linalg.norm(tangent)
            if length<1e-6:tangent=np.array([1.,0.,0.])
            else:tangent/=length
            rise=np.cross(n,tangent);axes=tuple(np.round([*tangent,*rise],6))
            indices=[]
            for j in face:
                key=j,axes
                if key not in seen:
                    seen[key]=len(positions);positions.append(v[j].tolist())
                    uv.append([float(v[j]@tangent)/2.4,float(v[j]@rise)/2.56])
                indices.append(seen[key])
            triangles.append(tuple(indices))
        part.update(vertices=positions,texcoords=uv,triangles=triangles)
