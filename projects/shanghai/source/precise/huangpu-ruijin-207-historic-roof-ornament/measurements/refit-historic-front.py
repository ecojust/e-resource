"""Recover the historical exterior plane from three visible storeys and the original column lines."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares

P=Path(__file__).resolve().parents[1]
M=P/'measurements'
def put(f,j):f.write_text(json.dumps(j,indent=2)+'\n')
h=[[[74,69],[933,233]], [[49,130],[950,274]], [[155,281],[647,325]], [[682,331],[915,353]], [[158,414],[551,425]], [[685,431],[912,436]], [[157,485],[256,485]], [[277,485],[369,485]], [[388,485],[467,485]], [[568,215],[648,229]]]
# The rear window heads, spandrels and parapet have different physical heights. Each pair is one continuous period line.
v=[[[144,152],[149,533]],[[266,172],[270,525]],[[375,189],[384,516]],[[470,207],[481,511]],[[559,219],[573,501]],[[665,234],[677,497]],[[735,246],[749,488]],[[798,256],[810,481]],[[856,266],[869,479]],[[911,273],[923,469]]]
def fit(lines):
 obs=np.array(lines,float)
 def r(q):
  d=q-obs[:,0];d/=np.linalg.norm(d,axis=1)[:,None];n=np.column_stack((-d[:,1],d[:,0]))
  return np.sum((obs[:,1]-obs[:,0])*n,axis=1)
 x=least_squares(r,[2600,500] if lines is h else [-65,-11000],loss='soft_l1',f_scale=1.3)
 return x.x,r(x.x)
vx,ex=fit(h);vz,ez=fit(v);centre=np.array([510,353])
focal=float(np.sqrt(-np.dot(vx-centre,vz-centre)))
def axis(vp):
 d=np.r_[vp-centre,focal];return d/np.linalg.norm(d)
x=axis(vx);z=axis(vz);y=np.cross(z,x);y/=np.linalg.norm(y)
R=np.column_stack((x,y,z));origin=np.array([598,170])
K=np.array([[focal,0,centre[0]],[0,focal,centre[1]],[0,0,1]])
t=np.linalg.solve(K,[*origin,1])
def camera(d):
 return K@np.column_stack((R,t*d))
def on(m,u,v):
 return np.linalg.solve((m[:2]-np.array([[u],[v]])*m[2])[:,[0,2]],(np.array([u,v])*m[2,3]-m[:2,3]))
m=camera(1);A=np.vstack([on(m,594,r) for r in [213,316,419]])
d=3.5/np.mean(-np.diff(A[:,1]));m=camera(d)
obs=dict(source_url='https://www.hpcbristol.net/visual/Ro-s018',native_raster=[1020,706],source_sha256='8a22ced1ee705ff3a087edd39036a4027824dff0fb40e4d3d2b0d85787067a61',origin_px=origin.tolist(),horizontal_line_ends_px=h,vertical_column_generators_px=v,period_u_px=594,three_window_head_rows_px=[213,316,419],estimated_storey_height_m=3.5,scale_sensitivity_m=[3,4],projection_fit='Pinhole camera with square pixels, zero skew and the optical centre at the print centre. Fit two vanishing points to independently traced horizontal elements and columns. The printed crop and the floor-to-floor height are uncertain.',horizontal_vanishing_point=vx.tolist(),vertical_vanishing_point=vz.tolist(),horizontal_signed_residual_px=ex.tolist(),vertical_signed_residual_px=ez.tolist(),focal_px=focal,shared_local_axes='X along the visible long facade to the right of the photograph, Y inward, Z up. Origin is the roof crest at original pixel (598,170). Ground elevation is not measured.',projection=m.tolist(),sample_storey_heights_m=(-np.diff(np.vstack([on(m,594,r) for r in [213,316,419]])[:,1])).tolist())
put(M/'rosholt-long-front-registration.json',obs)
print(vx,vz,ex,ez,obs['sample_storey_heights_m'],focal,d)
