from pathlib import Path
import argparse
import json
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
s=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description='Fit a metric frontal camera from the original facade lines.')
parser.add_argument('--width', type=float, default=5.430858200810337, help='measured span between the terminal pier axes in metres')
parser.add_argument('--output',type=Path,default=s/'204-front-metric-camera.json')
args=parser.parse_args()
segments={'x':[[669,417,807,431],[857,771,1159,795],[834,825,1149,849],[737,857,1155,888],[982,1171,824,1164],[1195,952,1895,1001],[557,910,741,922],[1241,1102,1476,1116],[591,1521,457,1518],[1276,1940,599,1948],[707,1905,1366,1897],[1126,1980,836,1986],[351,2732,570,2717],[1382,2135,1555,2125],[1514,2478,1416,2484]],'z':[[354,2159,302,2780],[575,2868,592,2245],[1223,281,1287,749],[475,1068,435,1532],[587,535,558,907],[910,1455,921,1764],[1302,1578,1339,1873],[432,1580,408,1884],[1118,1458,1143,1761],[1217,415,1244,630],[518,539,498,755],[1221,1161,1240,1337],[1383,2245,1401,2397]]}
def error(v,lines):
 e=[]
 for ax,ay,bx,by in lines:
  a=np.array([ax,ay]);b=np.array([bx,by]);m=(a+b)*.5;u=v-m;u=u/np.linalg.norm(u);e.append(np.dot(b-a,[u[1],-u[0]])*.5)
 return e
vx,vz=[least_squares(error,seed,args=(segments[k],),loss='soft_l1',f_scale=.45).x for k,seed in [('x',[14000,1700]),('z',[750,-2000])]]
c=np.array([1000.,1504]);f=np.sqrt(-np.dot(vx-c,vz-c));K=np.array([[f,0,c[0]],[0,f,c[1]],[0,0,1]])
def unit(v):return v/np.linalg.norm(v)
rx=unit(np.linalg.solve(K,[*vx,1])); rz=unit(np.linalg.solve(K,[*vz,1]));ry=np.cross(rz,rx);rot=np.column_stack((rx,ry,rz))
wspan=args.width
a=np.array([433.,2866.]);b=np.array([1536.,2806.])
def project(P,X):
 v=P@np.r_[X,1];return v[:2]/v[2]
def proj(t):return K@np.column_stack((rot,t))
def res(t):return np.r_[project(proj(t),[0,0,0])-a,project(proj(t),[wspan,0,0])-b]
sol=least_squares(res,[-2.8,5.3,8.0]);P=proj(sol.x);G=P[:,[0,2,3]]
def lift(u):v=np.linalg.solve(G,[*u,1]);return v[:2]/v[2]
print('VP',vx,vz,'f',f,'grade/error',res(sol.x),'eye',-rot.T@sol.x)
for uv in [[573,2857],[1442,2804],[592,2213],[1373,2177],[986,2082],[600,1900],[1365,1890],[465,2141],[1213,295]]:print(uv,lift(uv))
jamb=json.loads((s/'204-four-stone-recesses.json').read_text());obs=json.loads((s/'204-front-and-soffit-edges.json').read_text())
d=dict(source='高亦寒拍摄的陕西北路204号正面',image_size=[2000,3008],meet_segments_px=segments,local_origin='Left of the last two street pier axes, standing on the public paving, X toward the right entrance pier and positive Y into the passage.',principal_point_px=c.tolist(),focal_px=f,width_m=wspan,vanishing_horizontal=vx.tolist(),vanishing_vertical=vz.tolist(),local_P=P.tolist(),apparent_grade_controls_px=[list(a),list(b)],ground_control_residual_px=res(sol.x).tolist(),camera_eye_local_m=(-rot.T@sol.x).tolist(),limitations='The pier feet lie behind street equipment. Estimated common centre of each facing and the adjacent grade give a scale conditional on the twelve-pier plan. Photographic control of relief is more precise than its absolute height.',crown_relief={'ogees':[list(map(lambda x:lift(x).tolist(),v)) for v in jamb['pointed_recesses_inner']],'centre':[lift(x).tolist() for x in jamb['centre_recess_inner']],'horizontal':[lift(x).tolist() for x in jamb['horizontal_profiles']],'jambs':[lift(x).tolist() for x in jamb['opening_jambs']],'front_edge':[lift([q['x'],q['outer_front_lower_edge_y']]).tolist() for q in obs['samples']],'inner_line_on_front_plane':[lift([q['x'],q['inner_soffit_line_y']]).tolist() for q in obs['samples']]})
args.output.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
