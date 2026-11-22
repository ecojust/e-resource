"""Export one epoch and detail level after checking every independent solid."""
from pathlib import Path
import argparse,collections,hashlib,json,sys
import numpy as np

p=argparse.ArgumentParser();p.add_argument('role',choices=('historic','lod','full'));p.add_argument('--out',type=Path,required=True);args=p.parse_args()
s=Path(__file__).resolve().parents[1]/'source'
sys.path.insert(0,str(s))
from build_model import GatehouseBuilder,PALETTE,add_building,metadata
period='2018' if args.role=='historic' else '2022'
b=GatehouseBuilder(PALETTE)
add_building(b,args.role=='lod',period)
def closed(f):
 edges=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);m=edges.max()+1
 forward=np.sort(edges[:,0]*m+edges[:,1]);backward=np.sort(edges[:,1]*m+edges[:,0])
 return np.all(forward[1:]!=forward[:-1]) and np.array_equal(forward,backward)
fail=[];modes=collections.Counter();minimum=1e30;labels=set()
for part in b.parts:
 v=np.asarray(part['vertices']);f=np.asarray(part['triangles'])
 t=v[f]-v[f[0,0]];vol=np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6
 mode='indexed' if closed(f) else 'uv' if closed(np.unique(v.round(8),axis=0,return_inverse=True)[1][f]) else 'open'
 if mode=='open' or vol<=1e-13:fail.append({'part':part['label'],'mode':mode,'volume':vol})
 minimum=min(minimum,float(vol));modes[mode]+=1;labels.add(part['label'])
report={'period':period,'role':args.role,'parts':len(b.parts),'groups':len(labels),'triangles':sum(len(part['triangles'])for part in b.parts),'edge_modes':modes,'minimum_volume_m3':minimum,'failures':fail,'overlong_labels':[v for v in labels if len(v.encode())>63]}
path=args.out;path.mkdir(exist_ok=True,parents=True)
(path/(args.role+'-closed.json')).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items()if k!='failures'}),fail[:8],flush=True)
if fail or report['overlong_labels']:raise SystemExit(2)
f=path/(args.role+'-source.glb');g=b.save(f,metadata(period));assert g['triangles']==report['triangles']
print(json.dumps({k:g[k]for k in ('parts','triangles','bytes','sha256')}),flush=True)
