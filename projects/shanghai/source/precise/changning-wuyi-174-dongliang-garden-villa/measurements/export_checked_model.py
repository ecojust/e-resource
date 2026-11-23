"""Export either level of detail after checking every solid, including UV seams."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from build_model import META, PALETTE, VillaBuilder, add_building


def paired_edges(tri):
    edges=np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]])
    radix=int(edges.max())+1
    forward=np.sort(edges[:,0]*radix+edges[:,1])
    reverse=np.sort(edges[:,1]*radix+edges[:,0])
    return np.all(forward[1:]!=forward[:-1]) and np.array_equal(forward,reverse)


def export(role,out):
    builder=VillaBuilder(PALETTE)
    add_building(builder,role=='lod')
    out.mkdir(exist_ok=True,parents=True)
    edge_modes=Counter()
    failures=[]
    total=0
    minimum=float('inf')
    for part in builder.parts:
        points=np.asarray(part['vertices'])
        indices=np.asarray(part['triangles'])
        faces=points[indices]-points[indices[0,0]]
        volume=float(np.einsum('ij,ij->i',faces[:,0],np.cross(faces[:,1],faces[:,2])).sum()/6)
        mode='indexed'
        if not paired_edges(indices):
            _,merged=np.unique(points.round(7),axis=0,return_inverse=True)
            mode='UV seams' if paired_edges(merged[indices]) else 'open'
        if mode=='open' or volume<=1e-13 or len(part['label'].encode())>63:
            failures.append(dict(label=part['label'],mode=mode,volume_m3=volume))
        edge_modes[mode]+=1
        minimum=min(minimum,volume)
        total+=len(indices)
    report=dict(role=role,parts=len(builder.parts),groups=len({p['label']for p in builder.parts}),triangles=total,
                minimum_signed_volume_m3=minimum,edge_modes=edge_modes,failures=failures)
    (out/(role+'-closure.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    if failures:raise ValueError(failures[:10])
    dest=out/(role+'-source.glb')
    stats=builder.save(dest,META)
    assert stats['triangles']==total
    print(role,total,stats['parts'],stats['bytes'],stats['sha256'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('role',choices=('full','lod'))
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    export(args.role,args.out)
