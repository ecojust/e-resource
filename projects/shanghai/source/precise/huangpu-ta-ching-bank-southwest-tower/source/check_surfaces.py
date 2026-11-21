"""Independent first-contact checks for the southwest bank tower, in local metres."""
from math import sqrt
from pathlib import Path
import runpy,numpy as np
AP=2.66215
HALF=AP*(sqrt(2)-1)
POINTS=np.array([[-AP-.5275*3.65,.84955*3.65],[-AP,0],[-HALF,HALF-AP],[HALF,HALF-AP],[AP,0],[AP+.84201*3.65,.53946*3.65]])
def check_triangles(triangles,materials,distant):
    root=Path(__file__).resolve().parents[4]
    ray=runpy.run_path(str(root/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['first_hit']
    mats=np.asarray(materials);out=[]
    def evaluate(label,origin,direction,names,minimum,maximum):
        i,dist,point=ray(triangles,origin,direction)
        assert np.isfinite(dist) and mats[i] in names and minimum<=dist<=maximum,(distant,label,str(mats[i]),dist,minimum,maximum)
        out.append(dict(feature=label,origin=np.asarray(origin).tolist(),direction=np.asarray(direction).tolist(),distance_m=round(float(dist),4),material=str(mats[i])))
    for idx,(a,b) in enumerate(zip(POINTS,POINTS[1:])):
        tangent=(b-a)/np.linalg.norm(b-a);norm=np.array([tangent[1],-tangent[0],0]);t=np.r_[tangent,0.];mid=np.r_[(a+b)/2,0.]
        def cast(label,u,z,materials,low,high):
            origin=mid+u*t+3*norm+[0,0,z]
            evaluate(str(idx)+' '+label,origin,-norm,materials,low,high)
        for name,z in [('ground glass',2.11),('pedimented window glass',6.83),('middle window glass',10.69),('upper drum window glass',14.51)]:
            cast(name,.216,z,['recessed dark glazing'],3.305,3.335)
        for name,z in [('ground sash',2.11),('pedimented sash',6.83),('middle sash',10.69),('upper sash',14.51)]:
            cast(name,0,z,['dark timber sashes'],3.146,3.171)
        for name,z in [('base plinth',.18),('lower floor belt',4.66),('middle floor belt',8.78),('upper floor belt',12.94),('deep eave',16.43)]:
            cast(name,.25,z,['carved pale stone'],2.58,2.98)
        cast('upper triangular pediment',.03,8.63,['carved pale stone'],2.73,2.91)
        cast('red brick spandrel',.21,9.07,['restored red facing brick'],2.992,3.009)
        if 0<idx<4:
            cast('paired small left shaft',-.72,6.89,['carved pale stone'],2.74,2.80)
            cast('paired small right shaft',.72,6.89,['carved pale stone'],2.74,2.80)
    for x,y in [(0,.21),(.81,.65),(-.90,.69),(1.67,.02),(-1.67,.02),(1.78,1.21),(-1.74,1.73)]:
        evaluate('low copper cap',np.array([x,y,21.]),[0,0,-1],['oxidised copper','dark patinated seams'],2.75,3.55)
    evaluate('slender summit rod',np.array([0.,HALF,20.]),[0,0,-1],['dark patinated seams'],.63,.67)
    return dict(triangles=len(triangles),rays=out)
