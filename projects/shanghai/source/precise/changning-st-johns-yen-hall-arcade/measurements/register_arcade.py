"""Fit four perspective cameras to the recorded arcade, sharing the same field scale and levels."""
from pathlib import Path
import json, numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
HERE=Path(__file__).resolve().parent
J=json.loads((HERE/'arcade-photo-observations.json').read_text())
labels=['deck','ground_apex','lower_floor','middle_apex','upper_floor','parapet','upper_apex','high_eave']
prior=np.array([.41,3.90,5.0,8.50,9.35,10.70,12.65,13.65])
W=J['front_width_m'];pitch=(W-1.16)/11
def x_for(k):return .58+np.asarray(k)*pitch-W/2
def start_camera(raw,levels):
    uv=np.array([r[2:]for r in raw['picks']]); x=x_for([r[0]for r in raw['picks']]); z=np.array([levels[labels.index(r[1])]for r in raw['picks']]); xyz=np.column_stack((x,np.zeros(len(x)),z))
    w,h=raw['size'];f=w*.95
    points=np.c_[x,z,np.ones(len(x))]
    un,vn=((uv-[w/2,h/2])/f).T
    A=np.concatenate((np.c_[points,points*0,-un[:,None]*points],np.c_[points*0,points,-vn[:,None]*points]))
    H=np.linalg.svd(A,full_matrices=False)[2][-1].reshape(3,3)
    if H[2,2]<0:H=-H
    H/=np.linalg.norm(H[:,0]);rx=H[:,0];rz=H[:,1];ry=np.cross(rz,rx);r0=np.column_stack((rx,ry,rz));u,_,v=np.linalg.svd(r0);R=u@v
    return list(Rotation.from_matrix(R).as_rotvec())+list(H[:,2])+[np.log(f),0.0,0.0]
def run():
    raw=list(J['stations'].values());keys=list(J['stations'])
    init=np.r_[prior[1:],*[start_camera(d,prior)for d in raw]]
    def evaluate(p,report=False):
        levels=np.r_[prior[0],p[:7]];res=[];out={}
        if not report:res.extend(((levels[1:]-prior[1:])/[1.7,2,3,3.0,3.1,4.0,4.0]).tolist())
        for i,d in enumerate(raw):
            q=p[7+i*9:16+i*9];r=Rotation.from_rotvec(q[:3]).as_matrix();t=q[3:6]; f=np.exp(q[6]);w,h=d['size']
            K=np.array([[f,0,w/2+w*q[7]],[0,f,h/2+h*q[8]],[0,0,1.]])
            pos=np.array([[x_for(v[0]),0,levels[labels.index(v[1])]]for v in d['picks']]);uv=np.array([v[2:]for v in d['picks']]);survey=(pos@r.T+t)@K.T;pred=survey[:,:2]/survey[:,2,None];delta=pred-uv
            res.extend(delta.ravel())
            for a,b in d['depth_lines']:
                line=np.cross([*a,1],[*b,1]);line=line/np.linalg.norm(line[:2]);direction=K@r[:,1];res.append((line@direction)/np.linalg.norm(direction[:2])*100)
            # Planar scenes only weakly constrain focal length. Model a bounded photographic field of view.
            res.extend([(np.log(f/w)-np.log(1.15))*2.4,q[7]*4,q[8]*3])
            if report:
                pix=np.linalg.norm(delta,axis=1);out[keys[i]]=dict(size=d['size'],R=r.tolist(),K=K.tolist(),P=(K@np.column_stack((r,t))).tolist(),C=(-r.T@t).tolist(),focal_px=f,median_px=float(np.median(pix)),max_px=float(np.max(pix)),errors=[{'feature':v[:2],'observed':v[2:],'predicted':pred[n].round(3).tolist(),'error':round(float(pix[n]),2)}for n,v in enumerate(d['picks'])])
        if report:return dict(parameters=dict(total_width_m=W,pitch_m=pitch,half_end_pier_m=.58,levels=dict(zip(labels,levels))),stations=out)
        return np.asarray(res)
    fit=least_squares(evaluate,init,loss='soft_l1',f_scale=2,max_nfev=400,x_scale='jac')
    book=evaluate(fit.x,True);dest=HERE/'arcade-registration.json';dest.write_text(json.dumps(book,indent=2)+'\n');print(book['parameters']);print([(k,round(v['focal_px'],1),round(v['median_px'],2),round(v['max_px'],2)) for k,v in book['stations'].items()])
if __name__=='__main__':run()
