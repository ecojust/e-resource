"""Register the short front from the press oblique and two independently recorded street views."""
import json
from pathlib import Path
import sys

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

HERE=Path(__file__).absolute().parent
sys.path.insert(0,str(HERE.parent/'source'))
from build_model import PIX, surface_point

# Corners are clockwise, starting at the upper left in the image.
READINGS={
    'street-front-2020':{
        'upper-west':[[263,141],[298,134],[300,166],[262,173]],
        'lower-west':[[257,228],[298,223],[298,268],[255,271]],
        'upper-center':[[335,127],[401,114],[408,158],[338,172]],
        'lower-center':[[342,204],[418,195],[428,259],[345,266]],
        'upper-east':[[448,106],[497,96],[508,130],[456,139]],
        'lower-east':[[478,205],[531,198],[548,253],[491,259]]},
    'street-corner-2020':{
        'upper-west':[[252,91],[275,107],[274,144],[249,128]],
        'lower-west':[[243,203],[270,214],[269,263],[240,252]],
        'upper-center':[[300,123],[325,142],[326,180],[299,163]],
        'lower-center':[[300,219],[325,230],[325,277],[298,265]],
        'upper-east':[[348,159],[361,170],[361,200],[347,192]],
        'lower-east':[[348,254],[362,260],[361,293],[347,286]]}}
STATIONS={
    'press-oblique':([640,426],[-12,-15,1.5],[5.,0.,7.],480,None),
    'street-front-2020':([550,470],[2.8,-9.,2.32],[5.,0.,6.1],275,275),
    'street-corner-2020':([550,430],[-6.,-8.,2.32],[4.,0.,6.5],275/np.tan(np.deg2rad(34)),275/np.tan(np.deg2rad(34)))}

def fit(name,settings):
    frame,initial_eye,target,f0,fixed=settings
    source=PIX if name=='press-oblique' else READINGS[name]
    xyz=[];uv=[];labels=[];held=[]
    for key in READINGS['street-front-2020']:
        for i,(p,q) in enumerate(zip(PIX[key],source[key])):
            x,z=surface_point(p);xyz.append([x,0,z]);uv.append(q);labels.append(f'{key}-{i+1}')
            held.append((key,i) in {('upper-center',0),('lower-west',2),('upper-east',2),('lower-center',3),('upper-west',1)})
    xyz=np.asarray(xyz);uv=np.array(uv);keep=~np.array(held)
    e=np.array(initial_eye);fwd=np.array(target)-e;fwd/=np.linalg.norm(fwd)
    side=np.cross(fwd,[0,0,1]);side/=np.linalg.norm(side)
    rv=Rotation.from_matrix([side,np.cross(fwd,side),fwd]).as_rotvec()
    def camera(param):
        c=param[:3];R=Rotation.from_rotvec(param[3:6]).as_matrix();f=fixed or np.exp(param[6])
        K=np.array([[f,0,(frame[0]-1)/2],[0,f,(frame[1]-1)/2],[0,0,1]])
        P=K@np.column_stack([R,-R@c]);v=xyz@P[:,:3].T+P[:,3]
        return c,R,K,P,v[:,:2]/np.maximum(.01,v[:,2,None])
    def residual(v):
        c,_,_,_,q=camera(v)
        return np.r_[((q-uv)[keep]/2).ravel(),(c[2]-initial_eye[2])/.37,(v[6]-np.log(f0))/.22]
    p=least_squares(residual,np.r_[e,rv,np.log(f0)],max_nfev=750,loss='soft_l1').x
    c,R,K,P,q=camera(p);err=np.linalg.norm(q-uv,axis=1)
    return dict(size=frame,C=c.tolist(),R=R.tolist(),K=K.tolist(),P=P.tolist(),fit_rms_px=float(np.sqrt(np.mean(err[keep]**2))),held_rms_px=float(np.sqrt(np.mean(err[~keep]**2))),controls={k:dict(xyz=v.tolist(),pixel=pt.tolist(),predicted=a.tolist(),residual_px=float(d),holdout=bool(h))for k,v,pt,a,d,h in zip(labels,xyz,uv,q,err,held)})

if __name__=='__main__':
    stations={}
    for key,v in STATIONS.items():
        stations[key]=r=fit(key,v)
        print(key,np.round(r['C'],2),round(r['fit_rms_px'],2),round(r['held_rms_px'],2))
    (HERE/'three-front-stations.json').write_text(json.dumps(stations,ensure_ascii=False,indent=2)+'\n')
