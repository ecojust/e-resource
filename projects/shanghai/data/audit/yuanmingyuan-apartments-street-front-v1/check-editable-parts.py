"""Check individual closed parts and outward-facing geometry before UV duplication for export."""
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
SRC=HERE.parents[2]/'source/precise/huangpu-yuanmingyuan-apartments-street-front/source'
sys.path.insert(0,str(SRC))
from build_model import AggregateBuilder, PALETTE
from central_brickwork import add_central_brickwork
from east_facade import add_recessed_entrance,add_wings,add_side_loggias
from english_name import add_english_name
from street_entrance import add_entrance,add_metal_letters
from wing_casements import add_windows


def check(lod):
    b=AggregateBuilder(PALETTE)
    counts={}
    for action in [add_entrance,add_recessed_entrance,add_english_name,add_wings,add_windows,add_side_loggias,add_central_brickwork]:
        start=len(b.parts);action(b,lod);counts[action.__name__]=len(b.parts)-start
    add_metal_letters(b)
    bad=[];volumes=[];surfaces=[]
    for p in b.parts:
        v=np.asarray(p['vertices'],dtype=float)
        tri=v[np.asarray(p['triangles'])]-np.mean(v,axis=0)
        cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);area=np.linalg.norm(cross,axis=1)/2
        vol=float(np.sum(tri[:,0]*cross)/6)
        if np.min(area)<1e-12 or vol<=1e-12:bad.append(dict(label=p['label'],min_triangle_area=float(np.min(area)),volume=vol))
        volumes.append(vol);surfaces.append(float(area.sum()))
    return dict(passed=not bad,materials=len({p['material']for p in b.parts}),editable_labels=len({p['label']for p in b.parts}),parts=len(b.parts),group_parts=counts,
                minimum_signed_volume_m3=min(volumes),surface_area_sum_m2=sum(surfaces),signed_volume_sum_m3=sum(volumes),invalid=bad)


if __name__=='__main__':
    out=Path(sys.argv[1])
    results={name:check(lod)for name,lod in [('full',False),('lod',True)]}
    out.write_text(json.dumps(results,indent=2)+'\n')
    for name,r in results.items():print(name,r['parts'],r['passed'],r['invalid'][:5])
    sys.exit(int(any(not r['passed']for r in results.values())))
