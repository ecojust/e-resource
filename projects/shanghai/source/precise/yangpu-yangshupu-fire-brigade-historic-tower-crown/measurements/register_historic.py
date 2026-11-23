"""Recover the local viewing transform of the two visible faces, using the historic image only."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

HERE = Path(__file__).parent
# Square envelope, unit shaft width. The upper lip projects 5% beyond each side.
WORLD = np.array([[-.55,-.55,1.80],[.55,-.55,1.80],[.55,.55,1.80],[-.55,-.55,1.73],[.55,-.55,1.73],[.55,.55,1.73]])
CORNICE = np.array([[528,115],[616,82],[671,123],[530,119],[616,90],[670,131]])
VERTICALS = [([.5,-.5],613,289),([-.5,-.5],533,285),([.5,.5],660,280)]
# These are manual silhouette / tone transitions in the published 1080 x 768 image.
FACE = {
    "front":{"eye":[[568,166],[584,160],[575,154],[575,172]],"field":[[550,243],[599,229],[598,286],[550,297]],
             "upper_moulding":[[555,218],[554,170],[556,159],[562,151],[569,144],[578,140],[585,143]],
             "stepped_foot":[[556,219],[586,211],[587,207],[588,206],[587,197],[584,192],[583,183],[576,178]]},
    "return":{"eye":[[628,164],[640,178],[633,158],[636,181]],"field":[[622,231],[656,249],[655,286],[622,295]],
              "upper_moulding":[[623,210],[624,161],[627,152],[632,150],[637,156],[644,168],[647,179]],
              "stepped_foot":[[624,215],[644,225],[646,222]]}
}
TOP = {"cornice_left":[567,48],"cornice_right":[637,39],"top_left":[572,31],"highest_edge":[595,20],"top_right":[620,23],"front_post_left":[579,44],"front_post_right":[595,39],"open_light_left":[586,51],"open_light_right":[610,49],"solid_apron":[594,73]}
def camera(a):
    R=Rotation.from_rotvec(a[:3]).as_matrix();K=np.array([[a[6],0,540],[0,a[6],384],[0,0,1]])
    return K@np.column_stack((R,a[3:6]))
def project(p,world):
    world=np.asarray(world); q=np.column_stack((world,np.ones(len(world))))@p.T
    return q[:,:2]/q[:,2:]
def plane(p,uv,side):
    c=1 if side=='front' else 0
    H=np.column_stack((p[:,1-c],p[:,2],p[:,3]+p[:,c]*(-.5 if side=='front'else .5)))
    s=np.linalg.solve(H,[*uv,1]);return s[:2]/s[2]
def residual(a,pixels=CORNICE):
    p=camera(a);out=list((project(p,WORLD)-pixels).flat)
    for xy,x,y in VERTICALS:
        ab=project(p,[xy+[0],xy+[2]]); k=np.argsort(ab[:,1])
        out.append(np.interp(y,ab[k,1],ab[k,0])-x)
    for side,uv in [('front',(576,166)),('return',(635,170))]:
        out.append(13*plane(p,uv,side)[0])  # weak centred-eye prior, in native pixels
    return out
def solve(points=CORNICE):
    seed=[1.4,.5,-.55,.62,-1.09,6.55,604]
    return least_squares(residual,seed,args=(points,),bounds=([-5]*3+[-18,-30,.1,360],[5]*3+[18,10,35,2300]))
def run():
    a=solve();p=camera(a.x);rng=np.random.default_rng(724);sensitivity=[]
    for _ in range(32):
        q=solve(CORNICE+rng.uniform(-1.5,1.5,CORNICE.shape))
        sensitivity.append([q.x[6],plane(camera(q.x),(575,163),'front')[1]])
    out={'source_sha256':'c960748413e3c7ea35b4c22eaaed212db6bc887371a6240a87dc1a1a122a8abb',
         'size':[1080,768],'coordinates':'Normalized original shaft width 1. X→image right on front, return along +Y; Z up. Absolute site position and height were not measured.',
         'world_reference':WORLD.tolist(),'corner_uv':CORNICE.tolist(),'verticals':VERTICALS,
         'matrix':p.tolist(),'fit_residual_px':np.round(residual(a.x),4).tolist(),
         'estimated_focal_px':a.x[6],'sensitivity':'32 deterministic fits with independent ±1.5 px cornice shifts, not a survey confidence interval',
         'focal_and_front_eye_z_5_95':np.quantile(sensitivity,[.05,.95],axis=0).tolist(),'faces':FACE,'top':TOP,
         'plane_readings':{face:{k:[plane(p,v,face).round(5).tolist() for v in pts] for k,pts in item.items()} for face,item in FACE.items()}}
    (HERE/'historical-crown-camera.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':run()
