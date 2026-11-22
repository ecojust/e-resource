"""Joint fit of the two public corner photographs to independent street stations; units are metres."""
from pathlib import Path
from scipy.optimize import least_squares
import json,numpy as np
p=Path(__file__).parent
cams=[json.loads((p/(n+'-camera.json')).read_bytes())for n in ('city','named')]
Ks=[np.array(c['K'])for c in cams];Rs=[np.array(c['R'])for c in cams]
anchor=np.array([121.48798459,31.24940285]);metres=np.array([95175,110860]);bearing=np.deg2rad(325.76237479027736)
basis=np.array([[np.sin(bearing),np.cos(bearing)],[-np.cos(bearing),np.sin(bearing)]])
def local(ll):return (np.array(ll)-anchor)*metres@basis.T
stationXY=np.array([local(x)for x in [[121.48782709,31.24921404],[121.48796241,31.24937626],[121.4879735,31.24939123],[121.48797153,31.24940798],[121.48796804,31.24942373],[121.48786856,31.24954922]]])
sdir=stationXY[0]/np.linalg.norm(stationXY[0])
meas=np.array([np.linalg.norm(stationXY[0]),np.linalg.norm(stationXY[1]),*stationXY[2],*stationXY[3],stationXY[4,0],stationXY[5,0]])
def ring(plan):return np.array([plan[0]*sdir,plan[1]*sdir,plan[2:4],plan[4:6],[plan[6],0.],[plan[7],0.]])
# Projected verticals traced on the bare wall in preference to the projecting horizontal lips.
horizontal=[[(0,24.5,554.,3.5),(1,326,525,3.5),(2,400,549,3.5),(3,482,525,2.5),(4,569,509,4.5)],
            [(0,60.5,223.,2.1),(1,230.,223.,2.),(2,272.,225.,2.),(3,323.,227.,2.),(4,360.,218.,2.5),(5,498.5,182,2.1)]]
# Window rows along the west wing are interrupted by the gable; their heights are not forced
# equal to the opposite wing. Only the visually continuous portion of the two corner belts is shared.
bands=[ [[(328,338),(396,311),(479,298),(567,315)],[(327,739),(400,737),(485,735),(572,737)]],
        [[(244.5,109),(276,98),(317.7,99),(351,114)],[(220.5,304),(272.5,302),(325,301),(365,302)]] ]
ties=json.loads((p/'two-view-tie-points.json').read_bytes())
selected=[t for t in ties if any(t['id'].startswith(pref)for pref in ('cap_outer','cap_soffit','high_chang','high_nan','gable apex','oculus','near nanxun','second nanxun','upper center','lower center','right bevel','left bevel'))]
def ray(uv,j):
 v=Rs[j].T@np.linalg.solve(Ks[j],[*uv,1]);return v/np.linalg.norm(v)
rays=np.array([[ray(t[k],j)for j,k in enumerate(('city','named'))]for t in selected])
def project(x,eye,j):
 v=(np.asarray(x)-eye)@Rs[j].T@Ks[j].T;return v[...,:2]/v[...,2:3]
def unpack(t):return t[:3],t[3:6],t[6:14],t[14],t[15]
def residual(t,diagnose=False):
 c0,c1,params,hi,lo=unpack(t);rr=ring(params);es=[c0,c1];parts={}
 parts['independent_stations']=((params-meas)/[.42,1.25,.8,.8,.7,.7,1.05,.55]).tolist()
 parts['station_widths']=((np.linalg.norm(np.diff(rr[1:5],axis=0),axis=1)-np.linalg.norm(np.diff(stationXY[1:5],axis=0),axis=1))/.31).tolist()
 for j,eye in enumerate(es):
  vert=[];bands_r=[]
  for i,x,y,sigma in horizontal[j]:
   a,b=project([[*rr[i],1],[*rr[i],15]],eye,j);u=a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1]);vert.append((u-x)/sigma)
  for k,height in enumerate([hi,lo]):
   # On-image x/y at each arris are relative to the wall just below its coping.
   q=project(np.c_[rr[1:5],np.full(4,height)],eye,j)
   bands_r.extend(((q-bands[j][k])/[5.5 if j==0 else 2.8,4.0 if j==0 else 2.3]).flatten())
  parts['verticals_'+str(j)]=vert;parts['corner_bands_'+str(j)]=bands_r
 rel=c1-c0;errors=[]
 for (a,b),t in zip(rays,selected):
  ds=np.linalg.lstsq(np.stack([a,-b],axis=1),rel,rcond=None)[0];q=(c0+a*ds[0]+c1+b*ds[1])*.5
  for j,key in enumerate(['city','named']):errors.extend((project(q,es[j],j)-t[key])/(2.4 if j==0 else 1.4))
 parts['independent_two_image_ties']=errors
 # Pavement datum. Do not use the top of the wall base as the street height.
 f0=rr[0];fn=rr[1]-rr[0];fn=fn[::-1]*[1,-1];fn/=np.linalg.norm(fn)
 foot=[]
 for xy,sigma in [([322,865],.125),([278,858],.14),([65,824],.24)]:
  v=ray(xy,0);xyz=c0+v*(fn@(f0-c0[:2])/(fn@v[:2]));foot.append(xyz[2]/sigma)
 parts['pavement']=foot
 return {k:list(map(float,v))for k,v in parts.items()}if diagnose else np.concatenate([np.asarray(v) for v in parts.values()])
sol=least_squares(residual,[-5,-16,1.9,-5,-9,1.6,*meas,11.9,2.8],loss='soft_l1',f_scale=1,x_scale='jac',max_nfev=650)
e0,e1,plan,hi,lo=unpack(sol.x);points=ring(plan);print('eyes, shape',e0,e1,points.round(3).tolist(),hi,lo)
print('station difference',np.linalg.norm(points-stationXY,axis=1).round(3))
for k,v in residual(sol.x,True).items():print(k,np.median(abs(np.asarray(v))).round(3),np.max(abs(np.asarray(v))).round(3))
o=json.loads((p/'owner-ring.json').read_bytes());ids=['changzhi','corner-changzhi','corner-center','corner-nanxun','nanxun'];faces=[]
for id,a,b in zip(ids,points,points[1:]):
 v=b-a;length=np.linalg.norm(v);faces.append(dict(id=id,a=a.tolist(),b=b.tolist(),length=float(length),out=(v[::-1]*[1,-1]/length).tolist()))
layout=dict(status='Two street photographs registered jointly to independent ground rays',city_eye=e0.tolist(),named_eye=e1.tolist(),origin_wgs84=anchor.tolist(),nanxun_bearing_degrees=float(np.rad2deg(bearing)),angle_degrees=110.16,faces=faces,low_fascia=float(lo),upper_fascia=float(hi),ground_frontage_state='district-2023',units='metres',back_points=[local(ll).tolist()for ll in reversed(o['original'][3:9])])
(p/'bundle-street-layout.json').write_text(json.dumps(layout,indent=2)+'\n')
(p/'bundle-residuals.json').write_text(json.dumps(dict(city_photo=cams[0]['source_sha256'],named_photo=cams[1]['source_sha256'],photo_ties=selected,point_names=['southwest','A','B','C','D','northwest'],city_and_named_vertical_observations=horizontal,city_and_named_continuous_band_observations=bands,independent_plan_xy_m=stationXY.tolist(),fitted_plan_xy_m=points.tolist(),station_misses_m=np.linalg.norm(points-stationXY,axis=1).tolist(),residuals_in_declared_uncertainty_units=residual(sol.x,True)),indent=2)+'\n')
