"""Cast rays through held-out blue/ochre extrema from the original photograph."""
from pathlib import Path
from hashlib import sha256
import argparse,json,sys,runpy
import numpy as np
pr=argparse.ArgumentParser(description=__doc__);pr.add_argument('--profiles',type=Path,required=True);pr.add_argument('--output',type=Path,required=True);pr.add_argument('mesh',type=Path)
args=pr.parse_args()
project=Path(__file__).absolute().parents[4]
src=project/'source/precise/huangpu-jiangxi-320-paired-pediment-windows/source';sys.path.insert(0,str(src))
from photo_plane import position
io=runpy.run_path(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py')
tri,index,names,info=io['load_triangles'](args.mesh)
info.pop('file',None)
photo=json.loads(args.profiles.read_bytes());res=[]
for slot in photo['profiles']:
 records=[]
 for r in slot['extrema']:
  u,v=r['xy'];origin=position(u,v,-1.35);dest=position(u,v,.65);direction=dest-origin;direction/=np.linalg.norm(direction)
  i,t,*_=io['first_hit'](tri,origin,direction)
  actual=names[index[i]]if np.isfinite(t)else None
  want={'blue':'Dusty blue awning stripe','ochre':'Warm flax awning stripe'}[r['kind']]
  records.append(dict(kind=r['kind'],pixel=r['xy'],photo_signal_prominence=r['prominence'],observed=actual,expected=want,passed=actual==want))
 res.append(dict(name=slot['curtain'],cases=records))
 print(slot['curtain'],sum(v['passed']for v in records),'/',len(records),[(p['kind'],p['pixel'],p['observed'])for p in records if not p['passed']])
args.output.write_text(json.dumps(dict(geometry=info,photo_profiles_sha256=sha256(args.profiles.read_bytes()).hexdigest(),results=res),indent=2)+'\n')
