"""Recompute the joint fit in a new JSON file. All pixel features and camera data are local.

Usage: python recompute_jkk_camera_fit.py output.json
"""
from pathlib import Path
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
import numpy as np,json
import argparse
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('output', type=Path)
destination = parser.parse_args().output
directory = Path(__file__).resolve().parent
evidence = json.loads((directory / 'central-steel-source-pixels.json').read_text())
frames = json.loads((directory / 'jkk-calibration-inputs.json').read_text())['frames']
center=np.array([121.44051,31.217597]);metres=[111319.49*np.cos(np.radians(center[1])),110852.]
az0=np.radians(86.261);axes=np.array([[np.sin(az0), np.cos(az0),0],[-np.cos(az0),np.sin(az0),0],[0,0,1]])
opening_names=['low','middle','upper_main','upper_transom']
stations=list(dict.fromkeys(m['station']['id'] for m in frames.values()))
native_eye={};keys={};obs=[]
for name,m in frames.items():
 station=m['station'];sid=station['id'];native_eye[sid]=axes @ np.r_[(np.asarray(station['position'])-center)*metres,station['height']]
 a,p=np.radians([m['az'],m['pitch']])
 right=[np.cos(a),-np.sin(a),0.];down=[np.sin(a)*np.sin(p),np.cos(a)*np.sin(p),-np.cos(p)];forward=[np.sin(a)*np.cos(p),np.cos(a)*np.cos(p),np.sin(p)]
 orient=np.array([right,down,forward])@axes.T;f=m['width']/(2*np.tan(np.radians(m['hfov']/2)))
 K=np.array([[f,0,m['width']/2],[0,f,m['height']/2],[0,0,1.]])
 keys[name]=(stations.index(sid),K,orient,f)
 if name in evidence['frames']:
  for op,marks in evidence['frames'][name]['marks'].items():
   if op not in opening_names:continue
   for corner,uv in marks.items():
    if corner in ('TL','TR','BL','BR'):obs.append((name,op,corner,uv,1.))
main={'bay-west-sill':[[466.8,478.1],[442.7,519.5],[398.,510.0]],'bay-east-sill':[[513.8,477.8],[479.5,522.],[429.8,507.5]],'balcony-east-edge':[[685.5,359.8],[647.5,429.2],[565.5,365.5]],
 'balcony-straight-start':[[536.0,359.],[517.5,411.],[427.5,401.]]}
for op,pixels in main.items():
 for n,uv in zip(['upper-central-20','upper-west-15','upper-east-15'],pixels):obs.append((n,op,'X',uv,.45 if op.startswith('balcony') else .65))
# Shaft centre XY, four widths; individual lower and upper elevations; two ends of
# the neighbouring window sill; balcony horizontal front edge. Photo facade axes
# are shared. The two ends of a slab occupy the same physical elevation.
v0=[-5,1.,1.62,1.62,1.62,1.62, 2.8,4.9,6.9,9.05,10.8,12.1,12.35,12.98, -2.2,-1.0,-1.5,5.2, .5,4.9,-3.0,8.25]
N=len(v0);native=np.array([native_eye[s] for s in stations]);x0=np.r_[v0,np.zeros(len(stations)*5)]
def calculate(v):
 layout=np.asarray(v[:N]);corr=v[N:].reshape((-1,5));basis=Rotation.from_rotvec(corr[:,:3]).as_matrix()
 eyes=native+np.c_[corr[:,3:5],np.zeros(len(stations))]
 pts=[]
 for frame,op,corner,uv,w in obs:
  if op in opening_names:
   i=opening_names.index(op);x=layout[0]+(-.5 if 'L'in corner else .5)*layout[2+i]; point=[x,layout[1],layout[6+2*i+int('T'in corner)]]
  elif op.startswith('bay'):point=[layout[14+int(op=='bay-east-sill')],layout[16],layout[17]]
  else:point=[layout[18+int(op=='balcony-east-edge')],layout[20],layout[21]]
  pts.append(point)
 return corr,basis,eyes,np.array(pts)
weight=np.array([o[4] for o in obs]);fid=np.array([keys[o[0]][0]for o in obs])
km=np.array([keys[o[0]][1]for o in obs]);rot=np.array([keys[o[0]][2]for o in obs]);focal=np.array([keys[o[0]][3]for o in obs]);image_uv=np.array([o[3]for o in obs])
def residual(v,ret=False):
 corr,basis,eyes,pts=calculate(v)
 p=np.einsum('bij,bjk,bkl,bl->bi',km,rot,basis[fid],pts-eyes[fid]);uv=p[:,:2]/p[:,2,None];delta=(uv-image_uv)*550/focal[:,None]
 if ret:return delta
 return np.r_[(delta*weight[:,None]).ravel(),corr[:,:3].ravel()*150, corr[:,3:5].ravel()*5.5,(v[3:6]-v[2])*11,(v[15]-v[14]-1.05)*1.2]
sol=least_squares(residual,x0,loss='soft_l1',f_scale=1.45, max_nfev=420)
v=sol.x;print('layout',np.around(v[:N],3));err=np.linalg.norm(residual(v,True),axis=1)
for name in frames:
 ids=[i for i,o in enumerate(obs)if o[0]==name]
 if ids: print(name,len(ids),np.round(np.percentile(err[ids],[50,90,100]),2))
corr,basis,eyes,points=calculate(v);origin=np.array([v[0],v[16],0.])
output={};per={}
for n,(i,k,rt,f) in keys.items():
 m=k@rt@basis[i];P=m@np.column_stack((np.eye(3),origin-eyes[i]));output[n]=P.tolist()
for i,sid in enumerate(stations):
 per[sid]={'rotation_correction_deg':np.rad2deg(corr[i,:3]).round(3).tolist(),'camera_translation_correction_m':corr[i,3:5].round(3).tolist(),'eye_local_m':(eyes[i]-origin).round(4).tolist()}
controls=[]
for i,(name,op,c,uv,w) in enumerate(obs):
 controls.append({'camera':name,'feature':op+' '+c,'measurement_px':uv,'local_xyz_m':(points[i]-origin).round(4).tolist(),'check_equivalent_px_at_f550':round(float(err[i]),3)})
out={'reference':'Masonry behind street-facing balconies, excluding projecting belt bands. World +X approximately east (initial coarse axis 86.261 degrees), +Y into building, Z upward from estimated pavement. X0 is the central stair-window axis.','origin_in_initial_local_frame':origin.tolist(),'widths_and_sills':v[:N].tolist(),'camera_matrices':output,'station_fits':per,'features':controls,'median_reference_px':np.median(err),'p90_reference_px':np.percentile(err,90)}
destination.write_text(json.dumps(out,ensure_ascii=False,indent=1)+'\n')
