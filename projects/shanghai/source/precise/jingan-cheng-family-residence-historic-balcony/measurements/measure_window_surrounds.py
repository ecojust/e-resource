"""Register window surrounds and wall turns on the calibrated historical street elevation."""
from pathlib import Path
import argparse,json
import numpy as np
w=Path(__file__).resolve().parent
def intersect(P,uv,i,t):
 v=np.array(uv);a=P[:2,:3]-v[:,None]*P[2,:3];rhs=v*P[2,3]-P[:2,3]-a[:,i]*t
 keep=[k for k in range(3)if k!=i];r=np.zeros(3);r[i]=t;r[keep]=np.linalg.solve(a[:,keep],rhs);return r
def face_point(P,uv,a,b):
 v=np.array(uv);d=np.array(b)-np.array(a);d/=np.linalg.norm(d)
 h=P@np.r_[a,0.,1.];basis=np.stack([P[:,:3]@np.r_[d,0.],P[:,2]],1)
 return np.linalg.solve(basis[:2]-v[:,None]*basis[2],v*h[2]-h[:2])
def build(P):
    # The final two coordinates on the left are two visible points along the same cornice line.
    left=[1087,1250];right=[2054,1238]
    z=float(np.mean([intersect(P,k,1,0)[2]for k in (left,right)]))
    turns=[intersect(P,k,2,z)[:2]for k in ([720,1194],left,right,[2414,1140],[3202,1123])]
    turns[1]=intersect(P,left,1,0)[:2];turns[2]=intersect(P,right,1,0)[:2]
    # Bounds describe the outer light surround, with a separately measured inner opening.
    measurements=[
    ('left_splay','left return',0,[[754,1212],[995,1250],[981,1576],[745,1531]],[[785,1240],[956,1269],[949,1541],[779,1510]]),
    ('balcony_left','central west',1,[[1185,1250],[1454,1246],[1454,1542],[1173,1551]],[[1215,1284],[1421,1282],[1417,1540],[1210,1547]]),
    ('balcony_right','central east',1,[[1670,1243],[1948,1239],[1950,1541],[1663,1538]],[[1710,1279],[1909,1273],[1903,1540],[1707,1538]]),
    ('right_splay','right return',2,[[2120,1215],[2300,1175],[2299,1503],[2128,1548]],[[2157,1230],[2282,1198],[2283,1490],[2160,1515]]),
    ('right_front','right forward bay',3,[[2600,1144],[2933,1136],[2942,1506],[2602,1518]],[[2638,1175],[2888,1170],[2897,1465],[2642,1473]])]
    result=[];faces=[]
    for i,(a,b) in enumerate(zip(turns[:-1],turns[1:])):
        faces.append(dict(index=i,start=np.round(a,5).tolist(),end=np.round(b,5).tolist()))
    for key,name,i,outer,inner in measurements:
        a,b=turns[i:i+2]
        # Convert the four independent original-image corners to a rectangle within the survey tolerance.
        def rect(c):
            tl,tr,br,bl=np.array([face_point(P,x,a,b)for x in c])
            return [round(v,5)for v in [(tl[0]+bl[0])/2,(tr[0]+br[0])/2,(bl[1]+br[1])/2,(tl[1]+tr[1])/2]]
        o,r=rect(outer),rect(inner)
        if key.startswith('balcony_'):
            o[2],r[2]=-.046,.015
        result.append(dict(key=key,name=name,face=i,surround_corners_photo=outer,aperture_corners_photo=inner,surround_m=o,opening_m=r))
    return dict(datum='X increases to the right, Y increases behind the central two second-floor openings, Z0 at balcony floor.',registered_eave_z_m=round(z,5),selected_turn_pixels=[[720,1194],left,right,[2414,1140],[3202,1123]],faces=faces,windows=result,cut='Across the cropped left return and along the outer right pier. The upper floor fragment ends at the balcony sill band.')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('camera',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    projected=build(np.array(json.loads(a.camera.read_bytes())['gao2018']['P']))
    a.output.write_text(json.dumps(projected,indent=2,ensure_ascii=False)+'\n')
