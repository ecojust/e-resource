"""Check the editable crown sashes, glass cells, awning fabric and front hem."""
from collections import Counter
import argparse
import json
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'hongkou-general-post-office/source/common')]
from photo_architecture import Builder
from crown_window_sashes import PALETTE,GLASS,SHADED_GLASS,add_crown_windows,add_crown_brick_panels


def verify(level,openings,panels,glb=None):
    b=Builder(PALETTE)
    add_crown_windows(b,level,openings)
    add_crown_brick_panels(b,level,panels)
    volumes=[]
    counts={}
    names=[]
    for part in b.parts:
        v=np.array(part['vertices'])
        f=np.array(part['triangles'])
        name=part['label'];names.append(name)
        edge=Counter(tuple(sorted((a,b))) for t in f for a,b in zip(t,np.roll(t,-1)))
        assert set(edge.values())=={2},name
        is_glass=part['material'] in (GLASS,SHADED_GLASS)
        components=len(v)//8 if is_glass else 1
        for island in np.split(f,components):
            tri=v[island];tri=tri-tri[0,0]
            vol=np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2])).sum()/6
            assert vol>0,(name,vol)
            volumes.append(vol)
        if is_glass:
            counts[name]=components
    assert len(set(names))==len(names)==32
    assert list(counts.values())==([5,5,24,24] if level=='full' else [1,1,1,1])
    if glb:
        b.save(glb)
    return dict(lod=level,models=len(names),closed_solids=len(volumes),glazing_by_window=counts,
                smallest_volume_display_units_cubed=float(min(volumes)),triangles=sum(len(p['triangles'])for p in b.parts))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('schedule',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--export',action='store_true')
    args=parser.parse_args()
    data=json.loads(args.schedule.read_bytes())
    openings=data['openings']
    panels=data['panels']
    args.output.mkdir(exist_ok=True,parents=True)
    result=[verify(level,openings,panels,args.output/f'crown-sashes-{level}.glb' if args.export else None)for level in ('full','lod')]
    (args.output/'crown-sash-solids.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result)
