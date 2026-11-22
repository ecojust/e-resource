"""Write the two standalone editable portal meshes and check each closed shell."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[3]/'tools')]
from package_architectural_model import Builder
from paired_entrances import PALETTE,add_entrances,door_openings

def export(out):
    out.mkdir(exist_ok=True,parents=True)
    receipt=dict(openings=door_openings(),variants={})
    for name in ['full','lod']:
        b=Builder({});add_entrances(b,name=='lod')
        for p in b.parts:
            v=np.asarray(p['vertices']);f=np.asarray(p['triangles']);tri=v[f]-v.mean(axis=0)
            oriented=Counter((int(a),int(c)) for t in f for a,c in zip(t,np.roll(t,-1)))
            volume=np.sum(tri[:,0]*np.cross(tri[:,1],tri[:,2]))/6
            assert volume>0 and np.all(np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)>1e-12),p['label']
            assert all(value==1 and oriented[z,a]==1 for (a,z),value in oriented.items()),p['label']
        output=out/f'doors-{name}.glb';b.save(output,dict(id='wujin-225-paired-door-component',name='9号及11号双门',scope='门楼独立制作校验',model_scope_zh='门楼对照'))
        receipt['variants'][name]=dict(sha256=sha256(output.read_bytes()).hexdigest(),parts=len(b.parts),triangles=sum(len(q['triangles'])for q in b.parts),closed=True,positive_volume=True)
    (out/'paired-door-construction.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
    return receipt
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path);opt=ap.parse_args();print(export(opt.output)['variants'])
