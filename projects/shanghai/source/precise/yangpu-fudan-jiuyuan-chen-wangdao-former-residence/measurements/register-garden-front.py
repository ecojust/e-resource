"""Register two post-restoration garden photographs of the Fudan exhibition hall."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
HERE=Path(__file__).resolve().parent
def camera(values,center):
    angles=values[3:6];R=Rotation.from_euler('xyz',angles).as_matrix()@np.array([[1,0,0],[0,0,-1],[0,1,0]])
    f=values[6];K=np.array([[f,0,center[0]],[0,f,center[1]],[0,0,1]])
    return K@np.column_stack((R,-R@values[:3]))
def project(P,p):
    q=P@np.r_[p,1];return q[:2]/q[2]
def main():
    data=json.loads((HERE/'garden-image-points.json').read_text());points=data['points'];variants=['fayhoo','restoration']
    # Frame widths are independent. Preserve the first floor-to-transom display reference.
    # All coordinates beyond the registration plane come from their individual visible wall or join.
    start=[[2,-13,1.6,.13,0,0,810],[5,-22,1.7,.08,0,0,900]]
    q=np.array([*start[0],*start[1],*data['initial'].values()],dtype=float);keys=list(data['initial'])
    def unpack(v): return dict(zip(keys,v[14:]))
    def xyz(pt,m):return [m.get(x,x) for x in pt['xyz']]
    def residual(v):
        m=unpack(v);ps=[camera(v[j*7:j*7+7],data['centres'][j]) for j in range(2)]
        err=[]
        for pt in points:
            if pt.get('holdout'):continue
            for j,name in enumerate(variants):
                if name in pt:err.extend(project(ps[j],xyz(pt,m))-pt[name])
        err+= [(v[6]-810)/27,(v[13]-900)/140,(v[2]-1.55)/.16,(v[9]-1.55)/.50]
        for k,val,sigma in data['depth_priors']:err.append((m[k]-val)/sigma)
        return err
    sol=least_squares(residual,q,loss='soft_l1',f_scale=2.5,max_nfev=600,x_scale='jac')
    m=unpack(sol.x);out={}
    for j,name in enumerate(variants):
        v=sol.x[j*7:j*7+7];P=camera(v,data['centres'][j]);res=[]
        for pt in points:
            if name not in pt:continue
            predicted=project(P,xyz(pt,m));error=float(np.linalg.norm(predicted-pt[name]))
            res.append(dict(point=pt['id'],observed=pt[name],projected=predicted.tolist(),error_px=error,holdout=pt.get('holdout',False)))
        out[name]=dict(matrix=P.tolist(),eye=v[:3].tolist(),focal_px=v[6],points=res,median_px=float(np.median([r['error_px'] for r in res if not r['holdout']])))
    result=dict(unit='display metres',reference='Door threshold to common transom head = 2.75 display metres. No architectural survey dimension was available.',coordinates='X right from threshold, Y inward, Z upward',fields=m,photos=out)
    (HERE/'garden-front-registration.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(m);print({k:(v['eye'],v['focal_px'],v['median_px'])for k,v in out.items()})
if __name__=='__main__':main()
