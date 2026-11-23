"""Fit the villa's opposing broad windows and two independently observed rows of columns."""
from pathlib import Path
import argparse,json
import numpy as np
from scipy.optimize import least_squares
HERE=Path(__file__).absolute().parent

def rotation(yaw,pitch,roll):
    cy,sy=np.cos(yaw),np.sin(yaw);cp,sp=np.cos(pitch),np.sin(pitch);cr,sr=np.cos(roll),np.sin(roll)
    right=np.array([cy,-sy,0]);down=np.array([sy*sp,cy*sp,-cp]);forward=np.array([sy*cp,cy*cp,sp])
    return np.asarray([cr*right+sr*down,-sr*right+cr*down,forward])

def fit(data):
    names=list(data['working_size']);params=list(data['parameters']);nparam=len(params)
    p0=np.asarray(list(data['parameters'].values()));parindex={k:i for i,k in enumerate(params)}
    allcams=[[-.01,.41,0,-.03,-7.0,1.55,520],[.80,.15,.01,-11.0,-9.1,1.65,1470],[.55,-.04,.01,-3.2,-4.10,1.2,550]]
    obs=[];axes={};outlines={}
    for n,d in data['points'].items():
        ids=[];mul=[];constant=[]
        for elem in d['xyz']:
            if isinstance(elem,str):
                words=elem.split('*');ids.append(parindex[words[-1]]);mul.append(float(words[0])if len(words)==2 else 1.);constant.append(0.)
            else:ids.append(0);mul.append(0.);constant.append(elem)
        for name,uv in d['working_px'].items():
            obs.append((n,name,ids,np.array(mul),np.array(constant),np.array(uv),d['uncertainty_px']))
    byview={}
    for name in names:
        rows=[e for e in obs if e[1]==name]
        byview[name]=([e[0]for e in rows],*[np.asarray([e[i]for e in rows])for i in (2,3,4,5,6)])
        axes[name]=[]
        for ax,lines in data['axis_lines'][name].items():
            for a,b in lines:
                line=np.cross([*a,1.],[*b,1.]);line/=np.linalg.norm(line[:2])
                axes[name].append(('xyz'.index(ax),line,np.array(a),np.linalg.norm(np.subtract(a,b))))
        if name in data['outside_corner_lines']:
            a,b=data['outside_corner_lines'][name];line=np.cross([*a,1.],[*b,1.]);outlines[name]=line/np.linalg.norm(line[:2])
    def unpack(t):
        result={}
        for i,name in enumerate(names):
            yaw,pitch,roll,x,y,z,logf=t[nparam+7*i:nparam+7*i+7];f=allcams[i][-1]*np.exp(logf)
            w,h=data['working_size'][name];k=np.array([[f,0,w/2],[0,f,h/2],[0,0,1.]])
            result[name]=(k,rotation(yaw,pitch,roll),np.array([x,y,z]))
        return result
    def errors(t,report=False):
        cams=unpack(t);parts=[];px={}
        for i,name in enumerate(names):
            k,r,c=cams[name];kr=k@r
            ids,idx,mul,constant,uv,sigma=byview[name];world=t[idx]*mul+constant
            img=(world-c)@kr.T;img=img[:,:2]/img[:,2:]
            delta=img-uv;parts.extend((delta/sigma[:,None]).ravel())
            px[name]={n:np.round(a,2).tolist()for n,a in zip(ids,delta)}
            for axis,line,a,scale in axes[name]:
                vp=kr[:,axis];parts.append(line@vp/np.linalg.norm(vp[:2]-vp[2]*a)*scale/2.5)
            if name in outlines:
                y=t[parindex['wing_foot_y']]
                for z in (4.5,9.2):
                    one=kr@(np.array([-data['facade_span_m']/2,y,z])-c);parts.append((outlines[name]@one)/one[2]/3.)
            parts.append((c[2]-1.55)/(.53 if name!='05'else .75))
            parts.append(t[nparam+7*i+6]/(.115 if name=='04'else .55))
        # The common vertical datum is the court below the landing, five visible rises in 05.
        parts.append((t[parindex['door_base']]-.62)/.17)
        # The outside re-entrant corner marked by the drain is behind the broad front face.
        parts.append((t[parindex['wing_foot_y']]-.72)/.80)
        return px if report else np.asarray(parts)
    start=np.r_[p0,*[np.r_[c[:6],0.]for c in allcams]]
    res=least_squares(errors,start,loss='soft_l1',max_nfev=230,ftol=2e-10,xtol=2e-10)
    cams=unpack(res.x);params=dict(zip(params,res.x[:nparam].tolist()));allpx=errors(res.x,True);views={}
    for n,(k,r,c)in cams.items():
        factor=np.asarray(data['size'][n])/data['working_size'][n]
        native=np.diag([*factor,1.])@k
        views[n]=dict(K=native.tolist(),working_K=k.tolist(),R=r.tolist(),C=c.tolist(),size=data['size'][n],working_size=data['working_size'][n],working_error_vectors_px=allpx[n])
    return dict(axis={'x':'True bearing approximately 72 degrees. Increasing to right in photo 03.','y':'Into building, approximately 342 degrees. Y=0 is the broad front window plane.','z':'Up from the terrace forecourt; lower stair line in 05 sets approximate ground level.'},views=views,measured_layout_m=params,
                uncertainty='12.90 m overall facade width from the generalized 5241 footprint; likely variation approximately ±0.7 m. Parametric fit ties the two sides of the front and does not directly measure hidden floor interiors.')
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,default=HERE/'court-cameras.json');a=ap.parse_args();res=fit(json.loads((HERE/'portico-observations.json').read_bytes()));a.output.write_text(json.dumps(res,indent=2)+'\n')
    print(res['measured_layout_m'])
    for n,c in res['views'].items():
        v=np.asarray(list(c['working_error_vectors_px'].values()));err=np.linalg.norm(v,axis=1);print(n,c['C'],c['working_K'][0][0],np.median(err),np.max(err),sorted(zip(err,c['working_error_vectors_px']),reverse=True)[:4])
