from pathlib import Path
import json,hashlib
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
W=Path(__file__).parent
proof=W/'2020-street-frontage.json'
rec=json.loads(proof.read_bytes()); rows=rec['controls']; ids=list(rows)
scale=np.array(rec['map_scale']); base,end=np.array(rec['osm_front']);v=(end-base)*scale;v=v/np.linalg.norm(v);front=np.array([v[1],-v[0]])
cams=np.array([list((np.array(p['ll'])-base)*scale)+[p['height']]for p in rec['stations']]); data=[]
for j,k in enumerate(ids):
 for i,p in enumerate(rows[k]['observations']):
  if p is None:continue
  pt=np.r_[v*(p[0]/40-3),20-p[1]/40];u=pt-cams[i]
  data.append((i,j,u/np.linalg.norm(u)))
si,fi=np.array([(a,b) for a,b,_ in data]).T;obs=np.array([c for a,b,c in data])
def indices(names):return [ids.index(k) for k in names.split()]
same_z=[indices(x)for x in ['left_wall_cornice right_wall_cornice','left_dormer_apex right_dormer_apex','left_pair_outer_arch_peak left_pair_inner_arch_peak right_pair_inner_arch_peak right_pair_outer_arch_peak','upper_middle_left_square_head upper_middle_right_square_head','upper_left_pair_inner_opening_left_spring upper_left_pair_inner_opening_right_spring','middle_left_pair_inner_arch_peak middle_right_pair_outer_arch_peak','middle_left_pair_inner_sill middle_right_pair_outer_sill']]
same_x=[indices(x)for x in ['left_pair_inner_arch_peak upper_left_pair_inner_sill middle_left_pair_inner_arch_peak middle_left_pair_inner_sill','right_pair_outer_arch_peak middle_right_pair_outer_arch_peak middle_right_pair_outer_sill']]
n=len(ids)
def fit(omit=-1,prior=2.0):
 sel=si!=omit
 def unpack(q):
  ang=q[0];tw=np.cos(ang)*v+np.sin(ang)*front;nw=np.cos(ang)*front-np.sin(ang)*v
  T=q[4:4+n];Z=q[4+n:4+2*n];d=np.full(n,q[1]);d[4:6]+=q[2];d[2:4]+=q[3]
  return T,Z,np.column_stack((T[:,None]*tw+d[:,None]*nw,Z)),q[4+2*n:].reshape(4,3)
 def resid(q):
  t,z,xyz,rot=unpack(q);vv=xyz[fi]-cams[si];vv/=np.linalg.norm(vv,axis=1)[:,None]
  rays=Rotation.from_rotvec(rot).apply if False else Rotation.from_rotvec(rot[si]).apply(obs)
  e=[((vv[sel]-rays[sel])/np.deg2rad(.22)).ravel(),rot.ravel()/np.deg2rad(prior),np.array([q[0]/np.deg2rad(12),q[2]/1.5,q[3]/.8])]
  for a in same_z:e.append(np.diff(z[a])/.12)
  for a in same_x:e.append(np.diff(t[a])/.10)
  e.append(np.array([(t[15]+t[16]-2*t[7])/.15]))
  return np.concatenate(e)
 q=np.r_[0,-1,0,0,[r['osm_edge_chainage_m'] for r in rows.values()],[r['height_m'] for r in rows.values()],np.zeros(12)]
 res=least_squares(resid,q,loss='soft_l1',max_nfev=60);t,z,xyz,rot=unpack(res.x)
 rays=Rotation.from_rotvec(rot[si]).apply(obs);vv=xyz[fi]-cams[si];dist=np.linalg.norm(vv,axis=1);cos=np.sum(vv/dist[:,None]*rays,axis=1).clip(-1,1)
 metrics={'cornice_width':t[1]-t[0],'upper_pair_left_axial_spacing':t[7]-t[6],'upper_pair_right_axial_spacing':t[9]-t[8],'upper_pair_inner_opening':t[16]-t[15],'central_square_axial_spacing':t[18]-t[17],'dormer_spacing':t[5]-t[4],'street_cornice_height':np.mean(z[:2]),'central_crest':z[2],'central_shoulder':z[3],'dormer_apex':np.mean(z[4:6]),'upper_arch_peak':np.mean(z[6:10]),'upper_sill':z[10],'middle_arch_peak':np.mean(z[[11,12]]),'middle_sill':np.mean(z[[13,14]])}
 return dict(metrics={k:round(float(v),3) for k,v in metrics.items()},absolute_points={k:dict(wgs84=(base+xyz[i,:2]/scale).tolist(),height_m=round(float(z[i]),3)) for i,k in enumerate(ids)},rotation_degrees=np.degrees(rot).round(3).tolist(),range_adjusted_residuals_m=dict(median=round(float(np.median(np.sin(np.arccos(cos[sel]))*dist[sel])),3),p95=round(float(np.quantile(np.sin(np.arccos(cos[sel]))*dist[sel],.95)),3)),azimuth_change_degrees=round(float(np.degrees(res.x[0])),3))
all=fit();tests=[fit(i)['metrics'] for i in range(4)]+[fit(-1,p)['metrics'] for p in [.8,4]]
out=dict(method='Unsurveyed facade estimate from four 2020 street panoramas. Fixed vehicle positions/2.32 m camera heights. Fit plane, real common floor/eaves heights, vertical window axes and per-panorama small bearing, tilt and roll rotations. Dormers and central gable may stand back separately. No map width used as constraint. Systematic street-image georeferencing remains. Variation includes leave-one-station-out and 0.8/4 degree orientation regularization.',order=424,input_sha256=hashlib.sha256(proof.read_bytes()).hexdigest(),program_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),full=all,stability_intervals={k:[min(t[k] for t in tests),max(t[k] for t in tests)]for k in all['metrics']})
(W/'four-station-facade-adjustment.json').write_text(json.dumps(out,indent=1)+'\n');print(all['metrics']);print(out['stability_intervals']);print(all['rotation_degrees'],all['range_adjusted_residuals_m'])
