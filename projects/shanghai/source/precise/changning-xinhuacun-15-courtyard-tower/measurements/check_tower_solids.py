"""Verify individual closed groups, consistent orientation and volume in the generated building."""
import argparse,json,sys
from collections import Counter
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).absolute().parents[1]/'source'))
from build_model import PALETTE,add_building
from photo_architecture import Builder
def check(lod):
    b=Builder(PALETTE);add_building(b,lod);bad=[];total=0
    for part in b.parts:
        t=np.asarray(part['triangles']);v=np.asarray(part['vertices']);e=Counter();total+=len(t)
        for i,j,k in t:e.update([(i,j),(j,k),(k,i)])
        mismatches=sum(1 for (a,b),x in e.items()if e[b,a]!=x);tri=v[t]-v[t[0,0]]
        volume=float(np.sum(np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2])))/6.)
        if mismatches or volume<=1e-10:bad.append({'label':part['label'],'unpaired':mismatches,'signed_volume':volume})
    return dict(groups=len(b.parts),triangles=total,bad=bad)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);a=p.parse_args();report={k:check(l)for k,l in [('full',False),('lod',True)]};a.out.write_text(json.dumps(report,indent=2)+'\n');print([(k,len(r['bad']),r['bad'][:3])for k,r in report.items()]);sys.exit(any(r['bad']for r in report.values()))
