"""Fit the upper hipped silhouette independently in four measured winter frames."""
import numpy as np,json
from scipy.optimize import least_squares
from pathlib import Path
D=Path(__file__).resolve().parent
source=json.loads((D/'upper-roof-silhouettes.json').read_text())
views=json.loads((D/'upper-room-stations.json').read_text())
cams=[views['cameras'][k] for k in ('F','E','R','L')]
edges=source['silhouette_pixels_in_975x650']
ends={int(k):v for k,v in source['terminal_eave_samples'].items()}
Ps=np.array([c['P'] for c in cams])
near=tuple(map(np.array,edges))

def points(q):
 a,b,y0,y1,z,z1,ux,vx,uy,vy=q
 ridge_y=(uy+vy)/2
 return np.array([[a,y0,z],[b,y0,z],[b,y1,z],[a,y1,z],[ux,ridge_y,z1],[vx,ridge_y,z1]])
links=[[0,1],[1,2],[2,3],[3,0],[0,4],[1,5],[2,5],[3,4],[4,5],[0,5],[1,4],[2,4],[3,5]]
def project(pts):
 h=np.c_[pts,np.ones(len(pts))];s=Ps@h.T;return np.moveaxis(s[:,:2]/s[:,2:3],1,2)*.8125
def score(q,full=False):
 pts=points(q);frame=project(pts);res=[];err=[]
 for i,p in enumerate(frame):
  values=[]
  for x,y in near[i]:
   candidates=[]
   for a,b in links:
    dp=p[b]-p[a];t=(x-p[a,0])/(dp[0]+1e-9);dy=p[a,1]+np.clip(t,0,1)*dp[1]-y;dx=(np.clip(t,0,1)-t)*dp[0]
    if (min(p[a,0],p[b,0])-1)<=x<=max(p[a,0],p[b,0])+1:candidates.append(dy)
   d=min(candidates)if candidates else y*.0+(np.min(abs(p[:,0]-x))+8);values.append(d)
  res.extend(np.array(values)/5);err.append(values)
  if i in ends:
   target=np.array(ends[i]);j=np.argmin(np.linalg.norm(p[:4]-target,axis=1));res.extend((p[j]-target)/20)
 a,b,y0,y1,z,z1,ux,vx,uy,vy=q
 res.extend([(z-10.08)/.5,(y0-3.94)/.48,(a+.55)/.48,(b-5.98)/.55,(uy-vy)/.30])
 return err if full else res
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('output',type=Path)
 result_path=parser.parse_args().output
 best=None
 for delta in [-.7,0,.5]:
  init=[-.6,6.,3.92,8.7,10.01,12+delta,1.2,4.91,6.2,6.2]
  opt=least_squares(score,init,bounds=([-1.6,5.22,3.20,6.6,9.76,10.7,-1,2.8,4.5,4.5],[.33,6.95,4.4,12.,10.9,14.5,3.5,6.75,10.5,10.5]),loss='soft_l1',max_nfev=500);err=np.median(np.abs(np.concatenate(score(opt.x,True))));print(np.round(opt.x,3),'error',err,[round(float(np.median(np.abs(d))),1)for d in score(opt.x,True)]); 
  if best is None or opt.cost<best[0]:best=(opt.cost,opt.x)
 q=best[1];out={'points':points(q).tolist(),'eyes':[c['eye']for c in cams],'mesh':'roof front-left/front-right/rear-right/rear-left, lower-X and higher-X ridge ends. X to right; y inward. Four silhouette curves were measured separately rather than equating apparent apices from opposing views.','projected_points_975':project(points(q)).tolist(),'silhouette_pixels_in_975x650':edges,'signed_reprojection_975_px':score(q,True),'terminal_eave_samples':ends};result_path.write_text(json.dumps(out,indent=2)+'\n')
