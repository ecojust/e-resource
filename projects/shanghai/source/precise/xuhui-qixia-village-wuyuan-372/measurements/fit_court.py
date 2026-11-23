"""Resect four handheld cameras from line directions, common courtyard features and storey levels."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
HERE=Path(__file__).resolve().parent
VIEWS=(17,18,19,20)

def solve():
    data=json.loads((HERE/'row-line-observations.json').read_text())
    links=json.loads((HERE/'named-court-overlaps.json').read_text())['overlaps']
    marks=[]
    for pair,group in links.items():
        i,j=map(int,pair.split('-'))
        for row in group:
            front='divider' if 'divider' in row['feature'] else 'lip' if 'lip' in row['feature'] else 'door' if 'right-door' in row['feature'] else 'wall'
            marks.append((i,j,np.array(row['first_px']),np.array(row['second_px']),front,row))
    def pose(angles):
        yaw,pitch,roll=angles;sy,cy=np.sin(yaw),np.cos(yaw);sp,cp=np.sin(pitch),np.cos(pitch);sr,cr=np.sin(roll),np.cos(roll)
        right=np.array([cy,-sy,0]);down=np.array([sy*sp,cy*sp,-cp]);forward=np.array([sy*cp,cy*cp,sp])
        return np.array([cr*right+sr*down,-sr*right+cr*down,forward])
    def cameras(v):
        f=v[-4];k=np.array([[f,0,325],[0,f,243.5],[0,0,1.]])
        out={}
        for i,view in enumerate(VIEWS):
            r=pose(v[6*i:6*i+3]);c=v[6*i+3:6*i+6]
            out[view]=(c,r,k,r.T@np.linalg.inv(k))
        return out
    def wall(cam,uv,y):
        c,r,k,inv=cam;ray=inv@np.r_[uv,1.];return c+ray*((y-c[1])/ray[1])
    def project(cam,xyz):
        c,r,k,_=cam;p=k@r@(xyz-c);return p[:2]/p[2]
    def measurements(v,summary=False):
        cams=cameras(v);res=[];records=[]
        for view,cam in cams.items():
            c,r,k,_=cam
            for name,direction in [('along',r[:,0]),('vertical',r[:,2])]:
                van=k@direction
                for p,q in data['directions'][str(view)][name]:
                    p=np.array(p);lr=np.array(q)-p;u=van[:2]-p*van[2]
                    off=(lr[0]*u[1]-lr[1]*u[0])/np.linalg.norm(u)
                    res.append(off/1.8)
            levels=data['balcony_reference'][str(view)]
            for row,level in [('middle',3.18),('top',6.23)]:
                face=-v[-2] if view in (19,20) else -v[-3]
                heights=[wall(cam,uv,face)[2] for uv in levels[row]]
                res.append((np.mean(heights)-level)/.18)
            res.append((c[2]-1.58)/.12)
        soffit=data['no9_visible_soffit'];end=cams[soffit['view']]
        for face,back in zip(soffit['front_top_px'],soffit['rear_soffit_px']):
            z=wall(end,face,-v[-2])[2]-soffit['slab_thickness_estimate_m']
            res.append((wall(end,back,v[-1])[2]-z)/soffit['uncertainty_m'])
        for i,j,a,b,front,obs in marks:
            y={'wall':0.,'door':v[-1],'lip':-v[-2],'divider':-v[-3]}[front];pt=wall(cams[i],a,y);diff=project(cams[j],pt)-b
            # Two edges disappear into the tree at the change of exposure.
            # Their recorded pixels remain in the residual table with reduced fit weight.
            weight=8. if obs['feature'] in ('pair.upper-right.jamb-R.at-sill','pair.lower-left.jamb-L.at-sill') else obs['reading_tolerance_px']
            if front=='lip':weight=1.7
            if front=='door':weight=max(weight,6.)
            res.extend(diff/weight)
            records.append(dict(feature=obs['feature'],first=i,second=j,first_px=a.tolist(),second_px=b.tolist(),plane_y_m=y,
                                xyz_m=pt.tolist(),reprojection_px=diff.tolist(),error_px=float(np.linalg.norm(diff))))
        res.extend([(cams[18][0][0])/.01,(v[-4]-526.7)/9.,(v[-3]-.68)/.23,(v[-2]-.18)/.31,(v[-1]-1.05)/.28])
        return (cams,records) if summary else res
    start=np.r_[[q for x,yaw in [(9,-.52),(0,-.10),(-10,-.39),(-14,-.67)] for q in (yaw,.35,0.,x,-12.,1.58)],526.7,.8,.52,1.15]
    lo=np.r_[np.tile([-1.4,.02,-.26,-58,-32,1.12],4),490.,.08,-.45,.05]
    hi=np.r_[np.tile([1.4,.90,.26,58,-3,2.20],4),560.,2.45,2.15,3.2]
    out=least_squares(measurements,start,bounds=(lo,hi),loss='soft_l1',max_nfev=280,x_scale='jac')
    cams,points=measurements(out.x,True)
    views={i:dict(centre=c.tolist(),rotation=r.tolist(),intrinsic=k.tolist()) for i,(c,r,k,_) in cams.items()}
    errors=[m['error_px'] for m in points]
    return dict(views=views,shared_points=points,median_overlap_error_px=float(np.median(errors)),max_overlap_error_px=max(errors),
                balcony_projection_m=float(out.x[-3]),no9_balcony_projection_m=float(out.x[-2]),no9_door_recess_m=float(out.x[-1]),focal_length_px=float(out.x[-4]),storey_scale_assumption_m=3.05,
                coordinate_system='X along the row to the NE, Y inward to NW, Z up. The main court wall is Y=0; X origin is the horizontal position of camera 18.',
                uncertainties='Measurements from small street photographs; storey height and shared balcony projection are soft priors. The published fit records each remaining mismatch.',
                cost=float(out.cost),optimizer_message=out.message)
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--output',type=Path,required=True)
    args=cli.parse_args();result=solve();args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(result['median_overlap_error_px'],result['max_overlap_error_px'],result['balcony_projection_m'])
