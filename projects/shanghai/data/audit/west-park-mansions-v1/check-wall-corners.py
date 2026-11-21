from pathlib import Path
import numpy as np, sys, json
p=Path(__file__).resolve().parents[3];s=p/'source/precise/changning-west-park-mansions/source';sys.path.insert(0,str(s))
import build_model as m
from photo_architecture import Builder
b=Builder(m.PALETTE);m.add_building(b);hits=[]
for label,point in [('west front wall beyond main tower',[-14.01,-7.91,11.011]),('west flank near south',[-14.10,-7.80,11.011]),('east garden edge',[11.34,-9.46,11.011]),('garden centre',[.42,-9.46,22.78])]:
 pt=np.array(point);sample={'label':label,'xy_height_m':point,'coplanar_exterior':[]}
 for part in b.parts:
  if 'continuous-open-wall' not in part['label']:continue
  a=np.asarray(part['vertices'])[part['triangles']];t=a[:,1]-a[:,0];u=a[:,2]-a[:,0];n=np.cross(t,u);ln=(n*n).sum(axis=1);v=pt-a[:,0];plane=(v*n).sum(axis=1)/np.sqrt(ln);x=(np.cross(v,u)*n).sum(axis=1)/ln;y=(np.cross(t,v)*n).sum(axis=1)/ln
  for i in np.flatnonzero((abs(plane)<1e-6)&(x>=0)&(y>=0)&(x+y<=1)):
   sample['coplanar_exterior'].append({'wall':part['label'],'normal':(n[i]/np.sqrt(ln[i])).tolist()})
 hits.append(sample)
assert all(len(sample["coplanar_exterior"]) == 1 for sample in hits)
print(json.dumps(hits,ensure_ascii=False,indent=2),flush=True)
