"""Recover working pinholes for the two opposite clock elevations. Image coordinates refer to pixel centres."""
import numpy as np
from scipy.optimize import least_squares
from pathlib import Path
import json,hashlib
out=Path(__file__).resolve().parent
EXIF_F=7.0*8114.285714285715/25.4*1000/2272
# Equal-height bands physically continue around the tower. The opposite dial panels are not assumed identical.
planes={'court':12.50,'street':0.0}
xs={'court':-1,'street':1}
controls=[]
def ctrl(s,label,uv,point,hold=False,sigma=1.6):
 controls.append((s,label,uv,point,hold,sigma))
for side,u in [(-1,834),(1,165)]:
 ctrl('court','court corner at planted lawn', [u,621 if u==165 else 620],lambda v,sg=side:(sg*10.375,12.5,0),sigma=2.2)
for st,data in [('court',[(420,465,582,463),(422,324,580,323),(423,246,578,245),(423,138,577,137)]),('street',[(429,474,702,478),(455,304,664,304),(468,234,653,236),(474,159,639,161)])]:
 for n,(xl,yl,xr,yr) in enumerate(data):
  for sg,u,vv in [(-1,xl,yl),(1,xr,yr)]:
   ctrl(st,'tower band '+str(n)+' edge '+str(sg),[u,vv],lambda v,s=st,i=n,sg=sg:(xs[s]*sg*v[14]/2,planes[s],v[15+i]),sigma=2)
# Court return planes at X=±10.375. Two piers, on either wing, share a regular longitudinal pitch.
# Their floor/waist/eave crossings are read independently. The third visible arcade on each side is nearest.
for sg,samples in [(1,[(116,633,454,318),(73,642,444,292)]),(-1,[(880,629,454,315),(922,635,444,291)])]:
 for i,(x,ground,waist,eave) in enumerate(samples,1):
  # Pillar centre and inner roof angle have distinct X at the roof overhang. Only wall-to-pier and waist belong here.
  ctrl('court','return pier %s %d ground'%(sg,i),[x,ground],lambda v,sg=sg,i=i:(sg*10.375,12.5+i*v[19],0),sigma=3)
  ctrl('court','return pier %s %d at belt'%(sg,i),[x,waist],lambda v,sg=sg,i=i:(sg*10.375,12.5+i*v[19],v[15]),sigma=3)
# More reliable independent straight edges, first spring and clock midpoint. Bands hold out every other centre.
for s,rows in [('court',[(501,464),(501,324),(500,245),(500,137)]),('street',[(567,477),(559,304),(558,234),(557,160)])]:
 for n,uv in enumerate(rows):ctrl(s,'held centre of tower band '+str(n),uv,lambda v,i=n,s=s:(0,planes[s],v[15+i]),True,2)
# Held independent points on return planes halfway between first and second pier lie on the same belt.
# Read true transverse lines at fixed image x, checked after fitting with the plane's horizontal vanishing direction.
side_lines=[('court',[0,655],[164,621],0),('court',[999,650],[833,620],0),('court',[0,428],[165,465],1),('court',[999,426],[834,461],1)]
def camera(p,s):
 if s=='court':x,y,z,yaw,pitch,roll,cy=p[:7];f=EXIF_F;cx=499.5;orientation=-1
 else:x,y,z,yaw,pitch,roll,logf=p[7:14];f=np.exp(logf);cx=539.5;cy=404.5;orientation=1
 c=np.array([x,y,z])
 d=np.array([np.sin(yaw)*np.cos(pitch),orientation*np.cos(yaw)*np.cos(pitch),np.sin(pitch)])
 rr=np.array([orientation*np.cos(yaw),-np.sin(yaw),0.])
 up=np.cross(rr,d);right=rr*np.cos(roll)+up*np.sin(roll);vertical=up*np.cos(roll)-rr*np.sin(roll)
 R=np.array([right,-vertical,d]);K=np.array([[f,0,cx],[0,f,cy],[0,0,1]])
 return c,K,R,K@np.c_[R,-R@c]
def proj(P,xyz):
 q=P@np.r_[xyz,1];return q[:2]/q[2]
