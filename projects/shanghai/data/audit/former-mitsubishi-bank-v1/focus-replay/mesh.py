from pathlib import Path
import json,runpy,numpy as np
w=Path(__file__).parent;p=Path('/workspace/e-resource/projects/shanghai');tools=p/'data/audit/postal-office-v1/independent-glb-review-helpers.py';f=p/'assets/models/candidates/huangpu-former-mitsubishi-bank/huangpu-former-mitsubishi-bank-raw.glb';tri,mat,names,_=runpy.run_path(str(tools))['load_triangles'](f);print(names)
x,y,z=tri.transpose(2,0,1);spec={}
def store(k,mask):
 q=tri[mask];vs,idx=np.unique(q.reshape(-1,3),axis=0,return_inverse=True);spec[k]=dict(vertices=vs.tolist(),triangles=idx.reshape(-1,3).tolist());assert len(q)>0,k;print(k,len(q),q.min(axis=(0,1)),q.max(axis=(0,1)))
for i,center in enumerate([-6.55,-2.19,2.19,6.55]):
 mask=(((x-center)**2+(y+.18)**2<1.01**2)&(z>=.789)&(z<=12.47)).all(axis=1)&(mat==names.index('light dressed granite'));store('shaft'+str(i+1),mask)
c=((abs(x)<1.18)&(y>=2.20)&(y<=2.34)&(z>=.789)&(z<=3.63)).all(axis=1)
store('central entrance',c)
(w/'mesh.json').write_text(json.dumps(spec,separators=(',',':')))
