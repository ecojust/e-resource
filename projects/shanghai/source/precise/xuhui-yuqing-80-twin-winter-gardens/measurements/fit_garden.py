"""Fit the paired garden fronts with the visible portions of horizontal semicircles, common column points and rectilinear vanishing directions."""
from pathlib import Path
import argparse,json
import numpy as np
from scipy.optimize import least_squares
HERE=Path(__file__).resolve().parent


def rotation(yaw,pitch,roll):
    cy,sy=np.cos(yaw),np.sin(yaw);cp,sp=np.cos(pitch),np.sin(pitch);cr,sr=np.cos(roll),np.sin(roll)
    right=np.array([cy,-sy,0]);down=np.array([sy*sp,cy*sp,-cp]);forward=np.array([sy*cp,cy*cp,sp])
    return np.array([cr*right+sr*down,-sr*right+cr*down,forward])


def solve():
    data=json.loads((HERE/'paired-bay-photo-pixels.json').read_text());v=data['views'];centres=dict(zip(('SW','NE'),data['axis_centres_m']));outer=dict(zip(('SW','NE'),data['aerial_outer_radii_m']))
    families=('eave','sill','crown','midfloor')
    defs={}
    for name,obs in v.items():
        sets={}
        for axis in ('along','vertical'):
            seg=np.asarray(obs[axis]);line=np.cross(np.column_stack((seg[:,0],np.ones(len(seg)))),np.column_stack((seg[:,1],np.ones(len(seg)))))
            sets[axis]=(seg[:,0],line[:,:2])
        for k,pts in obs['curves'].items():sets[k]=np.column_stack((pts,np.ones(len(pts))))
        defs[name]=sets
    def pose(p,name):
        i=0 if name=='4' else 7;w,h=v[name]['size'];k=np.array([[p[i+6],0,w/2],[0,p[i+6],h/2],[0,0,1.]])
        return k,rotation(*p[i:i+3]),p[i+3:i+6]
    def evaluate(p,report=False):
        res=[];errors={};zs=dict(zip(families,p[14:18]));coeffs={'sill':p[18], 'crown':p[19]}
        for name,sets in defs.items():
            k,r,c=pose(p,name);a=k@r;errs={}
            for direction,j in [('along',0),('vertical',2)]:
                van=a[:,j];base,lines=sets[direction];u=van[:2]-base*van[2];val=(u*lines).sum(axis=1)/np.linalg.norm(u,axis=1)
                res.extend(val/2.0);errs[direction]=val.tolist()
            for key,P in sets.items():
                if key in ('along','vertical'):continue
                side,fam=key.split('.');cx=centres[side];radius=outer[side]
                if fam in coeffs:radius-=coeffs[fam]
                if fam=='midfloor':radius-=p[20] if side=='SW' else -p[21]
                z=zs[fam]
                theta=np.linspace(-np.pi/2,np.pi/2,145)
                world=np.column_stack((cx+radius*np.sin(theta),-radius*np.cos(theta),np.zeros_like(theta)+z))
                # Reject the backs of the circles; an unrestricted image conic confuses their near and far arcs.
                normal=np.column_stack((np.sin(theta),-np.cos(theta)))
                facing=((c[:2]-world[:,:2])*normal).sum(axis=1)>-.12
                uv=(world[facing]-c)@a.T;uv=uv[:,:2]/uv[:,2:3]
                start,end=uv[None,:-1,:],uv[None,1:,:];delta=end-start
                t=np.clip(((P[:,:2,None].transpose(0,2,1)-start)*delta).sum(axis=2)/(delta*delta).sum(axis=2),0.,1.)
                nearest=start+t[:,:,None]*delta;diff=nearest-P[:,:2,None].transpose(0,2,1)
                j=np.argmin((diff*diff).sum(axis=2),axis=1);d=diff[np.arange(len(P)),j]
                res.extend(d.ravel()/2.5);errs[key]=np.linalg.norm(d,axis=1).tolist()
            ix=0 if name=='4' else 1
            shared=[[*p[22:24],zs['midfloor']],[*p[22:24],p[26]],[*p[24:26],zs['midfloor']],[*p[24:26],p[26]],list(p[27:30])]
            for sig,xyz in zip(data['shared_colonnade'],shared):
                pixel=a@(np.asarray(xyz)-c);delta=pixel[:2]/pixel[2]-sig[name]
                res.extend(delta/sig['sigma_px'][ix]);errs[sig['name']]=delta.tolist()
            errors[name]=errs
        res.extend([(p[5]-1.55)/.36,(p[12]-1.55)/.36,(p[6]-734.9)/8.,(p[13]-635.)/230.,(p[18]-.45)/.2,(p[19]-.35)/.2,(p[20]-.4)/.3,(p[21]-.2)/.45])
        return errors if report else res
    lo=np.array([-1.10,-.05,-.20,2,-30,.65,680.,.12,-.05,-.25,-35,-30,.60,350.,4.,3.,5.,1.6,.06,.04,.04,-.4]);hi=np.array([-.05,.65,.20,35,-5,2.75,790.,1.15,.75,.25,-2,-4,2.8,1200.,12.,7.6,14.,6.1,1.1,1.1,1.0,1.4]);
    start=np.array([-.45,.25,0.,12.,-15.,1.6,735.,.55,.28,0.,-17.,-11.5,1.5,635.,8.,5.3,8.85,3.95,.47,.36,.49,.15])
    # Both column heads share the underside level and their feet share the top landing.
    start=np.r_[start,[-10.9,.07,-5.1,-2.31,-.05,-5.1,-1.04,2.05]]
    lo=np.r_[lo,[-14.,-3.,-8.7,-5.2,-.15,-8.5,-3.,1.]];hi=np.r_[hi,[-7.7,2.5,-2.8,.5,.75,-3.2,2.5,3.2]]
    out=least_squares(evaluate,start,bounds=(lo,hi),loss='soft_l1',x_scale='jac',max_nfev=180);p=out.x;err=evaluate(p,True);cams={}
    for name in v:
        K,R,C=pose(p,name);cams[name]={'K':K.tolist(),'R':R.tolist(),'C':C.tolist(),'size':v[name]['size']}
    measures={name:{k:dict(n=len(vv),median_abs_px=float(np.median(np.abs(vv))),max_abs_px=float(np.max(np.abs(vv))))for k,vv in groups.items()}for name,groups in err.items()}
    return {'cameras':cams,'centres_m':centres,'outer_radii_m':outer,'eave_soffit_z':p[14],'window_sill_z':p[15],'upper_parapet_z':p[16],'middle_slab_underside_z':p[17], 'window_recess_m':p[18],'crown_recess_m':p[19],'midfloor_radii_m':{'SW':outer['SW']-p[20],'NE':outer['NE']+p[21]},'residuals':measures,'signed_residuals_px':err,'shared_colonnade_xyz':{'west_capital':[*p[22:24],p[17]],'west_foot':[*p[22:24],p[26]],'inner_capital':[*p[24:26],p[17]],'inner_foot':[*p[24:26],p[26]],'arch_crown':list(p[27:30])},'cost':out.cost,'conditional_geometry':'Metric basis is the two aerial roof arcs, with different western/eastern radii. Camera height is a soft prior. Curves are photo silhouettes and may include renderer/occlusion and small asymmetric variations.'}
if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('--output',type=Path,default=HERE/'garden-cameras.json');arg=cli.parse_args();r=solve();arg.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in r.items()if k not in ('signed_residuals_px','residuals')});print(r['residuals'])
