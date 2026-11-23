"""Calibrate the 593 entrance against the actual geographic positions of five street images."""
from pathlib import Path
import argparse,json,math
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
HERE=Path(__file__).parent
def street_rotation(az,pitch):
    b,h=np.deg2rad([az,pitch]);c=np.cos(h);s=np.sin(h)
    return np.array([[np.cos(b),-np.sin(b),0],[s*np.sin(b),s*np.cos(b),-c],[c*np.sin(b),c*np.cos(b),s]])

def solve(book):
    loc=book['origin_prior_wgs84'];metres=np.array([111320*math.cos(math.radians(loc[1])),111130])
    active=list(book['picks']);base={}
    for name in active:
        s=book['photos'][name];w,h=s['size'];cx=(w/2);cy=h/2
        f=cx/math.tan(math.radians(s['hfov']/2));k=np.array([[f,0,cx],[0,f,cy],[0,0,1.]])
        c=np.array([*((np.array(s['center_wgs84'])-loc)*metres),s['height_m']])
        base[name]=(c,street_rotation(s['azimuth'],s['pitch']),k)
    def initial(mark):
        aa=[];bb=[]
        for n in active:
            if mark not in book['picks'][n]:continue
            c,r,k=base[n];u,v=book['picks'][n][mark];d=r.T@np.linalg.solve(k,[u,v,1]);nr=np.array([-d[1],d[0]]);nr/=np.linalg.norm(nr);aa.append(nr);bb.append(nr@c[:2])
        return np.linalg.lstsq(aa,bb,rcond=None)[0]
    j=initial('right_foot');l=initial('left_foot');vec=j-l
    angle=np.arctan2(vec[0],vec[1])
    x0=[*j,angle,np.linalg.norm(vec),2.72,2.77,.73,.27,.08,*([0.]*(len(active)*6))]
    def matrix(p):
        sn,cs=np.sin(p[2]),np.cos(p[2])
        return np.array([[sn,-cs,0],[cs,sn,0],[0,0,1]])
    def data(p,n,i):
        c0,r0,k=base[n];v=p[9+i*6:15+i*6]
        c=c0+v[:3];r=Rotation.from_rotvec(np.deg2rad(v[3:])).as_matrix()@r0
        rot=matrix(p);return rot.T@(c-[p[0],p[1],0]),r@rot,k
    def residual(p,observations=False):
        errors=[];report=[]
        for i,n in enumerate(active):
            c,r,k=data(p,n,i);recent=n.endswith('2002')
            for feat,uv in book['picks'][n].items():
                side,kind=feat.split('_');x=0 if side=='right' else -p[3];height=p[5] if side=='right' else p[4];y=0
                if kind=='foot':z=0
                if kind=='cap':z=height+(p[8] if recent else 0)
                if kind=='globe':z=height+p[7];y=p[6]*.5
                if kind in ('left','right'):x+=(-1 if kind=='left' else 1)*p[6]/2;z=height/2
                xyz=[x,y,z];pt=k@r@(xyz-c);pred=pt[:2]/pt[2];dif=pred-uv
                if kind in ('left','right'):dif=dif[:1]
                weight=4 if (n=='7-1512' or kind=='globe')else 3
                errors.extend(dif/weight);report.append(dict(station=n,name=feat,observed=uv,predicted=pred.tolist(),xyz=xyz,error_px=float(np.linalg.norm(dif))))
            v=p[9+i*6:15+i*6];errors.extend(v[:3]/[.40,.40,.19]);errors.extend(v[3:]/[1.40,.86,.39])
        errors.extend([(p[4]-p[5])/.08,(p[6]-.72)/.18,(p[8]-.06)/.08,(p[7]-.28)/.13])
        return report if observations else errors
    q=least_squares(residual,x0,loss='soft_l1',f_scale=2,max_nfev=1600);p=q.x;records=residual(p,True)
    out={'parameters':dict(zip(('offset_e','offset_n','bearing_rad','axes_distance','plain_cap','inscribed_cap','pier_width','globe_center_above_cap','new_cap_addition'),p[:9])),
         'origin_wgs84':(np.asarray(loc)+p[:2]/metres).tolist(),'positive_x_bearing_true_deg':float(np.rad2deg(p[2])%360),'stations':{},'observations':records}
    for i,n in enumerate(active):
        c,r,k=data(p,n,i);e=[v['error_px']for v in records if v['station']==n]
        out['stations'][n]={'size':book['photos'][n]['size'],'C':c.tolist(),'R':r.tolist(),'K':k.tolist(),'P':(k@np.column_stack((r,-r@c))).tolist(),'median_work_px':float(np.median(e)),'peak_work_px':max(e),'station_correction_xyz_m':p[9+i*6:12+i*6].tolist(),'station_rotation_correction_deg':p[12+i*6:15+i*6].tolist()}
    return out
if __name__=='__main__':
    c=argparse.ArgumentParser(description=__doc__);c.add_argument('out',type=Path);a=c.parse_args();d=solve(json.loads((HERE/'gate-survey.json').read_bytes()));a.out.write_text(json.dumps(d,indent=2)+'\n');print(d['parameters'],d['origin_wgs84'],d['positive_x_bearing_true_deg']);print([(k,round(v['median_work_px'],2),round(v['peak_work_px'],1)) for k,v in d['stations'].items()])
