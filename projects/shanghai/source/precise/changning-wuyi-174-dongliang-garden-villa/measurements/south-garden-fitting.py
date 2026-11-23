"""Joint garden camera, eave and bay fitting in native photographic coordinates."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares


BOOK=Path(__file__).with_name('south-garden-two-photographs.json')
book=json.loads(BOOK.read_bytes())
P0=np.array(list(book['third_solution']['fitted_m'].values()))
c08=np.r_[book['third_solution']['views_8pars']['8']['camera_coefficients'],1.,0.]
c00=np.r_[book['third_solution']['views_8pars']['0']['camera_coefficients'],1.,0.]
pairs=[["wL",8,313,401],["wC",8,523,402],["wR",8,732,401],["aw",8,522,192],["wLl",8,249,196],["wLr",8,375,196],["wRl",8,669,196],["wRr",8,795,196],["deck",8,531,629],["soffit",8,531,725],["ground",8,532,1157],["rail",8,531,440],["lDeck",8,120,578],["rDeck",8,927,580],["lRail",8,120,402],["rRail",8,927,403],["lJamb",8,397,1155],["rJamb",8,667,1155],["lFold",8,308,1138],["rFold",8,753,1138],["lStone",8,207,693],["rStone",8,853,693],["lHead",8,398,736],["rHead",8,667,737],["lFoldHead",8,309,715],["rFoldHead",8,754,715],["deck",0,552,281],["soffit",0,552,309],["rail",0,552,234],["lDeck",0,438,290],["rDeck",0,658,283],["lRail",0,438,248],["rRail",0,658,239],["lHead",0,515,323],["rHead",0,590,321],["lFoldHead",0,488,323],["rFoldHead",0,618,319],["lStone",0,457,322]]
gutters={8:np.array([[310,72],[522,70],[735,70]]),0:np.array([[400,209],[521,205],[620,205]])}

def project(c,pt):
    U,V,s,k,dv,ds,yaw,r,zh,q=c;x,d,z=pt;h=z-2.96;den=1-k*d+yaw*x+q*h
    return np.array([U+(s*x+ds*d+r*h)/den,V+(dv*d-s*zh*h-r*x)/den])

def at_horizontal_station(c,u,d,z):
    U,V,s,k,dv,ds,yaw,r,zh,q=c;t=u-U;h=z-2.96
    x=(t*(1.-k*d+q*h)-ds*d-r*h)/(s-t*yaw)
    return project(c,[x,d,z])

def at_depth(c,xy,d):
    U,V,s,k,dv,ds,yaw,r,zh,q=c;u,v=xy[0]-U,xy[1]-V
    x,h=np.linalg.solve([[s-u*yaw,r-u*q],[-r-v*yaw,-s*zh-v*q]],[u*(1-k*d)-ds*d,v*(1-k*d)-dv*d])
    return [x,h+2.96]

def geometry(p):
    pitch,w,aw,hw,sh,high,thick,fg,xa,xb,xc,bg,cg=p
    g=dict(wL=(-pitch,0,2.995),wC=(0.,0,2.995),wR=(pitch,0,2.995),aw=(0.,.33,aw),wLl=(-pitch-w/2,0,aw-.10),wLr=(-pitch+w/2,0,aw-.10),wRl=(pitch-w/2,0,aw-.10),wRr=(pitch+w/2,0,aw-.10),deck=(0,2.12,2.96),soffit=(0,2.12,2.96-thick),ground=(0,fg,.042),rail=(0.,2.065,2.96+high))
    for side,sg in [('l',-1),('r',1)]:
        for label,x,d,z in [('Deck',hw,sh,2.96),('Rail',hw,sh-.045,2.96+high),('Jamb',xa,fg,.042),('Head',xa,fg,2.96-thick-.04),('Fold',xb,bg,.042),('FoldHead',xb,bg,2.96-thick-.04),('Stone',xc,cg,2.96-thick-.04)]:
            g[side+label]=(sg*x,d,z)
    return g

def fit(eave_z=5.55,eave_d=.45,roof_z=10.15,roof_d=-6.08,focal=None,strict=False):
    ini=np.r_[P0,c08,c00,3.34,3.14]
    # First-stage scale and established heights carry independent architectural information.
    def residual(p,output=False):
        shape=p[:13];a,b=p[13:23],p[23:33];g=geometry(shape);rr=[]
        for label,n,u,v in pairs:rr.extend((project(a if n==8 else b,g[label])-np.array([u,v]))/(2.2 if n==8 else 2.5))
        for c,n in [(a,8),(b,0)]:
            for u,v in gutters[n]:
                rr.append((at_horizontal_station(c,u,eave_d,eave_z)[1]-v)/(1.2 if n==8 else 1.6))
        x,z=at_depth(b,[493,114],roof_d);rr.append((z-roof_z)/.065)
        # The two short iron return rails continue toward an uncertain depth vanishing point.
        rr.extend([(a[0]-a[5]/a[3]-511.38)/36,(a[1]-a[4]/a[3]-6.30)/30])
        for c,n in [(a,8),(b,0)]:
            rr.extend([np.log(c[8])/(.04 if strict else .075),c[9]/(.02 if strict else .048),c[7]/2.2])
        for x,na,fa in [(-p[33],109,436),(p[34],907,656)]:
            rr.extend([(project(a,[x,0.,4.72])[0]-na)/4.,(project(b,[x,0.,4.72])[0]-fa)/15.])
        # Keep the 08 plan silhouette tied to the independently constrained 2.12 m projection.
        for idx,prior,err in [(7,2.03,.08),(4,1.78,.16),(6,.55,.13),(11,1.99,.12),(12,1.86,.15)]:
            rr.append((p[idx]-prior)/err)
        M=np.array([[b[2],b[5],b[7]],[-b[7],b[4],-b[2]*b[8]],[b[6],-b[3],b[9]]])
        eye=np.linalg.solve(M,[0.,0.,-1.])
        rr.append((eye[2]+2.96-1.6)/.22)
        support=np.array([1.70685,1.02482,4.793,2.36947,1.78127,.99718,.55760,2.052,.73653,1.23860,1.85937,1.993,1.858])
        rr.extend((shape-support)/np.array([.055,.035,.055,.07,.05,.03,.035,.04,.035,.05,.05,.08,.10]))
        if focal: rr.append(np.log((b[2]/b[3])/focal)/.025)
        return np.array(rr)
    low=np.r_[[1.1,.70,4.2,1.6,1.0,.7,.32,1.78,.53,.9,1.3,1.4,1.2],
              [470,370,85,.035,25,-35,-.10,-7,.76,-.17],[485,250,24,.025,-35,-25,-.12,-6,.72,-.18],2,2]
    hi=np.r_[[2.24,1.5,5.2,2.85,2.05,1.2,.73,2.13,1.1,1.65,2.6,2.1,1.99],
             [565,430,220,.24,135,35,.10,7,1.26,.16],[600,355,78,.23,35,35,.12,6,1.28,.18],4.5,4.5]
    rr=least_squares(residual,np.clip(ini,low+1e-8,hi-1e-8),bounds=(low,hi),loss='soft_l1',f_scale=1.8,max_nfev=170)
    p=rr.x;a,b=p[13:23],p[23:33];g=geometry(p[:13]); out={}
    for n,c in [(8,a),(0,b)]:
        obs=[[label,[u,v],project(c,g[label]).tolist()] for label,station,u,v in pairs if station==n];ds=[np.linalg.norm(np.array(o[1])-o[2]) for o in obs]
        out[n]={'coeff':c.tolist(),'f_px_ratio_s_over_k':c[2]/c[3],'median_p90_max':np.quantile(ds,[.5,.9,1.]).tolist(),'observations':obs,'gutter_reprojected_uv':[at_horizontal_station(c,u,eave_d,eave_z).tolist() for u,v in gutters[n]],'eye_local':np.linalg.solve(np.array([[c[2],c[5],c[7]],[-c[7],c[4],-c[2]*c[8]],[c[6],-c[3],c[9]]]),[0,0,-1]).tolist()}
    z=at_depth(b,[493,114],roof_d)[1];z2=at_depth(b,[644,113],roof_d)[1]
    return dict(eave_z=eave_z,eave_d=eave_d,roof_z=roof_z,roof_d=roof_d,shape=p[:13].tolist(),ridge_check=[z,z2],cameras=out,cost=rr.cost)

if __name__=='__main__':
 import argparse
 q=argparse.ArgumentParser();q.add_argument('--sweep',action='store_true');q.add_argument('--output',type=Path,required=True);args=q.parse_args()
 trials=[(5.52,.30,10.60,-5.5,None,False)]
 if args.sweep:trials += [(z,d,10.60,-5.5,None,False) for z,d in [(5.46,.3),(5.46,.65),(5.65,.3),(5.65,.65),(5.55,.15)]]+[(5.55,.45,10.15,-6.08,f,False) for f in [450,525,650,800]]+[(5.55,.45,10.15,-6.08,None,True)]
 allr=[]
 for t in trials:
  j=fit(*t);allr.append(j);print(t, j['ridge_check'],[(n,r['median_p90_max'],r['gutter_reprojected_uv'][1][1])for n,r in j['cameras'].items()],flush=True)
 name='physical-gutter-sweep.json' if args.sweep else 'physical-gutter-current.json'
 args.output.write_text(json.dumps(allr,indent=2)+'\n')
