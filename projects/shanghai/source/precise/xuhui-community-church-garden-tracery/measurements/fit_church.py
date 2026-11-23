"""Register three independent street and courtyard photographs to the surveyed seven-light window."""
import json,math
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
HERE=Path(__file__).resolve().parent
def axes(c,t):
    f=np.asarray(t)-c;f/=np.linalg.norm(f);u=np.cross(f,[0,0,1]);u/=np.linalg.norm(u)
    return np.vstack((u,np.cross(f,u),f))
def geometry(q,ref):
    span,low,middle,high,tip,foil,depth=q[:7];base=ref['width_between_caps']/2
    out={'peak':[*ref['peak_offset_xy_from_caps'],ref['peak_z']],'left':[-base,0,ref['cap_z']],'right':[base,0,ref['cap_z']],'outer-tip':[0,depth,tip],'foil-left':[-span,depth,foil],'foil-right':[span,depth,foil]}
    for i in range(7):out['arch'+str(i+1)]=[(i-3)*span,depth,[low,middle,middle,high,middle,middle,low][i]]
    return out
def camera(p,sz):
    c=p[:3];r=Rotation.from_rotvec(p[3:6]).as_matrix();f=np.exp(p[6]);w,h=sz
    k=np.array([[f,0,(w-1)/2],[0,f,(h-1)/2],[0,0,1.]])
    return c,r,k
def solve(book,ref):
    names=list(book);p0=[.746,9.91,10.43,11.50,13.41,11.16,.57];prior=np.array(p0);sig=np.array([.15,1.2,1.15,1.1,1.1,1.1,.25])
    seeds={'fayhoo2017':[-.1,-25.6,1.65],'livelikerw2013':[8.3,-16.2,1.7],'szalai2018':[7.5,-10.7,1.65]}
    def predicted_f(n):
        w,h=book[n]['size'];return np.hypot(w,h)*book[n]['mm35_exif']/np.hypot(36,24)
    for n in names:
        c=np.asarray(seeds[n]);r=axes(c,[0,0,10.10]);p0.extend([*c,*Rotation.from_matrix(r).as_rotvec(),np.log(predicted_f(n))])
    def residual(p,save=False):
        model=geometry(p,ref);out=[];re=[]
        for i,n in enumerate(names):
            data=book[n];c,r,k=camera(p[7+i*7:14+i*7],data['size'])
            for key,uv in data['observations'].items():
                t=k@r@(np.asarray(model[key])-c);pixel=t[:2]/t[2];err=pixel-uv
                spread=8. if n=='fayhoo2017' else 18. if n=='livelikerw2013' else 26.
                if key in ['left','right','peak']:spread*=.9
                if key=='foil-left' and n!='fayhoo2017':spread*=1.5
                out.extend(err/spread);re.append({'station':n,'name':key,'observed':uv,'predicted':pixel.tolist(),'error_px':float(np.linalg.norm(err))})
            out.extend([(c[2]-1.70)/.44,np.log(k[0,0]/predicted_f(n))/.11])
            if n=='fayhoo2017':out.append(c[0]/3.7)
        out.extend((p[:7]-prior)/sig);return re if save else out
    fit=least_squares(residual,p0,loss='soft_l1',x_scale='jac',max_nfev=900);p=fit.x;records=residual(p,True);stations={}
    for i,n in enumerate(names):
        c,r,k=camera(p[7+7*i:14+7*i],book[n]['size']);stations[n]={'size':book[n]['size'],'C':c.tolist(),'R':r.tolist(),'K':k.tolist(),'P':(k@np.column_stack((r,-r@c))).tolist()}
    return {'parameters':dict(zip(['light_pitch','outside_arch_z','paired_arch_z','central_arch_z','opening_peak_z','oculus_center_z','window_plane_y'],p[:7])),'survey':ref,'stations':stations,'world_points':geometry(p,ref),'observations':records}
if __name__=='__main__':
    book=json.loads((HERE/'public-photo-measurement.json').read_bytes());ref=json.loads((HERE/'winter-gable-metric.json').read_bytes())
    out=solve(book['stations'],ref);(HERE/'church-registration.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(out['parameters'])
    for n,c in out['stations'].items():print(n,c['C'],np.median([v['error_px'] for v in out['observations']if v['station']==n]))
