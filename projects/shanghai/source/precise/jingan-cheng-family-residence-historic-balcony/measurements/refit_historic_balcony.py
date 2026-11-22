"""Refit the 2018 and undated period street-elevation cameras from the numerical observations.

Run with Python, NumPy and SciPy. Both cameras refer to the nominal rail scale in
historic-balcony-upper-lines.json. The two printed historic photographs are
independent scans of one exposure. Only the larger scan is fitted here.
"""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

HERE=Path(__file__).resolve().parent

def read(name):
    return json.loads((HERE/name).read_text())

def unpack(q):
    r=Rotation.from_rotvec(q[:3]).as_matrix()
    k=np.array([[q[6],0.,q[7]],[0.,q[6],q[8]],[0.,0.,1.]])
    return k,r,k@np.column_stack((r,q[3:6]))

def project(p,xyz):
    xyz=np.atleast_2d(xyz)
    image=np.column_stack((xyz,np.ones(len(xyz))))@p.T
    return image[:,:2]/image[:,2,None]

def at_wall(p,uv,y):
    v=np.linalg.solve(np.column_stack((p[:,0],p[:,2],p[:,3]+y*p[:,1])),[*uv,1.])
    return np.array([v[0]/v[2],y,v[1]/v[2]])

def modern():
    data=read('historic-balcony-upper-lines.json')
    cap,foot=[np.array(data[k])for k in ('measured_cap_native','measured_sill_native')]
    groups={}
    for key,axis in [('X',0),('Z',2)]:
        segments=np.array(data['vanishing_lines'][key]['segments'])
        mid=segments.mean(axis=1)
        delta=segments[:,1]-segments[:,0]
        length=np.linalg.norm(delta,axis=1)
        normal=delta[:,[1,0]]*[1,-1]/length[:,None]
        visible=mid[:,1]<1520 if key=='X' else np.ones(len(mid),bool)
        groups[axis]=mid[visible],normal[visible],np.minimum(length[visible],160)
    def errors(q):
        k,r,p=unpack(q)
        out=[]
        for axis,(mid,normal,length) in groups.items():
            v=k@r[:,axis]
            rays=v[:2]-mid*v[2]
            out.extend(.7*length*(rays*normal).sum(1)/np.linalg.norm(rays,axis=1))
        for i,y in enumerate([0.,q[13],q[13],0.]):
            out.extend((project(p,[q[i+9],y,data['nominal_rail_height_m']])[0]-cap[i])/1.6)
            x=at_wall(p,foot[i],y)[0]
            out.append((project(p,[x,y,0])[0,1]-foot[i,1])/2.2)
        axes=[at_wall(p,uv,0)[0]for uv in data['window_axes_native']]
        out.append(sum(axes)/.002)
        out.extend([(q[6]-4180.)/200.,(q[7]-1724.5)/210.,(q[8]-1348.)/210.])
        return out
    q=least_squares(errors,data['approximate_start'],x_scale='jac',loss='soft_l1',
                    f_scale=1.5,ftol=1e-11,max_nfev=240).x
    return unpack(q)[-1]

def period():
    data=read('historic-balcony-period-controls.json')
    selected=[v for v in data['controls'] if v['fit']]
    xyz=np.array([v['xyz_m']for v in selected])
    uv=np.array([v['native_640']for v in selected])
    sigma=np.array([v['sigma']for v in selected])[:,None]
    def errors(q):
        r=(project(unpack(q)[-1],xyz)-uv)/sigma
        return np.r_[r.ravel(),(q[6]-670.)/360.,(q[7]-320.)/105.,(q[8]-220.)/100.]
    fits=[]
    for start in data['starting_camera_parameters']:
        q=least_squares(errors,start,x_scale='jac',max_nfev=500,loss='soft_l1').x
        if q[6]>0:
            fits.append((sum(np.log1p(errors(q)**2)),q))
    q=min(fits,key=lambda row:row[0])[1]
    return unpack(q)[-1]

if __name__=='__main__':
    points=np.array([[-1.,-.715,.5],[1.,0.,2.],[0.,-.118,4.]])
    for name,p,reference in [('2018',modern(),read('historic-balcony-cameras.json')['gao2018']),
                             ('period',period(),read('historic-balcony-period-camera.json'))]:
        difference=np.linalg.norm(project(p,points)-project(np.array(reference['P']),points),axis=1)
        assert max(difference)<.04,(name,difference)
        print(name,'maximum difference from the saved camera in pixels',max(difference))
