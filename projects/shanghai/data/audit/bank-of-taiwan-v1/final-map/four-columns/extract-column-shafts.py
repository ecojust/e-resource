"""Extract the four shaft assemblies from the actual decoded 54,008-triangle near file."""
import hashlib,json,runpy,sys
from pathlib import Path
import numpy as np
p=Path(sys.argv[1]).resolve()
work=Path(sys.argv[3]).resolve();work.mkdir(exist_ok=True,parents=True)
load=runpy.run_path(str(p/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['load_triangles']
tri,materials,names,asset=load(Path(sys.argv[2]))
assert len(tri)==54008
x,y,z=tri.transpose(2,0,1)
spec={}
for index,center in enumerate((-7.56,-2.52,2.52,7.56)):
 mask=(((x-center)**2+(y-.87)**2<.97**2)&(z>=1.5199)&(z<=13.4202)).all(axis=1)&(materials==names.index("silver grey granite"))
 picked=tri[mask];vs,idx=np.unique(picked.reshape(-1,3),axis=0,return_inverse=True)
 assert len(picked)>800 and abs(np.min(picked[:,:,2])-1.52)<.0001 and abs(np.max(picked[:,:,2])-13.42)<.0001
 spec[str(index)]={'center_x_m':center,'vertices':vs.round(6).tolist(),'triangles':idx.reshape(-1,3).tolist(),'triangle_count':len(picked),'materials':sorted({names[i] for i in materials[mask]})}
out={'decoded_asset':asset,'columns':spec}
(work/'columns.json').write_text(json.dumps(out,separators=(',',':'))+'\n')
print([(v['triangle_count'],len(v['vertices']),v['materials'])for v in spec.values()])
