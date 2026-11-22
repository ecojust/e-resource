"""Re-estimate the three camera poses and the 2026 wall homography from measured source pixels."""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

def fit(data):
    west=np.asarray(data['reference_px']['west']);east=np.asarray(data['reference_px']['east'])
    views=data['views']
    def directions(q):
        m,wx,mz,wz,b=q[:5];cx,cy=480.,360.
        return np.array([1+cx*wx/1000,m+cy*wx/1000,wx/1000]),np.exp(b)*np.array([mz+cx*wz/1000,-1+cy*wz/1000,wz/1000])
    def parameters(q):
        vx,vz=directions(q)
        a=(east[0]-west[0])/(vx[0]-east[0]*vx[2])/data['span_x_m']
        Q=np.column_stack((a*vx,a*vz,west-a*q[5]*vz))
        cameras={}
        for i,(name,obs) in enumerate(views.items()):
            k=6+i*6;rot=Rotation.from_rotvec(q[k:k+3]).as_matrix();eye=q[k+3:k+6]
            P=obs['K']@np.column_stack((rot,-rot@eye))
            cameras[name]=(P,eye)
        return Q,cameras
    def lines(line,d):
        x,y,u,v=line;delta=np.array([u-x,v-y]);mid=(np.array([x,y])+[u,v])/2
        direct=d[:2]-mid*d[2]
        return (delta[0]*direct[1]-delta[1]*direct[0])/np.linalg.norm(direct)
    def residual(q):
        Q,cameras=parameters(q);vx,vz=directions(q)
        residuals=[lines(l,vx)/.9 for l in data['reference_line_controls']['x']]
        residuals.extend(lines(l,vz)/.8 for l in data['reference_line_controls']['z'])
        for name,(P,eye) in cameras.items():
            obs=views[name];xy=np.asarray(obs['fit']);H=P[:,[0,2,3]]@np.linalg.inv(Q)
            dest=np.c_[xy[:,:2],np.ones(len(xy))]@H.T
            residuals.extend(((dest[:,:2]/dest[:,2:]-xy[:,2:])/1.15).ravel())
            residuals.append((eye[2]-obs['station_eye_height_m'])/.20)
        return residuals
    solved=least_squares(residual,data['seed_parameters'],loss='soft_l1',f_scale=1.25,max_nfev=125,x_scale='jac')
    Q,cameras=parameters(solved.x);result={'wall_XZ_to_frame':Q.tolist(),'datum_z':float(solved.x[5]),'views':{}}
    for name,(P,eye) in cameras.items():
        controls=np.asarray(views[name]['held']);H=P[:,[0,2,3]]@np.linalg.inv(Q)
        reprojected=np.c_[controls[:,:2],np.ones(len(controls))]@H.T
        error=np.linalg.norm(reprojected[:,:2]/reprojected[:,2:]-controls[:,2:],axis=1)
        result['views'][name]={'P':P.tolist(),'C':eye.tolist(),'heldout':len(error),'median_px':float(np.median(error)),'p90_px':float(np.percentile(error,90))}
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('result',type=Path)
    args=ap.parse_args();obs=Path(__file__).with_name('street-front-observations.json')
    args.result.write_text(json.dumps(fit(json.loads(obs.read_text())),indent=1)+'\n')
