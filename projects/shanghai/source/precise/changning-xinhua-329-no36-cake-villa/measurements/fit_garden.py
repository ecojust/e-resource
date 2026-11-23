"""Jointly fit the three central openings, floor bands and photographs of No. 36."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
HERE=Path(__file__).resolve().parent

def axes(c,t):
    f=np.asarray(t)-c;f/=np.linalg.norm(f)
    u=np.cross(f,[0,0,1]);u/=np.linalg.norm(u)
    return np.vstack((u,np.cross(f,u),f))

def structure(p):
    radius,step,side,door,sill,door_sill,head,transom,balcony,top,rail=p[:11]
    out={'roof.apex':[0,radius,8.78],'roof.gutter':[0,-.36,6.50]}
    for col,i,w in [('left',-1,side),('door',0,door),('right',1,side)]:
        angle=i*step
        def xyz(x,z):
            return [radius*np.sin(angle)+x*np.cos(angle), radius*(1-np.cos(angle))+x*np.sin(angle),z]
        for key,x,z in [('low',0,door_sill if not i else sill),('high',0,head),('hl',-w/2,head),('hr',w/2,head)]:
            out[col+'.'+key]=xyz(x,z)
        if not i:
            out['door.transom']=xyz(0,transom);out['door.ll']=xyz(-w/2,door_sill);out['door.lr']=xyz(w/2,door_sill)
        else:out['outer.'+col+'-brick']=xyz(i*radius*np.tan(step/2),balcony)
        bay={'door':'centre'}.get(col,col)
        out['upper.'+bay+'-foot']=xyz(0,balcony);out['upper.'+bay+'-head']=xyz(0,top)
        out['rail.'+bay]=xyz(0,rail)
    return out

def cam(p,size):
    c=p[:3];r=Rotation.from_rotvec(p[3:6]).as_matrix();f=np.exp(p[6])
    k=np.array([[f,0,(size[0]-1)/2],[0,f,(size[1]-1)/2],[0,0,1]])
    return c,r,k

def solve(book):
    photos=book['photos'];names=list(photos)
    pri=np.array([9.30,.255,1.48,1.92,.67,.38,3.04,2.50,3.87,6.12,4.92])
    sig=np.array([1.10,.055,.32,.34,.23,.12,.30,.22,.38,.60,.34])
    p0=list(pri);focal=[1800.,735.]
    for i,n in enumerate(names):
        c=np.array([-.15,-24.,1.70]);r=axes(c,[0.,1.2,3.4]);p0.extend([*c,*Rotation.from_matrix(r).as_rotvec(),np.log(focal[i])])
    def residual(p,details=False):
        world=structure(p);rows=[];out=[]
        for i,n in enumerate(names):
            rec=photos[n];c,r,k=cam(p[11+7*i:18+7*i],rec['size'])
            for key,q in rec['observations'].items():
                v=k@r@(np.array(world[key])-c);uv=v[:2]/v[2];e=uv-q
                if not key.startswith('rail.'):
                    out.extend(e/rec['sigma_px'])
                rows.append({'photo':n,'point':key,'used_in_fit':not key.startswith('rail.'),'observed':q,'calculated':uv.tolist(),'error_px':float(np.linalg.norm(e))})
            out.extend([(c[2]-1.68)/.38, np.log(k[0,0]/focal[i])/.45])
        out.extend((p[:11]-pri)/sig);out.append((p[7]-p[5]-2.12)/.085)
        return rows if details else out
    opt=least_squares(residual,p0,loss='soft_l1',max_nfev=450,x_scale='jac')
    p=opt.x;stations={}
    for i,n in enumerate(names):
        c,r,k=cam(p[11+7*i:18+7*i],photos[n]['size'])
        stations[n]={'size':photos[n]['size'],'C':c.tolist(),'R':r.tolist(),'K':k.tolist(),'P':(k@np.column_stack((r,-r@c))).tolist()}
    keys=['radius','bay_angle','block_window_width','door_width','block_sill','door_sill','opening_top','door_transom','balcony_floor','upper_opening_top','rail_top']
    return {'parameters':dict(zip(keys,p[:11])),'stations':stations,'geometry_points':structure(p),'observations':residual(p,True),'limits':'Photo dates unknown. The radius and all absolute dimensions are conditional. Three rail points in each view withheld. Only visible garden sectors are modelled.'}
if __name__=='__main__':
    book=json.loads((HERE/'garden-photo-controls.json').read_bytes())
    result=solve(book);(HERE/'garden-registration.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['parameters'])
