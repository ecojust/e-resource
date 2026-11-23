"""Two-camera estimate of the balcony depth relative to the Dafuli gate fronts."""
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
import json
w=Path(__file__).parent
s=w
j=json.loads((s/'court-camera.json').read_bytes());K=np.array(j['camera_intrinsics']);R=np.array(j['R_world_to_image']);C=np.array(j['camera_centre'])
K=np.diag([950/4912,631/3264,1])@K
# A few edges are shared at the two front posts and the base of their boundary wall.
# These tie the reconstruction to the address plaque's provisional metre scale.
plane=[('rear gate coping left',(627,446),(409,255)),('far pier front at base',(659,614),(426,330)),
       ('masonry wall junction',(663,474),(429,271)),('wall at No4',(724,457),(450,264)),
       ('No4 badge centre',(734,449),(453,257)),('No4 cap front corner',(710,420),(443,248)),
       ('No3 pier front',(795,411),(477,265))]
free=[('chimney pots silhouette',(598,32),(405,40)),('quoined block street shoulder',(590,135),(399,98)),
      ('quoined block upper chimney corner',(602,54),(406,55)),('cross wing left window sill',(679,214),(440,142)),
      ('cross wing left window head',(673,158),(439,111)),('cross wing right sill',(726,216),(468,141)),
      ('cross wing right head',(724,157),(466,108)),('quoined block plinth sidewalk',(614,598),(397,322)),
      ('quoined block lower cornice',(613,383),(398,226))]
def ray(k,r,p):return r.T@np.linalg.solve(k,[*p,1])
def run(opt):
    k=np.array(opt['K']);r=np.array(opt['R']);rays={n:ray(K,R,p) for n,p,q in plane+free}
    def calc(v,output=False):
        cam=C+v[:3];rr=Rotation.from_rotvec(np.radians(v[3:])).as_matrix()@r
        def xy(pt):
            q=k@rr@(pt-cam);return q[:2]/q[2]
        residual=[];control=[]
        for name,p,q in plane:
            d=rays[name];a=C+d*(-C[1])/d[1];err=xy(a)-q
            control.append([name,*err]);residual.extend(err)
        for name,p,q in free:
            d=rays[name];d2=ray(k,rr,q)
            t=np.linalg.lstsq(np.column_stack([d,-d2]),cam-C,rcond=None)[0][0]
            err=xy(C+d*t)-q;residual.extend(err);control.append([name,*err])
        if output:return cam,rr,control
        return np.r_[residual,v[3:]/.48,v[2]/.15]
    start=[4.0,-.25,0.,0.,0.,0.]
    res=least_squares(calc,start,loss='soft_l1',f_scale=2.,bounds=([.3,-3.,-.45,-4,-4,-4],[12.,3.,.45,4,4,4]))
    cam,rr,ctrl=calc(res.x,True)
    def triang(p,q):
        d=ray(K,R,p);e=ray(k,rr,q);t,u=np.linalg.lstsq(np.column_stack([d,-e]),cam-C,rcond=None)[0]
        a=C+d*t;b=cam+e*u
        return ((a+b)/2).round(3).tolist(),round(float(np.linalg.norm(a-b)),3)
    landmarks=[('west end front top',(714,278),(444,185)),('near end front top',(802,178),(497,158)),
                ('near end front bottom',(813,250),(497,187)),('near end at wall',(879,176),(528,157)),
                ('west end at deck',(718,318),(444,207))]
    return dict(f35=opt['equiv'],C2=cam.tolist(),R2=rr.tolist(),adjust=res.x.tolist(),
                median_pixel_error=float(np.median(np.linalg.norm(np.array([v[1:] for v in ctrl]),axis=1))),controls=ctrl,
                features=[dict(name=n,first=p,second=q,point=triang(p,q)) for n,p,q in landmarks])
import argparse
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path);args=parser.parse_args()
opts=json.loads((w/'companion-camera-options.json').read_bytes())
out=[run(opt)for opt in opts]
args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
for d in out:print(d['f35'],np.round(d['C2'],2),round(d['median_pixel_error'],2),[(x['name'],x['point'][0][1],x['point'][1]) for x in d['features']])
