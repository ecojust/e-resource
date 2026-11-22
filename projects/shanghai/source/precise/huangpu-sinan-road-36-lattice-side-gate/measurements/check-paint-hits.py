"""Verify the photographed enamel and its address strokes on the front-facing mesh."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys

import numpy as np


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for field in ['project','source','points','mesh','output']:
        parser.add_argument('--'+field,type=Path,required=True)
    args=parser.parse_args()
    sys.path.insert(0,str(args.source))
    from photo_plane import original_to_crop,position
    suite=runpy.run_path(args.project/'data/audit/postal-office-v1/independent-glb-review-helpers.py')
    triangles,ids,names,identity=suite['load_triangles'](args.mesh)
    looks=suite['material_appearance'](args.mesh)['materials']
    normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
    always=np.array([looks[name]['doubleSided']for name in names])[ids]
    reference=json.loads(args.points.read_bytes())
    rows=[]
    for sample in reference['points']:
        u,v=original_to_crop(*sample['original_upright'])
        eye=position(u,v,-2.2)
        ray=position(u,v,1.2)-eye
        ray/=np.linalg.norm(ray)
        legal=np.flatnonzero(always | ((normals@ray)<-1e-12))
        i,distance,impact=suite['first_hit'](triangles[legal],eye,ray)
        material=names[ids[legal[i]]] if np.isfinite(distance) else None
        expected=sample['expected']
        matched=(material in ('Light address paint','Weathered paint highlights') if expected=='paint' else material=='Deep green enamel')
        rows.append(dict(group=sample['group'],original=sample['original_upright'],rectified=sample['pixel'],expected=expected,
                         observed=material,depth_m=round(float(impact[1]),6) if material else None,passed=matched))
    result=dict(mesh_sha256=identity['sha256'],points_sha256=hashlib.sha256(args.points.read_bytes()).hexdigest(),
                count=len(rows),passed_count=sum(r['passed']for r in rows),rays=rows)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['passed_count'],'/',result['count'],[(r['group'],r['rectified'],r['observed'])for r in rows if not r['passed']])
if __name__=='__main__':
    main()
