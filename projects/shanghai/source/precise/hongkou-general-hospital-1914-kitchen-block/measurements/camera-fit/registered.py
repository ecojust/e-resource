"""Street photograph on the plane of the northern wall. All image coordinates refer to the 920 by 690 working rendition."""
import numpy as np,json
from pathlib import Path
w=Path(__file__).resolve().parent
d=json.loads((w/'qiao-shifted-perspective.json').read_bytes())
R,K=np.array(d['R']),np.array(d['K'])
def ray(uv):
    return R.T@np.linalg.solve(K,[*uv,1])
def footprint(anchors):
    normals=[];values=[]
    for xy,uv in anchors:
        dx,dy=ray(uv)[:2]
        n=np.array([dy,-dx])/np.hypot(dx,dy)
        normals.append(n);values.append(n@xy)
    return np.linalg.lstsq(normals,values,rcond=None)[0]
# Independent panorama ray intersections give the distance between the northern terminal quoins.
# The first and last eastern quoins are held out for review. Height zero is the short entrance sill.
anchors=[([0,0],[295.1,322]),([44.62,0],[716.6,510])]
eye=np.r_[footprint(anchors),0.]
def cut(uv,axis=1,offset=0):
    r=ray(uv)
    return eye+(offset-eye[axis])/r[axis]*r
eye[2]=-cut([252,629],0,0)[2]
def project(p):
    q=K@R@(np.array(p)-eye)
    return q[:2]/q[2]
if __name__=='__main__':
    print('eye',eye.tolist())
    for i in [[295,67],[295,102],[295,538],[554,397],[570,453],[353,160]]:
        print(i,cut(i))
