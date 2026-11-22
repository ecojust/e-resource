"""Export repeatable procedural materials with a consistent UV projection on all six faces."""
import hashlib,json,re,struct
from pathlib import Path
import numpy as np
from photo_architecture import Builder

class RiverBuilder(Builder):
    def add(self, vertices, faces, material='limestone', label='detail'):
        super().add(vertices,faces,material,label)
        if not self.palette[material].get('texture') or 'washed aggregate' not in material:
            return
        part=self.parts[-1]
        pts=np.asarray(part['vertices'],float)
        # World-aligned triplanar UVs get a separate seam for each projection plane.
        out=[];uv=[];tris=[];lookup={}
        for tri in part['triangles']:
            a,c,d=pts[list(tri)]
            normal=np.cross(c-a,d-a)
            axis=int(np.argmax(np.abs(normal)))
            axes=((1,2),(0,2),(0,1))[axis]
            group=[]
            for previous in tri:
                k=(previous,axis)
                if k not in lookup:
                    lookup[k]=len(out);out.append(pts[previous].tolist())
                    uv.append((pts[previous,axes[0]]*.82,pts[previous,axes[1]]*.82))
                group.append(lookup[k])
            tris.append(tuple(group))
        part.update(vertices=out,triangles=tris,texcoords=uv)

    def save(self,path,metadata=None):
        path=Path(path)
        report=super().save(path,metadata)
        with path.open('r+b') as f:
            f.seek(12)
            size,kind=struct.unpack('<II',f.read(8))
            if kind!=0x4e4f534a:raise ValueError('Missing GLB JSON chunk')
            data=f.read(size)
            patched,n=re.subn(rb'("wrap[ST]"\s*:\s*)33071',rb'\g<1>10497',data)
            if len(patched)!=size or n!=2:raise ValueError('Unexpected texture repeat configuration')
            f.seek(20);f.write(patched)
        report['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        path.with_suffix('.geometry.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        return report
