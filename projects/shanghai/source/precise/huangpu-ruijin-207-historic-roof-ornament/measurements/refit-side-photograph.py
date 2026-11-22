"""Reconstruct the short return visible only in the independently catalogued second image."""
import numpy as np,json,sys
from pathlib import Path
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'source'))
from rosholt_front_plane import on_face

def xyz_rect(u,v):return [(u-736)/32,0,(128-v)/32]
# Actual homologues are the heads of successive front piers, vents in unoccluded bays and the middle dark window.
controls=[]
for px,xy in zip([170,296,422,548,674,848,974,1100,1229,1356],[(306,83),(365,102),(414,117),(456,129),(499,143),(543,156),(572,165),(598,174),(621,183),(640,188)]):
 controls.append(('pier head',xyz_rect(px,182),xy))
for u,x,y,z in [(348,382,167,275),(471,429.5,178,275),(593,470,187,277),(705,503,194,277),(783,525,199,277),(889,553,204,278),(1014,583,210,278),(348,381,309,495),(471,430,312,495),(593,470,315,495),(889,554,319,497)]:
 controls.append(('vent or dark masonry inset',xyz_rect(u,z),(x,y)))
for uv,xy in [((581,422),(500,264)),((650,424),(528,266))]:
 controls.append(('dark central infill head',on_face(uv).tolist(),xy))
pts=np.array([v[1] for v in controls]);uv=np.array([v[2] for v in controls])
# Plane homography initializes a perspective camera. The side-wall vanishing direction supplies depth.
M=[]
for (x,y,z),(u,v) in zip(pts,uv):
 M.extend([[x,z,1,0,0,0,-u*x,-u*z,-u],[0,0,0,x,z,1,-v*x,-v*z,-v]])
_,_,vt=np.linalg.svd(M);hom=vt[-1].reshape(3,3)
if hom[2,2]<0:hom*=-1
K=np.array([[590,0.,344],[0,590,219.5],[0,0,1]])
cols=np.linalg.solve(K,hom);scale=(np.linalg.norm(cols[:,0])+np.linalg.norm(cols[:,1]))/2
rx,rz,t=cols.T/scale;rm=np.column_stack((rx,np.cross(rz,rx),rz));U,_,V=np.linalg.svd(rm);rot=Rotation.from_matrix(U@V)
lines=[[[184,80],[93,124]],[[181,166],[100,193]],[[181,251],[135,256]]]
def params(p):
 mat=Rotation.from_rotvec(p[:3]).as_matrix()
 k=np.array([[p[6],0,p[7]],[0,p[6],p[8]],[0,0,1.]])
 return k@np.column_stack((mat,p[3:6]))
def res(p):
 proj=params(p);q=proj@np.c_[pts,np.ones(len(pts))].T
 out=(q[:2]/q[2]-uv.T).T.ravel().tolist()
 vp=proj[:,1];vp=vp[:2]/vp[2]
 for a,b in np.array(lines):
  axis=vp-a;axis/=np.linalg.norm(axis)
  out.append(4*np.cross(np.r_[b-a,0],np.r_[axis,0])[2])
 out.extend([(p[7]-344)/65,(p[8]-219.5)/65]);return np.array(out)
p=least_squares(res,np.r_[rot.as_rotvec(),t,590,344,219.5],loss='soft_l1',f_scale=1.1,max_nfev=2500).x
m=params(p)
def axis(u,v,i,value):
 eq=m[:2]-np.array([[u],[v]])*m[2];indices=[j for j in range(3) if j!=i]
 vv=np.linalg.solve(eq[:,indices],-eq[:,3]-value*eq[:,i]);o=np.zeros(3);o[indices]=vv;o[i]=value;return o
def out_uv(x):
 w=m@np.r_[x,1];return w[:2]/w[2]
corner_a=axis(185,79,1,0)
corner_b=axis(183,326,1,0)
# At this view the blank rendered corner includes a shallow return along each street. Its arris is at x≈197 in the print.
end_a=axis(184,80,2,-1.70);end_b=axis(93,124,2,-1.70);corner=np.mean([end_a,end_b],axis=0);print('return observed endpoints',end_a,end_b)
print('RMS/reprojection',np.sqrt(np.mean(res(p)**2)),p[6], 'near end',corner_a,corner_b,corner,'side far',axis(94,123,0,corner[0]))
print([(v[0],(out_uv(v[1])-v[2]).round(2))for v in controls])
J=dict(source_url='https://wiki.histoire-chine.fr/images/5/5f/Le_Laboratoire_Municipal_avant_de_devenir_Institut_Pasteur_entre_1934_et_1938.jpg',source_sha256='0e64591c5af1d512c7549152c7af8e28925d1ab3091c3a5cd7ba09338eb62e29',native_raster=[688,439],historic_source_caption='Le Laboratoire Municipal avant de devenir Institut Pasteur entre 1934 et 1938',controls=[dict(feature=k,primary_frame_xyz_m=pt,secondary_native_px=xy) for k,pt,xy in controls],short_return_lines_px=lines,secondary_camera_matrix=m.tolist(),secondary_focal_px=float(p[6]),rms_px=float(np.sqrt(np.mean(res(p)**2))),corners=dict(near_arris_px=[184,80],near_arris_x_m=float(corner[0]),near_eave_xyz_m=end_a.tolist(), far_eave_xyz_m=end_b.tolist(),far_end_px=[93,124]),scope='The two period photographs show the same parapets, nine longitudinal bays and the central dark infill. Relative dimensions use an estimated 3.50 m storey. The short return is directly visible in the second view. The unphotographed rear is not surveyed.')
(P/'measurements/historic-two-view-registration.json').write_text(json.dumps(J,indent=2)+'\n')
