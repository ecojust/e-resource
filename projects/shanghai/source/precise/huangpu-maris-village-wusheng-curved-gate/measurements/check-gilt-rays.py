"""Check non-coplanar first intersections of the gate lettering in the registered 2021 view."""
import argparse
import json
from pathlib import Path
import runpy
import sys

import numpy as np

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for k in ('project','source','mesh','points','out'):ap.add_argument('--'+k,required=True,type=Path)
    a=ap.parse_args();sys.path.insert(0,str(a.source))
    from photo_plane import position
    tools=runpy.run_path(a.project/'data/audit/postal-office-v1/independent-glb-review-helpers.py')
    triangles,ids,names,info=tools['load_triangles'](a.mesh)
    appearance=tools['material_appearance'](a.mesh)['materials']
    normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
    double=np.array([appearance[n]['doubleSided']for n in names])[ids]
    seen=[]
    for point in json.loads(a.points.read_bytes())['points']:
        u,v=point['detail_2021_px'];eye=position(u,v,-1.8);aim=position(u,v,.6);ray=aim-eye;ray/=np.linalg.norm(ray)
        potential=np.flatnonzero(double|((normals@ray)<-1.e-10))
        i,distance,xyz=tools['first_hit'](triangles[potential],eye,ray)
        tag=names[ids[potential[i]]] if np.isfinite(distance) else None
        expected=('Black painted sign disks',) if point['expected']=='black' else ('Raised gilt letters','Shadowed gilt edges')
        seen.append(dict(**point,observed=tag,passed=tag in expected))
    out=dict(mesh_sha256=info['sha256'],count=len(seen),passed_count=sum(item['passed']for item in seen),points=seen)
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(out['passed_count'],out['count'],[(r['letter'],r['expected'],r['observed'])for r in seen if not r['passed']])
if __name__=='__main__':main()
