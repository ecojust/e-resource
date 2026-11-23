"""Rebuild each delivered level and verify oriented closed components and the actual GLB."""
from collections import Counter
from pathlib import Path
import argparse
import json
import sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from build_model import Builder,PALETTE,META,add_building

def paired_edges(tri):
    edges=np.concatenate((tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]))
    base=int(edges.max())+1
    forward=np.sort(edges[:,0]*base+edges[:,1]);backward=np.sort(edges[:,1]*base+edges[:,0])
    return bool(np.array_equal(forward,backward) and np.all(np.diff(forward)>0))

def rebuild(lod,out):
    b=Builder(PALETTE)
    add_building(b,lod)
    checks=Counter()
    failures=[]
    volumes=[]
    for part in b.parts:
        pos=np.asarray(part['vertices']);idx=np.asarray(part['triangles'])
        tri=pos[idx]-pos[idx[0,0]]
        vol=np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2])).sum()/6
        volumes.append(float(vol))
        scheme='indexed'
        if not paired_edges(idx):
            _,inverse=np.unique(np.round(pos,7),axis=0,return_inverse=True)
            scheme='seam weld' if paired_edges(inverse[idx]) else 'open'
        checks[scheme]+=1
        if scheme=='open' or vol<1e-12:
            failures.append({'component':part['label'],'material':part['material'],'volume':float(vol),'edges':scheme})
    role='lod' if lod else 'full'
    file=out/(role+'-source.glb')
    stats=b.save(file,META)
    report={'role':role,'sha256':stats['sha256'],'bytes':file.stat().st_size,'triangles':stats['triangles'],'components':len(b.parts),'groups':len({v['label'] for v in b.parts}),'checks':checks,'minimum_volume_m3':min(volumes),'failures':failures}
    (out/(role+'-closure.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    if failures:raise ValueError(failures[:8])
    print(role,report['components'],report['triangles'],report['sha256'],flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('out',type=Path)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    for lod in [False,True]:rebuild(lod,args.out)
