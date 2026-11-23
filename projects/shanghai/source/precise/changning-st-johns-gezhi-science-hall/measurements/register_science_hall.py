"""Recover two oblique cameras and a metric frontal reference from matched architectural features."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
HERE=Path(__file__).resolve().parent

def homography(a,b):
    rows=[]
    for (x,y),(u,v) in zip(a,b):
        rows.extend([[x,y,1,0,0,0,-u*x,-u*y,-u],[0,0,0,x,y,1,-v*x,-v*y,-v]])
    h=np.linalg.svd(rows,full_matrices=False)[2][-1].reshape(3,3)
    return h/h[2,2]

def transform(h,p):
    a=np.c_[p,np.ones(len(p))]@h.T
    return a[:,:2]/a[:,2,None]

def fit():
    book=json.loads((HERE/'front-observations.json').read_bytes());pairs=book['control_pairs'];a=[r for r in pairs if r['station']=='school-aerial'];h=homography([r['uv']for r in a],[r['front']for r in a]);ends=transform(h,book['aerial_outer_edges_at_middle_sill'])[:,0]
    # The middle cornice deviates by less than a pixel from the horizontal through the seven visible bays.
    s=book['west_front_length_m']/np.diff(ends)[0]; xref=323.; vertical=book.get('effective_vertical_to_horizontal_scale',1.); zref=book['quoted_ground_level_v'];stations={}
    for name,(w,height) in book['stations'].items():
        fx=900. if name=='west-school-ground' else w*1.15;u0,v0=(w-1)/2,(height-1)/2
        sample=[r for r in pairs if r['station']==name];qv=np.array([r['uv']for r in sample])
        if name=='west-school-ground':
            cond=book.get('frontal_depth_condition',{});fx=cond.get('stand_off_m',s*fx)/s;v0=zref-cond.get('eye_z_m',(zref-v0)*s*vertical)/(s*vertical)
            R=np.array([[1.,0,0],[0,0,-1],[0,1.,0]]);c=np.array([(u0-xref)*s,-s*fx,(zref-v0)*s*vertical]);t=-R@c;K=np.array([[fx,0,u0],[0,fx/vertical,v0],[0,0,1.]])
            errors=[]
        else:
            xz=np.array([[(r['front'][0]-xref)*s,(zref-r['front'][1])*s*vertical]for r in sample]);p=np.c_[xz[:,0],xz[:,0]*0,xz[:,1]];uv=(qv-[u0,v0])/fx;hf=homography(xz,uv);hf/=np.linalg.norm(hf[:,0]);R=np.c_[hf[:,0],np.cross(hf[:,1],hf[:,0]),hf[:,1]];uu,_,vv=np.linalg.svd(R);r=Rotation.from_matrix(uu@vv);start=np.r_[r.as_rotvec(),hf[:,2],np.log(fx),0.,0.]
            def project(q,details=False):
                R=Rotation.from_rotvec(q[:3]).as_matrix();t=q[3:6];f=np.exp(q[6]);K=np.array([[f,0,u0+q[7]],[0,f,v0+q[8]],[0,0,1.]]);uvw=(p@R.T+t)@K.T;projected=uvw[:,:2]/uvw[:,2,None];diff=projected-qv
                if details:return R,t,K,projected
                ray=K@R[:,1];verts=[]
                for a,b in book['depth_lines'][name]:
                    l=np.cross([*a,1],[*b,1]);verts.append(l@ray/np.linalg.norm(l[:2])/np.linalg.norm(ray[:2])*110.)
                return np.r_[diff.ravel(),verts,(q[6]-np.log(w*1.25))*5,q[7]/15,q[8]/15]
            q=least_squares(project,start,loss='soft_l1',f_scale=1.6,max_nfev=500,x_scale='jac');R,t,K,pred=project(q.x,True);errors=[dict(feature=r['key'],native_px=r['uv'],predicted=xy.round(3).tolist(),error_px=round(float(np.linalg.norm(xy-r['uv'])),3))for r,xy in zip(sample,pred)]
        residuals=[r['error_px']for r in errors];stations[name]=dict(size=[w,height],R=R.tolist(),C=(-R.T@t).tolist(),K=K.tolist(),P=(K@np.c_[R,t]).tolist(),controls=errors,median_px=float(np.median(residuals))if residuals else None,maximum_px=max(residuals)if residuals else None)
    results=dict(metres_per_reference_pixel=s,reference_centre_u=xref,reference_ground_v=zref,extent_reference_u=ends.tolist(),vertical_metres_per_reference_pixel=s*vertical,scope='Three approximate cameras. Frontal camera is the rectified-plane reference and is not an independent fitting residual. Ground elevation and camera-to-front distances are conditional.',stations=stations)
    (HERE/'science-registration.json').write_text(json.dumps(results,indent=2)+'\n');print(ends,s,[(k,r['median_px'],r['maximum_px'],r['C'])for k,r in stations.items()]);return results
class Camera:
    def __init__(self,station):
        raw=json.loads((HERE/'science-registration.json').read_bytes())['stations'][station];self.c=np.asarray(raw['C']);self.k=np.asarray(raw['K']);self.r=np.asarray(raw['R'])
    def ray(self,pixel):return self.r.T@np.linalg.solve(self.k,[*pixel,1.])
    def wall(self,pixel,depth=0.):
        ray=self.ray(pixel);return self.c+ray*((depth-self.c[1])/ray[1])
    def pixel(self,xyz):
        p=self.k@self.r@(np.asarray(xyz)-self.c);return p[:2]/p[2]
if __name__=='__main__':fit()
