"""Check every model component for directed manifold edges and nonzero positive volume."""
from collections import Counter
from pathlib import Path
import argparse
import hashlib
import json
import sys
import tempfile
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from build_model import Builder,PALETTE,add_building,META

def inspect(lod,input_file):
    builder=add_building(Builder(PALETTE),lod);failures=[];volumes=[];triangles=0
    seen=set();repeated=[];unoriented=set();reversed_overlaps=0
    for item in builder.parts:
        xyz=np.asarray(item['vertices'],dtype='<f4');indices=np.asarray(item['triangles'])
        points,inv=np.unique(xyz,axis=0,return_inverse=True);idx=inv[indices]
        e=np.concatenate((idx[:,[0,1]],idx[:,[1,2]],idx[:,[2,0]]));edges=Counter(map(tuple,e))
        tris=xyz[indices].astype(np.float64);tris-=tris[0,0].copy()
        volume=np.einsum('ij,ij->i',tris[:,0],np.cross(tris[:,1],tris[:,2])).sum()/6
        if any(count!=1 or edges[(b,a)]!=1 for (a,b),count in edges.items()) or volume<=1e-10:failures.append(item['label'])
        volumes.append(float(volume));triangles+=len(idx)
        for face in xyz[indices]:
            v=tuple(map(bytes,face));key=min(v,v[1:]+v[:1],v[2:]+v[:2])
            if key in seen:repeated.append(item['label'])
            seen.add(key);unordered=tuple(sorted(v))
            if unordered in unoriented:reversed_overlaps+=1
            unoriented.add(unordered)
    with tempfile.TemporaryDirectory(dir=input_file.parent) as t:
        report=builder.save(Path(t)/'replay.glb',META)
    original=hashlib.sha256(input_file.read_bytes()).hexdigest()
    assert report['sha256']==original and not failures and not repeated,(failures,repeated[:3])
    return dict(sha256=original,parts=len(volumes),triangles=triangles,closed_with_positive_volume=len(volumes),minimum_volume_m3=min(volumes),duplicate_triangles=len(repeated),coincident_faces_including_opposed=reversed_overlaps,exact_rebuild=True)
if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('folder',type=Path);args=cli.parse_args()
    results={role:inspect(role=='lod',args.folder/(role+'-source.glb')) for role in ['full','lod']}
    (args.folder/'solid-review.json').write_text(json.dumps(results,indent=2)+'\n');print(results)
