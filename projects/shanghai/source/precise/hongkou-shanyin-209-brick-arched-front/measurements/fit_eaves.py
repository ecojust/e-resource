"""Fit the first common garden eave line in two photographs. Pass the first and second photographs and output JSON."""
from pathlib import Path
import json,numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import least_squares
from PIL import Image
import sys
folder=Path(__file__).resolve().parent
P=np.array(json.loads((folder/'garden-front-layout.json').read_bytes())['camera_P']);other=np.array(json.loads((folder/'second-photo-camera.json').read_bytes())['camera_P'])
second=np.asarray(Image.open(Path(sys.argv[2]))).astype(float).mean(2);first=np.asarray(Image.open(Path(sys.argv[1]))).astype(float).mean(2)
def fitline(pts):
 uv=np.asarray(pts);fit=least_squares(lambda c:c[0]*uv[:,0]+c[1]-uv[:,1],[.08,59.],loss='soft_l1',f_scale=.7);return fit.x
out=[]
for u in range(18,202,3):
 guess=.085*u+57.;lo=int(guess)-5;hi=int(guess)+6;gr=np.gradient(gaussian_filter1d(second[:,u],.7));v=lo+np.argmin(gr[lo:hi])
 if gr[v]<-15:out.append([u,v])
ab=fitline(out);print('secondary front edge',len(out),ab)
uv1=[]
for u in range(570,965,3):
 gr=np.gradient(gaussian_filter1d(first[:,u],1.))
 l=422;v=l+np.argmin(gr[l:435])
 if gr[v]<-10:uv1.append([u,v])
aa=fitline(uv1);print('primary',len(uv1),aa)
def point(u,v,y):
 m=P[:2]-np.array([u,v])[:,None]*P[2]
 x,z=np.linalg.solve(m[:,[0,2]],-m[:,1]*y-m[:,3]);return [x,y,z]
def residual(depth,du=0):
 xz=np.array([point(u,aa[0]*u+aa[1],depth[0])for u in np.arange(370,965,35)])
 pix=xz@other[:,:3].T+other[:,3];pix=pix[:,:2]/pix[:,2:]
 return pix[:,1]-(pix[:,0]*ab[0]+ab[1]+du)
depth=least_squares(residual,[-1.]);estim=[]
for shift in [-2.5,0,2.5]:
 y=least_squares(residual,[-1],args=(shift,)).x[0];estim.append(y)
z=point(626.5,aa[0]*626.5+aa[1],depth.x[0])[2]
print('y',depth.x,'z',z,'band',estim)
Path(sys.argv[3]).write_text(json.dumps({'primary_controls':uv1,'secondary_controls':out,'first_line':aa.tolist(),'second_line':ab.tolist(),'front_eave_y':depth.x[0],'front_eave_z':z,'depth_at_2_5px_datum_shift':estim,'cross_projection_rms_px':float(np.mean(depth.fun**2)**.5)},indent=1,default=lambda value:value.item()))
