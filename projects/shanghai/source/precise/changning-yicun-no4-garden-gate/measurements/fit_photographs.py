"""Register two independent published camera views against the gate and the gable."""
from pathlib import Path
import json,math
import numpy as np
from scipy.optimize import least_squares

# Original coordinates in the two photographs (publication year, not shutter date).
A = (600,347)
B = (640,426)
# Name, plane/feature, xB,yB, xA,yA, used in fit.
anchors=[
 ('gate_seam','gate',303,210,114,223,True),
 ('right_jamb','gate',407,211,237,230,True),
 ('right_pier_cap_inner','gate',402,185,234,208,True),
 ('right_pier_cap_outer','gate',466,184,301,205,True),
 ('door_number','gate',439,219,273,241,False),
 ('door_number_top_left','gate',426,210,260,231,True),
 ('door_number_lower_right','gate',450,228,286,251,False),
 ('east_panel_lower_left','gate',466,264,302,280,True),
 ('gable_upper_vent','house',352,113,157,67,True),
 ('gable_lower_left_vent','house',345,119,149,76,False),
 ('gable_lower_right_vent','house',359,120,165,77,False),
 ('steel_sash_upper_left','house',325,136,123,102,True),
 ('steel_sash_upper_right','house',377,137,188,103,True),
 ('air_conditioner_round_fan','house',394,170,208,147,False),
]
def axes(yaw,pitch):
 a=math.radians(yaw); b=math.radians(pitch)
 f=np.array([math.sin(a)*math.cos(b),math.cos(a)*math.cos(b),math.sin(b)])
 right=np.array([math.cos(a),-math.sin(a),0.]);return f,right,np.cross(right,f)
def ray(uv,size,focal,eye,yaw,pitch,depth):
 f,r,u=axes(yaw,pitch);v=f+r*(uv[0]-size[0]/2)/focal-u*(uv[1]-size[1]/2)/focal
 return eye+v*(depth-eye[1])/v[1]
def project(x,size,focal,eye,yaw,pitch):
 f,r,u=axes(yaw,pitch);y=x-eye;return np.array(size)/2+focal*np.array([y@r,-y@u])/(y@f)
def fit(depth):
 # The 2023 station is the reference local frame. The gate opening is normalized
 # to approx. 2.3m, with a 1.55m eye and a nominal 52.3 degree horizontal lens.
 # The height and baseline are working assumptions, not reported field measures.
 eb=np.array([.18,-7.04,1.55]); fb=650.;yb,pb=0.,4.12
 def world(x):return ray(x[2:4],B,fb,eb,yb,pb,0. if x[1]=='gate' else depth)
 def resid(t):
  ea=np.array(t[:3]);f,y,p=t[3:]
  raw=[project(world(q),A,f,ea,y,p)-np.array(q[4:6])for q in anchors if q[-1]]
  return np.r_[np.array(raw).ravel(),(f-680)/120,(ea[2]-1.55)/.35]
 s=least_squares(resid,(-.5,-6.8,1.55,680,12,7),bounds=([-8,-14,.6,390,-48,-18],[8,-2.5,3.3,1050,48,32]),loss='soft_l1',f_scale=3)
 ea=np.array(s.x[:3]);fa,ya,pa=s.x[3:]
 def cam(e,f,y,p,dim):
  fwd,rr,uu=axes(y,p);rot=np.stack((rr,-uu,fwd));K=np.array([[f,0,dim[0]/2],[0,f,dim[1]/2],[0,0,1.]])
  return {'eye_m':e.tolist(),'target_m':(e+fwd*12).tolist(),'focal_px':f,'layout':dim,'yaw_deg':y,'pitch_deg':p,'horizontal_fov_degrees':math.degrees(2*math.atan(dim[0]/(2*f))),'projection_3x4':(K@np.column_stack((rot,-rot@e))).tolist()}
 result=[]
 for q in anchors:
  x=world(q);a=project(x,A,fa,ea,ya,pa);result.append(dict(feature=q[0],plane=q[1],source_2023=q[2:4],source_2021=q[4:6],used=q[-1],world_m=[round(k,5) for k in x],projection_2021_px=a.round(2).tolist(),error_px=round(np.linalg.norm(a-q[4:6]),2)))
 return {'house_plane_behind_gate_m':depth,'stations':{'press-2023':cam(eb,fb,yb,pb,B),'shangguan-2021':cam(ea,fa,ya,pa,A)},'anchors':result,'training_rms_2021_px':round(math.sqrt(np.mean([q['error_px']**2 for q in result if q['used']])),2),'held_out_rms_2021_px':round(math.sqrt(np.mean([q['error_px']**2 for q in result if not q['used']])),2)}
if __name__=='__main__':
 candidates=[fit(v) for v in (4.,6.,8.,10.,12.)];selected=candidates[2]
 selected['depth_sensitivity']=[{k:c[k]for k in ('house_plane_behind_gate_m','training_rms_2021_px','held_out_rms_2021_px')}for c in candidates]
 selected['interpretation']='Eight metre separation is an illustrative working depth for the two detached surfaces. Variable lenses, unknown camera stations and nearly frontal views leave scale and distance ambiguous. Compare the residuals over 4–12 m; they do not measure the actual depth.'
 p=Path(__file__).with_name('two-photograph-registration.json');p.write_text(json.dumps(selected,indent=2,ensure_ascii=False)+'\n');print(selected['depth_sensitivity'])
