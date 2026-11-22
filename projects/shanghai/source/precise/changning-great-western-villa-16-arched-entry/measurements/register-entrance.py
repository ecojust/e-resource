"""Calibrate the axes of the double brick entrance from brick courses, jambs and the door width."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
HERE=Path(__file__).absolute().parent
C=np.array([400.,300.])
LINES={
 0:[[23,377,82,380],[23,415,82,419],[23,545,82,549],[653,470,731,473],[653,554,731,558],[89,296,136,300],[634,326,756,333],[300,171,506,180]],
 1:[[118,568,146,554],[118,554,146,541],[118,541,146,529],[118,528,146,515],
    [605,545,625,558],[605,532,625,544],[605,518,625,529],[605,506,625,516]],
 2:[[128,356,101,596],[10,350,0,457],[631,374,633,582],[627,359,639,589],
    [277,355,264,598],[494,353,491,586],[307,348,295,565],[475,347,475,548]]}
# Rear structural openings are approximately 1.08 metres clear at the arch spring.
ANCHOR=np.array([[305.,342.],[476.,348.]])
def model(q):
    yaw,pitch,roll,f,d,u,v=q
    right=np.array([np.cos(yaw),np.sin(yaw),0.]);forward=np.array([-np.sin(yaw)*np.cos(pitch),np.cos(yaw)*np.cos(pitch),np.sin(pitch)])
    down=np.cross(forward,right);R=np.array([np.cos(roll)*right+np.sin(roll)*down,-np.sin(roll)*right+np.cos(roll)*down,forward])
    K=np.array([[f,0,C[0]],[0,f,C[1]],[0,0,1.]]);T=np.r_[([u,v]-C)/f,1]*d
    return K@np.column_stack([R,T]),-R.T@T
def project(P,pts):
    pts=np.atleast_2d(pts);q=np.c_[pts,np.ones(len(pts))]@P.T
    return q[:,:2]/q[:,2,None]
def plane(P,uv,axis,value):
    idx=[i for i in range(3)if i!=axis];a=np.atleast_2d(uv)
    H=np.column_stack([P[:,idx[0]],P[:,idx[1]],P[:,3]+value*P[:,axis]])
    t=np.c_[a,np.ones(len(a))]@np.linalg.inv(H).T;out=np.zeros((len(a),3))+value
    out[:,idx]=t[:,:2]/t[:,2,None];return out
def residual(q):
    P,_=model(q);r=[]
    for k,lines in LINES.items():
        for line in lines:
            a,b=np.asarray(line).reshape(2,2);d=b-a;t=P[:2,k]-(a+b)/2*P[2,k];t/=np.linalg.norm(t)
            r.append((d[0]*t[1]-d[1]*t[0])*.62)
    width=project(P,[[-.54,0,0],[.54,0,0]])-ANCHOR
    return np.r_[r,width.ravel(),(q[3]-647.1)/21.]
def solve_depth(P):
    # The sides reveal the same vertical planes at the front and back of the porch.
    corners=[[[253,229],[242,592]],[[128,320],[102,590]],[[523,225],[529,488]],[[626,355],[636,596]]]
    rear=[];front=[]
    for back,pier in zip(corners[::2],corners[1::2]):
        rear.append(np.mean(plane(P,back,1,0)[:,0]))
        front.append(np.mean(plane(P,pier,0,rear[-1])[:,1]))
    return rear,front
if __name__=='__main__':
    r=least_squares(residual,[-.055,.12,-.043,648,4.14,390,345],bounds=([-.32,-.05,-.13,578,2.9,380,337],[.32,.35,.13,735,5,400,354]),loss='soft_l1')
    P,eye=model(r.x);xs,ys=solve_depth(P)
    report=dict(photo_sha256='717c66fb616b82f01470ecf7869f2bf8e19de09c71a08dcabd48b13b6fe3de82',source_size=[4160,3120],working_size=[800,600],cameras_equivalent_mm=28,
        primary_mortar_and_jamb_lines=LINES,trial_residuals_px=r.fun.tolist(),parameters=r.x.tolist(),world_to_working=P.tolist(),eye_enu_m=eye.tolist(),rear_width_control=ANCHOR.tolist(),assumed_rear_open_door_width_m=1.08,
        outer_sidewall_width_limits_m=xs,independent_front_plane_estimates_m=ys,outer_front_y_m=float(np.mean(ys)),datum='后拱木门净口两侧的平均起拱高。两次进深估计来自照片上左右内侧墙分别在前后出现的竖棱。')
    assert all(y<-.30 for y in ys) and max(ys)-min(ys)<.45
    (HERE/'entrance-camera.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(r.x,eye,xs,ys,np.std(r.fun))
