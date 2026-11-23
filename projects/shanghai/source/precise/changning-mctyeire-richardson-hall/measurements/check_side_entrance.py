"""Test the emitted detached side door from Ctny's native photograph and check its solids."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import runpy
import sys
import numpy as np
from check_lawn import RAY, measure, render
from fit_side_entrance import px
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from side_entrance import *

# Independent surface samples, separate from the contour points used to construct the object.
samples={WOOD:[(142,226),(232,193),(321,212),(349,314)],FIELD:[(342,280),(345,335),(352,389),(128,411)],
    GLASS:[(222,187),(267,211),(290,209),(490,174),(779,185)],
    STEP:[(242,482),(229,503),(277,522),(220,536)],STONE:[(112,191),(326,183),(525,205),(678,208),(807,199)],
    PIPE:[(394,154),(394,229),(395,316)],CANVAS:[(210,64),(313,81)],ROLL:[(277,89),(418,102)],
    SHUTTER:[(552,185),(700,198)],SHADOW:[(214,273),(232,362)],ASH:[(422,145),(599,187)]}
def check_solid(b):
    wrong=[];counts=[]
    for piece in b.parts:
        xyz=np.asarray(piece['vertices'],dtype='<f4'); triangles=np.asarray(piece['triangles'])
        _,inv=np.unique(xyz,axis=0,return_inverse=True);links=inv[triangles]
        edges=Counter(map(tuple,np.concatenate([links[:,[0,1]],links[:,[1,2]],links[:,[2,0]]])))
        v=xyz[triangles].astype(float);v-=v[0,0].copy()
        volume=np.einsum('ij,ij->i',v[:,0],np.cross(v[:,1],v[:,2])).sum()/6
        if volume<=0 or any(n!=1 or edges[(j,i)]!=1 for (i,j),n in edges.items()):wrong.append([piece['label'],volume])
        counts.append(volume)
    return dict(total=len(counts),oriented_positive=len(counts)-len(wrong),minimum_volume_m3=min(counts),failed=wrong)
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('folder',type=Path);ap.add_argument('--render',action='store_true');args=ap.parse_args()
    checks={k:[tuple(np.rint(px(p)).astype(int).tolist()) for p in ps] for k,ps in samples.items()}
    P=np.asarray(json.loads(STATION.read_bytes())['projection'])
    scene=runpy.run_path(str(RAY))['SerialScene']; reports={}
    for role in ['full','lod']:
        path=args.folder/(role+'-side-entrance.glb')
        db=add_side_entrance(Builder(),role=='lod')
        data=measure(scene(path),P,checks);data['exact_mesh_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        data['solids']=check_solid(db)
        data['bounds_m']=[np.vstack([p['vertices'] for p in db.parts]).min(axis=0).tolist(),np.vstack([p['vertices'] for p in db.parts]).max(axis=0).tolist()]
        if args.render and role=='full':data['render']=render(path,args.folder/'side-entrance-model.jpg',P,[0,0,1600,1067])
        reports[role]=data;print(role,data['direct'],'/',data['count'],[(v['pixel'],v['expected'],v['first_hit']) for v in data['points'] if not v['direct']],data['solids'])
    (args.folder/'side-entrance-check.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n')
