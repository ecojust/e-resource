"""Fit a shared four-column pavilion to three observed photographs and a coarse aerial scale."""
from pathlib import Path
import argparse,json
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
D=Path(__file__).resolve().parent

def axes(center,target):
    f=np.array(target)-center;f/=np.linalg.norm(f)
    u=np.cross(f,[0,0,1]);u/=np.linalg.norm(u)
    return np.vstack((u,np.cross(f,u),f))

def camera(p,size):
    c=p[:3];r=Rotation.from_rotvec(p[3:6]).as_matrix()
    f=np.exp(p[6]);k=np.array([[f,0,(size[0]-1)/2],[0,f,(size[1]-1)/2],[0,0,1.]])
    return c,r,k

def structure(p):
    span,inner,zfoot,zh,depth,statue,sill,hood,run,urnx,urnz,urny=p[:12]
    x=[-span,-inner,inner,span]
    return {'feet':[[q,0,zfoot]for q in x],'heads':[[q,0,zh]for q in x],
            'screen_sills':[[q,depth,sill]for q in [-statue,0,statue]],
            'screen_heads':[[q,depth,hood]for q in [-statue,0,statue]],
            'steps':[[-9.35,-run,0],[9.35,-run,0]],
            'vases':[[-urnx,urny,urnz],[urnx,urny,urnz]]}

def solve(book):
    photos=book['photos'];names=list(photos)
    p0=[5,2.5,.90,4.40,3.4,3.50,1.60,3.48,1.70,7.5,2.30,-.3]
    for name,s in photos.items():
        c=np.array(s['eye'],float);r=axes(c,[0,1.3,2.1]);p0.extend([*c,*Rotation.from_matrix(r).as_rotvec(),np.log(s['focal'])])
    def residual(p,table=False):
        obs=structure(p);rows=[];out=[]
        for i,key in enumerate(names):
            desc=photos[key];c,r,k=camera(p[12+7*i:19+7*i],desc['size'])
            for group,points in book['observations'][key].items():
                sigma={'heads':6 if key=='fayhoo2014' else 2.8,'feet':1.8,'steps':4.2,'vases':4,'screen_heads':4.8,'screen_sills':3.0}[group]
                for n,(xyz,uv) in enumerate(zip(obs[group],points)):
                    if uv is None:continue
                    z=k@r@(xyz-c);pix=z[:2]/z[2];delta=pix-uv
                    out.extend(delta/sigma);rows.append({'station':key,'point':group+'/'+str(n+1),'observed':uv,'projected':pix.tolist(),'error_px':float(np.linalg.norm(delta))})
            out += [(c[2]-[1.35,1.65,1.45][i])/.48, np.log(k[0,0]/desc['focal'])/.65]
        out.extend([(p[2]-.93)/.20,(p[8]-1.70)/.51,(p[11]+.3)/.8])
        return rows if table else out
    fit=least_squares(residual,p0,loss='soft_l1',f_scale=2,max_nfev=700);p=fit.x
    rows=residual(p,True)
    result={'parameters':dict(zip(['outer_x','inner_x','landing_z','column_head_z','screen_y','niche_x','sill_z','arch_z','front_run','urn_x','urn_top_z','urn_y'],p[:12])),'stations':{},'controls':rows}
    for i,key in enumerate(names):
        s=photos[key];c,r,k=camera(p[12+7*i:19+7*i],s['size']);e=[v['error_px']for v in rows if v['station']==key]
        result['stations'][key]={'size':s['size'],'C':c.tolist(),'R':r.tolist(),'K':k.tolist(),'P':(k@np.column_stack((r,-r@c))).tolist(),'median_px':float(np.median(e)),'max_px':max(e)}
    return result

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('output',type=Path);a=cli.parse_args()
    a.output.write_text(json.dumps(solve(json.loads((D/'pavilion-observations.json').read_bytes())),ensure_ascii=False,indent=2)+'\n')
