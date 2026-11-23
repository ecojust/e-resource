"""Rebuild a level and check closed oriented triangle shells by component."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from collections import Counter

import numpy as np

HERE=Path(__file__).absolute().parent
sys.path.insert(0,str(HERE.parent/'source'))
from build_model import build,META


def closed(indices):
    ends=np.concatenate([indices[:,[0,1]],indices[:,[1,2]],indices[:,[2,0]]])
    size=int(ends.max())+1
    ordered=np.sort(ends[:,0]*size+ends[:,1])
    reverse=np.sort(ends[:,1]*size+ends[:,0])
    return np.all(ordered[1:]!=ordered[:-1]) and np.array_equal(ordered,reverse)


def check(level,out):
    builder=build(level=='far');out.mkdir(exist_ok=True,parents=True)
    failures=[];modes=Counter();volumes=[];count=0
    for part in builder.parts:
        pos=np.asarray(part['vertices']);idx=np.asarray(part['triangles'])
        tri=pos[idx]-pos[idx[0,0]]
        volume=float(np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2])).sum()/6)
        mode='indexed edges'
        if not closed(idx):
            _,merged=np.unique(np.round(pos,7),axis=0,return_inverse=True)
            mode='welded texture seams' if closed(merged[idx]) else 'open'
        if volume<=1e-13 or mode=='open':failures.append({'group':part['label'],'material':part['material'],'volume':volume,'edges':mode})
        modes[mode]+=1;volumes.append(volume);count+=len(idx)
    dest=out/(level+'.glb');stats=builder.save(dest,META)
    assert stats['triangles']==count
    result={'file':dest.name,'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),
            'triangles':count,'solids':len(builder.parts),'groups':len({p['label'] for p in builder.parts}),
            'edge_checks':modes,'minimum_signed_volume_m3':min(volumes),'failures':failures}
    (out/(level+'-closure.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    if failures:raise ValueError(failures[:8])
    print(level,count,len(builder.parts),result['sha256'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('level',choices=['near','far']);parser.add_argument('output',type=Path)
    args=parser.parse_args();check(args.level,args.output)
