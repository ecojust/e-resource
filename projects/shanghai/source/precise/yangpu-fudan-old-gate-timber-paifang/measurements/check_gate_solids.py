"""Check that all timber, roof and masonry pieces have paired, consistently oriented edges."""
import argparse,json,sys
from collections import Counter
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
from build_model import Builder,PALETTE,add_building
def check(lod,inscribed=True):
    b=Builder(PALETTE);add_building(b,lod,inscribed);bad=[];count=0
    for p in b.parts:
        t=np.array(p['triangles']);v=np.array(p['vertices']);count+=len(t)
        e=Counter()
        for i,j,k in t:e.update([(i,j),(j,k),(k,i)])
        n=sum(1 for (i,j),a in e.items()if e[j,i]!=a)
        xyz=v[t]-v[t[0,0]];vol=np.sum(np.einsum('ij,ij->i',xyz[:,0],np.cross(xyz[:,1],xyz[:,2])))/6
        if n or vol<=1e-9:bad.append(dict(part=p['label'],edge_mismatches=n,signed_volume_m3=vol))
    return dict(parts=len(b.parts),triangles=count,bad=bad)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);a.add_argument('--first',action='store_true');args=a.parse_args();d={k:check(l,not args.first)for k,l in [('full',False),('lod',True)]};args.out.write_text(json.dumps(d,indent=2)+'\n');print([(k,len(r['bad']),r['bad'][:2])for k,r in d.items()]);sys.exit(any(r['bad'] for r in d.values()))
