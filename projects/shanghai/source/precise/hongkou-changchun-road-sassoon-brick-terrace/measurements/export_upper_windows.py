"""Build both editable window sets and verify closed, positively wound components."""
import argparse, hashlib, json, sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parents[3]/'tools'),str(HERE.parent/'source')]
from package_architectural_model import Builder
from upper_windows import PALETTE,add_windows,opening_profiles

def export(out):
    out.mkdir(parents=True,exist_ok=True)
    inventory={'openings_xz_bounds':{k:np.round(p.bounds,4).tolist() for k,p in opening_profiles().items()},'variants':{}}
    for tag,low in [('near',False),('far',True)]:
        b=Builder(PALETTE);add_windows(b,low)
        for part in b.parts:
            v=np.asarray(part['vertices']);f=np.asarray(part['triangles']);tri=v[f]-v.mean(axis=0)
            edges=Counter((int(a),int(c)) for t in f for a,c in zip(t,np.roll(t,-1)))
            volume=np.sum(tri[:,0]*np.cross(tri[:,1],tri[:,2]))/6
            assert volume>0 and np.all(np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)>1e-12),part['label']
            assert all(n==1 and edges[z,a]==1 for (a,z),n in edges.items()),part['label']
        target=out/f'windows-{tag}.glb'
        b.save(target,dict(id='changchun-north-window-study',name='长春路北立面窗',scope='16组实照窗',model_scope_zh='长春路建筑实见窗扇'))
        inventory['variants'][tag]={'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'closed_solids':len(b.parts),'triangles':sum(len(p['triangles'])for p in b.parts)}
    (out/'window-construction.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=1)+'\n')
    return inventory
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('out',type=Path);args=ap.parse_args();print(export(args.out)['variants'])
