"""Map a repeating finish around each folded masonry face without stretching it."""
import hashlib
import json
import re
import struct
from pathlib import Path
import numpy as np
from photo_architecture import Builder

class CrownBuilder(Builder):
    def add(self, vertices, faces, material='limestone', label='detail'):
        super().add(vertices,faces,material,label)
        if not self.palette[material].get('texture'):
            return
        part=self.parts[-1]
        points=np.asarray(part['vertices'])
        xyz=[];uv=[];indices=[];lookup={}
        for face in part['triangles']:
            a,b,c=points[list(face)]
            normal=np.cross(b-a,c-a)
            normal=normal/np.linalg.norm(normal)
            if abs(normal[2])>.9:
                tangent=np.array([1.,0.,0.]);up=np.array([0.,1.,0.])
            else:
                tangent=np.array([-normal[1],normal[0],0.]);tangent/=np.linalg.norm(tangent)
                up=np.cross(normal,tangent)
            axes=tuple(np.round((*tangent,*up),6))
            tri=[]
            for idx in face:
                key=idx,axes
                if key not in lookup:
                    lookup[key]=len(xyz)
                    xyz.append(points[idx].tolist())
                    uv.append([float(points[idx]@tangent)*.78,float(points[idx]@up)*.78])
                tri.append(lookup[key])
            indices.append(tuple(tri))
        part.update(vertices=xyz,triangles=indices,texcoords=uv)

    def save(self,path,metadata=None):
        path=Path(path)
        report=super().save(path,metadata)
        with path.open('r+b') as out:
            out.seek(12)
            size,kind=struct.unpack('<II',out.read(8))
            if kind!=0x4e4f534a:raise ValueError('Missing glTF JSON')
            buf,count=re.subn(rb'("wrap[ST]"\s*:\s*)33071',rb'\g<1>10497',out.read(size))
            if count!=2 or len(buf)!=size:raise ValueError('Unexpected sampler')
            out.seek(20);out.write(buf)
        report['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        path.with_suffix('.geometry.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        return report
