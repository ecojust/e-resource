"""Check authoring solids and reproduce the named raw files byte for byte."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import tempfile
import numpy as np
here=Path(__file__).resolve().parent
sys.path.insert(0,str(here.parent/'source'))
from build_model import build,write_named

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def examine(source,lod):
    builder=build(lod)
    with tempfile.TemporaryDirectory() as folder:
        regenerated=Path(folder)/source.name
        write_named(regenerated,builder)
        assert sha(source)==sha(regenerated)
    records=[]
    for part in builder.parts:
        vertices=np.asarray(part['vertices'])
        triangles=np.asarray(part['triangles'])
        _,welded=np.unique(vertices.astype('float32'),axis=0,return_inverse=True)
        indices=welded[triangles]
        edges=np.concatenate([indices[:,[0,1]],indices[:,[1,2]],indices[:,[2,0]]])
        _,counts=np.unique(np.sort(edges,axis=1),axis=0,return_counts=True)
        xyz=vertices[triangles]
        volume=np.einsum('ij,ij->i',xyz[:,0],np.cross(xyz[:,1],xyz[:,2])).sum()/6
        direction,frequency=np.unique(edges,axis=0,return_counts=True)
        paired={tuple(edge) for edge in direction}
        assert np.all(counts==2) and np.all(frequency==1) and all((j,i) in paired for i,j in paired) and volume>0,part['label']
        records.append(dict(part=part['label'],triangles=len(triangles),signed_volume_m3=float(volume),open_or_nonmanifold_edges=0,inconsistent_directed_edges=0))
    return dict(file=source.name,sha256=sha(source),all_parts_closed=True,parts=records)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('near',type=Path)
    parser.add_argument('far',type=Path)
    parser.add_argument('output',type=Path)
    a=parser.parse_args()
    results=[examine(a.near,False),examine(a.far,True)]
    a.output.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
