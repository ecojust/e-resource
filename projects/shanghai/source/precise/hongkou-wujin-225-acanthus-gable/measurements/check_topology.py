"""Verify winding, closure and positive volume for every editable source component."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
from build_model import GableBuilder, PALETTE, add_gable
from package_architectural_model import group_parts

def inspect(lod):
    builder=GableBuilder(PALETTE)
    add_gable(builder,lod)
    unique_edges=triangles=0
    smallest=float('inf')
    for part in builder.parts:
        points=np.array(part['vertices'])
        faces=np.array(part['triangles'])
        p=points[faces]
        volume=np.sum(p[:,0]*np.cross(p[:,1],p[:,2]))/6
        assert volume>0,(part['label'],volume)
        _,weld=np.unique(points,axis=0,return_inverse=True)
        edges=Counter()
        for a,b,c in weld[faces]:
            edges.update(((a,b),(b,c),(c,a)))
        assert all(edges[a,b]==edges[b,a]==1 for a,b in edges),part['label']
        smallest=min(smallest,volume);triangles+=len(faces);unique_edges+=len(edges)//2
    return dict(parts=len(builder.parts),groups=len(group_parts(builder)),triangles=triangles,unique_edges=unique_edges,min_signed_volume=float(smallest),passed=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report',type=Path);args=parser.parse_args()
    args.report.write_text(json.dumps({k:inspect(lod) for k,lod in [('full',False),('lod',True)]},indent=2)+'\n')
