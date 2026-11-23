"""Check directed edge closure of the additional lawn-wing components at each detail level."""
from collections import Counter
import argparse
from pathlib import Path
import json,sys
import numpy as np
S=Path(__file__).resolve().parents[1]; P=S.parents[2]
sys.path[:0]=[str(S/'source'),str(P/'source/precise/hongkou-general-post-office/source/common')]
from photo_architecture import Builder
from social_hall import PALETTE
from lawn_return import add_lawn_return

def check(lod):
    b=Builder(PALETTE);add_lawn_return(b,lod)
    invalid=[]
    for part in b.parts:
        points=np.array(part['vertices'],float)
        tri=np.array(part['triangles'],int)
        edges=Counter()
        for ia,ib,ic in tri.tolist():
            edges.update(((ia,ib),(ib,ic),(ic,ia)))
        open_edges=sum(count for (i,j),count in edges.items() if edges[j,i]!=count)
        p=points[tri]
        volume=float(np.sum(np.einsum('ij,ij->i',np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]),p[:,0]-p[0,0]))/6)
        if open_edges or volume<=1e-8:
            invalid.append(dict(label=part['label'],open_edges=open_edges,volume=volume))
    return dict(parts=len(b.parts),triangles=sum(len(p['triangles'])for p in b.parts),rejected=invalid)
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path);args=ap.parse_args()
    result={k:check(lod)for k,lod in (('full',False),('lod',True))};args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(result);sys.exit(any(r['rejected'] for r in result.values()))
