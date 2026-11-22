from pathlib import Path
import numpy as np,json
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
s=Path(__file__).resolve().parent
photo=json.loads((s/'204-front-metric-camera.json').read_text());h=np.array(photo['local_P'])[:,[0,2,3]];p=np.array(photo['local_P'])
xlines=[[1810,2713,2627,2599],[2612,2498,1857,2621],[1870,2477,2584,2338],[1900,1050,2547,722],[1855,936,2485,593],[1909,963,2475,663],[1807,877,2327,585],[2301,641,1835,900],[2082,2697,2491,2641],[1722,3924,1968,3966],[1968,1461,2138,1391],[2816,2101,2972,2064]]
zlines=[[1794,1947,1802,1401],[2692,1438,2651,957],[2816,3284,2835,3766],[1789,2357,1793,1961],[2640,1424,2598,1037],[2116,1895,2122,2155],[2887,3595,2900,3847],[2408,1806,2420,2016],[1753,761,1756,555],[2227,1028,2235,1224]]
def err_line(v,lines):
 ret=[]
 for a,b,c,d in lines:
  q=np.array([[a,b],[c,d]]);u=v-q.mean(axis=0);u/=np.linalg.norm(u);ret.append(np.dot(q[1]-q[0],[u[1],-u[0]])*.5)
 return ret
K=np.diag([4912*24/36,4912*24/36,1]);K[:2,-1]=[1632,2456.]
vx,vz=[least_squares(err_line,v,args=(ls,),loss='soft_l1').x for v,ls in (([-2900,3440],xlines),([1850,-6000],zlines))]
def xyz(v):return np.linalg.solve(K,[*v,1])
def unit(x):return x/np.linalg.norm(x)
rx=-unit(xyz(vx));rz=unit(xyz(vz));ry=np.cross(rz,rx)
U,sv,Vt=np.linalg.svd(np.column_stack((rx,ry,rz)));rot=Rotation.from_matrix(U@Vt)
def vec(v):q=K@v;return q[:2]/q[2]
def rp(r):
 mat=Rotation.from_rotvec(r).as_matrix();return err_line(vec(mat[:,0]),xlines)+err_line(vec(mat[:,2]),zlines)
R=Rotation.from_rotvec(least_squares(rp,rot.as_rotvec(),loss='soft_l1').x).as_matrix()
# Two dated photographs share the four tips, the frontmost inner opening and two granite jamb bottoms.
ref=[(657,1983),(767,1981),(1190,1970),(1300,1964),(592,2213),(1373,2177),(573,2857),(1442,2804)]
ob=[(1883,2730),(2010,2703),(2583,2641),(2752,2607),(1814,3045),(2848,2927),(1797,3805),(2897,3944)]
def inv(b):q=np.linalg.solve(h,[*b,1]);return np.array([q[0]/q[2],0,q[1]/q[2]])
X=np.array([inv(b)for b in ref]);ob=np.array(ob)
def proj(P,w):q=np.c_[w,np.ones(len(w))]@P.T;return q[:,:2]/q[:,2,None]
def tm(t):return K@np.column_stack([R,t])
z=least_squares(lambda t:(proj(tm(t),X)-ob).flatten(),[.4,5,11],loss='soft_l1',f_scale=8);P=tm(z.x);C=np.linalg.solve(P[:,:3],-P[:,3])
print('eye',C,'vanish',vx,vz,'reprojection',np.round(proj(P,X)-ob,1))
def plane(uv,y):
 A=P[:,[0,2,3]].copy();A[:,2]+=P[:,1]*y;q=np.linalg.solve(A,[*uv,1]);return np.array([q[0]/q[2],y,q[1]/q[2]])
# Front- and rear-facing edges at the lower right corner of the projecting two-storey bay.
rows=[]
for front,back in [((2568,2287),(2675,2313)),((2573,2329),(2705,2366)),((2520,1390),(2630,1432)),((2479,753),(2566,810))]:
 b=plane(back,.18)
 ff=plane(front,.18); delta=plane(front,1.18)-ff;dist=(b[2]-ff[2])/delta[2];a=ff+dist*delta
 rows.append(dict(front_native_px=front,return_native_px=back,rise_m=float(b[2]),lateral_m=float(b[0]-a[0]),return_m=float(b[1]-a[1])))
(s/'204-splayed-bay-oblique.json').write_text(json.dumps(dict(source='Gao Can 88, southern oblique 09. Same-site frontal 11 by Gao Yihan measured the opposite façade plane.',relative_coordinate_system=photo['local_origin'],camera_P_local=P.tolist(),camera_eye_local=C.tolist(),horizontal_native_px=xlines,vertical_native_px=zlines,depths=rows,observed_window_division='Three narrow lights separated by two stone mullions on both levels.',estimated_error_m=.15,control_residual_px=(proj(P,X)-ob).tolist(),method='Four level stone or metal return edges on the right cheek. Each return starts at the ordinary wall plane. Solving the near point on the same level lets lateral splay vary. The camera uses EXIF 16 mm (24 mm equivalent), the two facade vanishing directions, and the common lower pier and ogee controls.'),ensure_ascii=False,indent=2)+'\n')
