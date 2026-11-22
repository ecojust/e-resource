"""Calibrate the 2022 corner entrance plane from its photographed semicircle, radial web and sill."""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

W=Path(__file__).resolve().parents[1]
m=json.loads((W/'measurements/2022-fanlight-members.json').read_bytes())['members']
outer=np.asarray(m[0]['centreline']);vertical=np.asarray(m[3]['centreline'])
a,b=outer[0],outer[-1];hub=vertical[0];crown=vertical[-1]
# The 2019 wide exposure gives a nominal span of 3.72 m for the fan within
# the approximately 10.33 m entrance cut across the named OSM footprint. The mesh is not a
# surveyed building. The focal length comes from the 2022 Huawei EXIF.
RADIUS=1.86
SIZE=(7296,5472);f=np.hypot(*SIZE)*27/np.hypot(36,24);K=np.array([[f,0,SIZE[0]/2],[0,f,SIZE[1]/2],[0,0,1.]])
base=np.array([[1,0,0],[0,0,-1],[0,1,0.]])
def matrices(par):
    rotation=Rotation.from_rotvec(par[:3]).as_matrix()@base
    camera=K@rotation
    return np.stack((camera[:,0],camera[:,2],K@par[3:]),axis=1),camera[:,1]
def unpack(H,pts):
    rays=np.column_stack((pts,np.ones(len(pts))));raw=np.linalg.solve(H,rays.T).T;return raw[:,:2]/raw[:,2,None]
def residual(par):
    h,_=matrices(par);xz=unpack(h,outer[::3]);refs=unpack(h,np.array([a,b,hub,crown]))
    length=np.linalg.norm(xz,axis=1)-RADIUS
    expected=np.array([[-RADIUS,0.],[RADIUS,0.],[0.,0.],[0.,RADIUS]])
    edges=refs-expected
    return np.r_[length/.009,edges.ravel()/.005]
t0=f*2*RADIUS/(b[0]-a[0]);start=[0.,0.,0.,(hub[0]-SIZE[0]/2)*t0/f,(hub[1]-SIZE[1]/2)*t0/f,t0]
fit=least_squares(residual,start,loss='soft_l1',max_nfev=450,xtol=1.e-12,ftol=1.e-12)
H,D=matrices(fit.x);old_grade=unpack(H,np.array([[278.*SIZE[0]/690.,394.*SIZE[0]/690.]]))[0,1]
wall=H.copy();wall[:,2]+=wall[:,1]*old_grade
ring=unpack(H,outer);deviation=1000*(np.linalg.norm(ring,axis=1)-RADIUS)
d=dict(photo_sha256='e3c32ee79cb3203236105cf72483c2e9df6d0013f52eba0b35a4ecedb52d9faf',nominal_spring_diameter_m=2*RADIUS,spring_height_m=round(float(-old_grade),4),normalized_frame_median_radial_difference_mm=round(float(np.median(abs(deviation))),3),normalized_frame_p95_radial_difference_mm=round(float(np.percentile(abs(deviation),95)),3),street_plane_homography=wall.tolist(),positive_depth_axis=D.tolist(),focal_length_px=float(f),focal_length_35mm_exif=27,original_size=SIZE,inputs=dict(left_spring=a.tolist(),right_spring=b.tolist(),mullion_base=hub.tolist(),mullion_crown=crown.tolist(),nominal_grade_pixel=[278.*SIZE[0]/690.,394.*SIZE[0]/690.]),source_scale='The two short chamfers total 10.458 m and their endpoint chord is approximately 10.33 m. Depending on the breaks used on the angled 2019 overview, the fan spans about 0.34–0.38 of the entrance frontage, giving a nominal 3.72 m diameter within that range. Depth and height dimensions are inferred from single-view registration, independent of the phone location tag.')
(W/'measurements/2022-entrance-registration.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print(fit.success,d['spring_height_m'],d['normalized_frame_median_radial_difference_mm'],d['normalized_frame_p95_radial_difference_mm'],fit.x)
