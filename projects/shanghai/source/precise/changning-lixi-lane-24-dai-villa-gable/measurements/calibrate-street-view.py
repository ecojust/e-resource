"""Fit the 2018 image axes and scale on the central arched window of the Dai residence."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
m=Path(__file__).absolute().parent
C=np.array([(531-352)*697/410,(298.5-12)*740/435])
horizontal=[[255,22,505,39],[218,456,546,467],[258,388,506,396],[345,464,548,468]]
# These plumb edges span the street-level photograph. All are converted to the local gable chart.
vertical_full=[[694,402,709,581],[559,401,566,579],[657,420,668,548],[601,420,605,548],
               [475,266,476,324],[443,240,434,366],[686,249,692,332]]
vertical=[(np.array(v).reshape(2,2)-[352,12])*[697/410,740/435]for v in vertical_full]
def camera(q):
    yaw,pitch,roll=q[:3];focal,dist=q[3:5]
    right=np.array([np.cos(yaw),np.sin(yaw),0.])
    forward=np.array([-np.sin(yaw)*np.cos(pitch),np.cos(yaw)*np.cos(pitch),np.sin(pitch)])
    down=np.cross(forward,right)
    rot=np.array([np.cos(roll)*right+np.sin(roll)*down,-np.sin(roll)*right+np.cos(roll)*down,forward])
    K=np.array([[focal,0,C[0]],[0,focal,C[1]],[0,0,1.]])
    off=np.r_[(q[5:7]-C)/focal,1.]*dist
    return K@np.column_stack([rot,off]),-rot.T@off
def project(P,xyz):
    a=np.atleast_2d(xyz);q=np.column_stack([a,np.ones(len(a))])@P.T
    return q[:,:2]/q[:,2,None]
def residual(q):
    P,_=camera(q);err=[]
    for axis,lines in [(0,horizontal),(2,vertical)]:
        vp=P[:2,axis]/P[2,axis]
        for line in lines:
            p,r=np.asarray(line).reshape(2,2);t=vp-(p+r)*.5;t/=np.linalg.norm(t);d=r-p
            err.append((d[0]*t[1]-d[1]*t[0])/2.)
    width=project(P,[[-.5,0,0],[.5,0,0]])-[[344,429],[429,431]]
    return np.r_[err,width.ravel()/1.5,(q[3]-1339)/25,q[2]/.055]
if __name__=='__main__':
    r=least_squares(residual,[-.18,.37,0,1340,15.9,386.4,430],bounds=([-.9,.13,-.16,1250,12,378,422],[.65,.62,.16,1425,23,394,437]),loss='soft_l1')
    P,eye=camera(r.x);data=dict(photograph_sha256='c6630d75c5fcf710273b1ab932d3c2fe1c7a7a9d287e5428b3061f95c7d77834',
      working_size=[1062,597],source_size=[5312,2988],local_crop=[352,12,762,447],local_size=[697,740],rough_focal_35mm_equivalent=28,
      horizontal_control_segments=horizontal,vertical_control_full_px=vertical_full,central_spring_endpoints_local_px=[[344,429],[429,431]],
      assumed_central_opening_width_m=1.,parameters=r.x.tolist(),world_to_local=P.tolist(),eye_enu_m=eye.tolist(),
      residual_control_values=r.fun.tolist(),assumption='估计中央拱窗净宽1.00米。单张沿街照提供正面尺度，屋后长度及不能看见的墙厚保留为估计。')
    (m/'street-camera.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(r.x.round(3),eye.round(3))
