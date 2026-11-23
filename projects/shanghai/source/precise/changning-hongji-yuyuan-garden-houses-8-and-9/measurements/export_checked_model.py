"""Export a complete courtyard after validating the orientation and closure of every editable part."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from build_model import GardenBuilder, META, PALETTE, add_building


def paired_edges(tris):
    edges=np.concatenate([tris[:,[0,1]],tris[:,[1,2]],tris[:,[2,0]]])
    width=edges.max()+1
    outward=np.sort(edges[:,0]*width+edges[:,1])
    inward=np.sort(edges[:,1]*width+edges[:,0])
    return np.all(outward[1:]!=outward[:-1]) and np.array_equal(outward,inward)


def export(lod,out):
    role='lod' if lod else 'full'
    b=GardenBuilder(PALETTE);add_building(b,lod)
    modes=Counter();by_group=Counter();errors=[]
    minimum=float('inf');triangles=0
    for part in b.parts:
        label=part['label'];verts=np.asarray(part['vertices']);faces=np.asarray(part['triangles'])
        t=verts[faces]-verts[faces[0,0]]
        vol=float(np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6)
        mode='indexed'
        if not paired_edges(faces):
            _,inv=np.unique(verts.round(7),axis=0,return_inverse=True)
            mode='UV seams' if paired_edges(inv[faces]) else 'open'
        if mode=='open' or vol<=1e-13 or len(label.encode('utf-8'))>63:
            errors.append({'label':label,'volume_m3':vol,'edge_mode':mode,'name_bytes':len(label.encode())})
        minimum=min(vol,minimum);modes[mode]+=1;triangles+=len(faces)
        by_group[label.split(' | ',1)[0]]+=1
    report={'role':role,'parts':len(b.parts),'groups':len({p['label'] for p in b.parts}),
            'triangles':triangles,'owner_part_counts':by_group,'edge_modes':modes,
            'minimum_signed_volume_m3':minimum,'failures':errors}
    out.mkdir(exist_ok=True,parents=True)
    (out/(role+'-closure.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    if errors or set(by_group)!={'8','9','Garden'}:
        raise ValueError(f'Invalid parts or group membership: {errors[:10]}, {dict(by_group)}')
    dest=out/(role+'-source.glb')
    stats=b.save(dest,META)
    if stats['triangles']!=triangles:raise ValueError('Exported triangle count changed')
    print(role,triangles,report['parts'],stats['bytes'],stats['sha256'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('role',choices=('full','lod'));parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args()
    export(args.role=='lod',args.out)
