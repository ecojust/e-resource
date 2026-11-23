"""Fit the three gallery cameras jointly to the upper timberwork and the three garden windows."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
HERE=Path(__file__).resolve().parent
def solve(directory):
    frame=json.loads((directory/'curved-veranda-three-views.json').read_text())
    controls=json.loads((directory/'south-window-photo-controls.json').read_text());names=controls['sources']
    folded=json.loads((directory/'curved-veranda-folded-roof.json').read_text())
    base=frame['photos'];cams=[];centres=[]
    for key in names:
        stock=folded['stations'][key]
        base[key].update(P=stock['P'],focal_px=stock['focal_px'],plane_observations=stock['measured'])
    landmarks=folded['controls']
    def K(f,cx,cy):return np.array([[f,0,cx],[0,f,cy],[0,0,1.]])
    for key in names:
        v=base[key];cx,cy=np.asarray(v['extent'])/2;centres.append((cx,cy));f=v['focal_px']
        rt=np.linalg.solve(K(f,cx,cy),v['P']);cams.extend([*Rotation.from_matrix(rt[:,:3]).as_rotvec(),*rt[:,3],np.log(f)])
    x0=np.r_[.005,.333,.170,.368,-.316,-.781,.043,cams]
    def proj(x,i):
        q=x[7+i*7:14+i*7];r=Rotation.from_rotvec(q[:3]).as_matrix();return K(np.exp(q[-1]),*centres[i])@np.column_stack([r,q[3:6]])
    def world(x,name):
        _,group,_,corner=name.split('_');c,broad,narrow,step,top,sill,depth=x[:7]
        u=c+dict(left=-step,middle=0.,right=step)[group]
        u+=(broad if group=='middle' else narrow)*(.5 if corner[1]=='R' else -.5)
        return [u,depth,top if corner[0]=='T' else sill]
    def pixel(P,p):
        v=P@np.r_[p,1];return v[:2]/v[2]
    def residuals(x,report=False):
        groups=[]
        for i,key in enumerate(names):
            P=proj(x,i)
            for name,target in base[key]['plane_observations'].items():
                d=pixel(P,landmarks[name])-target
                groups.append((key,name,target,d))
            for name,pts in controls['corners'].items():
                if pts[i] is not None:groups.append((key,name,pts[i],pixel(P,world(x,name))-pts[i]))
        if report:return groups
        # Weak focal and window-depth priors constrain a nearly planar three-view scene.
        return np.r_[np.concatenate([d for k,n,t,d in groups]),(x[13::7]-x0[13::7])*8,(x[6]-.040)*12]
    res=least_squares(residuals,x0,loss='soft_l1',f_scale=1.35,max_nfev=140)
    views={};rows=residuals(res.x,True)
    for i,key in enumerate(names):
        data=[{'name':n,'image':q,'error_px':round(float(np.linalg.norm(d)),3)}for k,n,q,d in rows if k==key]
        views[key]={'file':base[key]['file'],'projection':proj(res.x,i).tolist(),'focal_px':float(np.exp(res.x[13+i*7])),'points':len(data),'median_px':float(np.median([d['error_px']for d in data])),'checks':data}
    return {'reference':'One unit is the centre spacing of the two tall timbers beside the curved upper gallery. x is rightward, y into the house, z is measured from the lower cross-timber.', 'shared_window_parameters':dict(zip(['centre','wide_width','narrow_width','spacing','head','sill','depth'],res.x[:7])), 'vertices':{k:world(res.x,k) for k in controls['corners']},'cameras':views}
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',nargs='?',type=Path,default=HERE);args=parser.parse_args();r=solve(args.directory)
    (args.directory/'south-window-and-gallery-fit.json').write_text(json.dumps(r,indent=2)+'\n');print([(k,round(v['median_px'],2),v['points']) for k,v in r['cameras'].items()],r['shared_window_parameters'])