def fun(p):
 Ps={s:camera(p,s)[3] for s in planes};out=[]
 for s,l,uv,xyz,h,sd in controls:
  if not h:out.extend((proj(Ps[s],xyz(p))-uv)/sd)
 out.extend([(p[9]-1.6)/.6,(p[6]-480)/130,((p[7])/1.8),(p[19]-3.3)/1.0])
 return out
p0=np.array([-.1,43.1,2.2,0,.01,0,523, -.1,-9.2,1.6,0,.45,0,np.log(680),4.95,4.85,9.18,11.70,15.11,3.2])
L=[-4,32,.4,-.16,-.3,-.05,240, -3,-26,.2,-.20,.12,-.06,np.log(300),4.4,4.2,8.4,11.,14.4,1.9]
U=[4,53,5,.16,.3,.05,625, 3,-3,3.2,.2,.90,.06,np.log(1500),5.6,5.5,9.9,12.5,16.0,4.6]
fit=least_squares(fun,p0,bounds=(L,U),loss='soft_l1',max_nfev=1400,xtol=1e-12,ftol=1e-12)
p=fit.x;stations={};meta=json.loads((out/'source-metadata.json').read_bytes())
for s in planes:
 c,k,r,P=camera(p,s);rows=[]
 for st,label,uv,xyz,held,sd in controls:
  if st!=s:continue
  a=xyz(p);re=proj(P,a)
  rows.append(dict(feature=label,pixel=uv,world_xyz=list(a),projected_pixel=re.tolist(),error_px=float(np.linalg.norm(re-uv)),holdout=held))
 stations[s]=dict(photo='metromod-00' if s=='court' else 'newspaper-03',image_size=[1000,745] if s=='court' else [1080,810],C=c.tolist(),K=k.tolist(),R=r.tolist(),P=P.tolist(),controls=rows)
def wall(st,uv,y):
 a=stations[st];c=np.array(a['C']);v=np.array(a['R']).T@np.linalg.solve(a['K'],[*uv,1]);return c+v*(y-c[1])/v[1]
reads={}
for s,points in [('court',{'third-floor cornice':[501,325],'upper roof soffit, projected to face':[500,75],'wing eave under fascia':[308,350],'wing roof axis ridge':[309,286],'wing openings sill':[288,436],'wing windows heads':[289,378],'tower dial centre':[500,195],'clock panel upper':[500,148],'clock panel lower':[500,239],'central arch crown':[501,477],'arch spring':[459,525],'raised roof tip projected to face':[402,22]}),('street',{'portal inner crown':[566,522],'portal outer moulding crown':[566,494],'portal righthand spring':[669,618],'wing soffit':[297,320],'inner portal foot':[475,804],'clock panel upper':[560,168],'clock panel lower':[558,229],'upper roof soffit projected to face':[556,126]})]:
 reads[s]={n:{'pixel':uv,'intersection_on_labelled_plane':wall(s,uv,planes[s]-(6.25 if n=='wing roof axis ridge' else 0)).tolist()} for n,uv in points.items()}
result=dict(frame='Metres. Ground at court facade v=620–621. X east along street; Y north into court. Published court opening width 20.75 m used as scale; distance from street to south internal elevation fixed at 12.50 m.',stations=stations,exif_focal_px=EXIF_F,parameters=dict(tower_width=p[14],waist_height=p[15],third_floor_base_height=p[16],band_below_dial=p[17],band_above_dial=p[18],fitted_return_pier_pitch=p[19]),readings=reads,limitations=['Court image edited in Photoshop. Its effective vertical principal point is estimated, focal length anchored to camera EXIF including focal-plane X resolution.','Street camera has no EXIF. Focal length and pose are estimated from common tower geometry and a soft standing-eye-height prior.','A returned intersection on a facade plane is not a depth measurement of the eave, its upturn, or the dial.','Additional return pier ground positions are partly obscured by vegetation; weights reflect this.'])
(out/'tower-stations.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
for s in stations:
 rows=stations[s]['controls'];print(s,'C',np.round(stations[s]['C'],3),'K',np.round(np.array(stations[s]['K'])[[0,1],[0,2]],2),'fit RMS',np.sqrt(np.mean([a['error_px']**2 for a in rows if not a['holdout']])),'held', [round(a['error_px'],1) for a in rows if a['holdout']])
print('params',result['parameters'],'reads',[(k,round(v['intersection_on_labelled_plane'][2],2)) for k,v in reads['court'].items()])
