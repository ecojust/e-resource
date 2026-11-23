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
from build_model import build,META
from serialize_mesh import save_study

def inspect(lod,input_file):
    builder=build(lod);failures=[];volumes=[];triangles=0
    faces_by_part=[]
    for item in builder.parts:
        xyz=np.asarray(item['vertices'],dtype='<f4');indices=np.asarray(item['triangles'])
        points,inv=np.unique(xyz,axis=0,return_inverse=True);idx=inv[indices]
        e=np.concatenate((idx[:,[0,1]],idx[:,[1,2]],idx[:,[2,0]]));edges=Counter(map(tuple,e))
        tris=xyz[indices].astype(np.float64);tris-=tris[0,0].copy()
        volume=np.einsum('ij,ij->i',tris[:,0],np.cross(tris[:,1],tris[:,2])).sum()/6
        if any(count!=1 or edges[(b,a)]!=1 for (a,b),count in edges.items()) or volume<=1e-10:failures.append(item['label'])
        volumes.append(float(volume));triangles+=len(idx)
        faces_by_part.append(xyz[indices])
    # Use exact Float32 vertex bytes and integer face triples for the whole model.
    # This avoids allocating a pair of Python tuple sets for every emitted triangle.
    triangles_3d=np.ascontiguousarray(np.concatenate(faces_by_part))
    packed=triangles_3d.reshape(-1,3).view(np.dtype((np.void,12))).ravel()
    _,vertex_ids=np.unique(packed,return_inverse=True)
    face_ids=vertex_ids.reshape(-1,3)
    rotate=(face_ids.argmin(axis=1)[:,None]+np.arange(3))%3
    oriented=np.take_along_axis(face_ids,rotate,axis=1)
    repeated=len(oriented)-len(np.unique(oriented,axis=0))
    reversed_overlaps=len(face_ids)-len(np.unique(np.sort(face_ids,axis=1),axis=0))
    if failures or repeated:
        raise ValueError((failures,repeated,reversed_overlaps))
    del faces_by_part,triangles_3d,packed,face_ids,oriented,vertex_ids,rotate
    with tempfile.TemporaryDirectory(dir=input_file.parent) as t:
        report=save_study(builder,Path(t)/'replay.glb',META)
    original=hashlib.sha256(input_file.read_bytes()).hexdigest()
    assert report['sha256']==original and not failures and not repeated,(Counter(failures),repeated)
    return dict(sha256=original,parts=len(volumes),triangles=triangles,closed_with_positive_volume=len(volumes),minimum_volume_m3=min(volumes),duplicate_triangles=repeated,coincident_faces_including_opposed=reversed_overlaps,exact_rebuild=True)
if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('folder',type=Path);args=cli.parse_args()
    results={role:inspect(role=='lod',args.folder/(role+'-source.glb')) for role in ['full','lod']}
    (args.folder/'solid-review.json').write_text(json.dumps(results,indent=2)+'\n');print(results)
