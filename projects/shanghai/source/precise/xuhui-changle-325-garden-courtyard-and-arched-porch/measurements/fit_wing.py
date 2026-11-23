"""Fit a common XYZ frame from the planar frames, balcony and pavement in four photographs."""
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
import json,math,sys
HERE=Path(__file__).resolve().parent
def camera_axes(az,pitch,roll):
    a,e,r=np.radians([az,pitch,roll]);f=np.array([np.sin(a)*np.cos(e),np.cos(a)*np.cos(e),np.sin(e)])
    x=np.array([np.cos(a),-np.sin(a),0]);y=np.cross(f,x)
    return np.array([x*np.cos(r)+y*np.sin(r),y*np.cos(r)-x*np.sin(r),f])
def solve(data):
    origin=np.array(data['reference_wgs']);conv=np.array([111320*np.cos(np.radians(origin[1])),110860])
    cams=data['cameras'];names=list(cams);n=4+len(names)*6
    # Site origin is below the middle of the right-hand steel window.
    initial=[250.,1.,-14.,3395.]
    for k,v in cams.items():
        if k=='fayhoo':initial.extend([1.,-1.,1.62,172,1,0])
        else:initial.extend([*((np.array(v['wgs'])-origin)*conv),v['camera_height'],v['az'],v['pitch'],0])
    # widths + heights, left tangent and wall gap, end of the curved opening, balcony projection.
    initial.extend([.92,.91,2.38,-1.69,.88,.92,2.35,.23,.15]);s0=np.array(initial)
    def sites(a):
        rw,rz0,rz1,lx,lw,lz0,lz1,arc_x,arc_y=a
        pts={'O':(0.,0.,0.),'Lground':(lx,0.,0.)}
        for lab,xl,xr,yl,yr,z0,z1 in [('R',-rw/2,rw/2,0.,0.,rz0,rz1),('L',lx-lw,lx,0.,0.,lz0,lz1)]:
            pts.update({lab+'tl':(xl,yl,z1),lab+'tr':(xr,yr,z1),lab+'bl':(xl,yl,z0),lab+'br':(xr,yr,z0)})
        pts['At']=(lx-lw-arc_x,arc_y,lz1);pts['Ab']=(lx-lw-arc_x,arc_y,lz0)
        return pts
    def projection(s):
        ang=np.radians(s[0]);axes=np.array([[np.sin(ang),-np.cos(ang),0.],[np.cos(ang),np.sin(ang),0.],[0.,0.,1.]])
        o=np.array([s[1],s[2],0.]);out={};sp=sites(s[n:])
        for i,(k,rec)in enumerate(cams.items()):
            C=s[4+i*6:10+i*6];ctr=axes.T@(C[:3]-o);R=camera_axes(*C[3:])@axes;w,h=rec['size'];f=s[3] if k=='fayhoo' else w/(2*np.tan(np.radians(rec['hfov']/2)))
            K=np.array([[f,0,(w-1)/2],[0,f,(h-1)/2],[0,0,1.]])
            out[k]={'P':K@np.column_stack([R,-R@ctr]),'R':R,'K':K,'eye':ctr,'size':[w,h],'ENU_eye':C[:3],'az_pitch_roll':C[3:]}
        return out,sp
    def res(s,output=False):
        cs,p=projection(s);r=[];details={}
        for j,(k,rec) in enumerate(cams.items()):
            P=cs[k]['P'];det={}
            for ident,uv in rec['xy'].items():
                t=P@[*p[ident],1];e=t[:2]/t[2]-uv;det[ident]=e.tolist();sig=rec.get('overrides',{}).get(ident,rec['pixel_sigma']);r.extend(e/sig)
            details[k]=det
            if j:
                d=(s[4+j*6:10+j*6]-s0[4+j*6:10+j*6])/[.42,.42,.20,1.1,1.15,.85];r.extend(d)
        f=s[n:];r.extend([(s[0]-250)/8,(s[3]-3395)/145,(s[6]-1.56)/.24,(f[2]-f[1]-1.45)/.35,(f[3]+1.7)/1.,(f[7]-.20)/.12,(f[8]-.12)/.12])
        return details if output else np.array(r)
    lo=np.full_like(s0,-np.inf);hi=np.full_like(s0,np.inf);lo[:4]=[227,-12,-45,2850];hi[:4]=[277,22,4,3900]
    lo[n:]=[.45,.45,1.3,-4,.3,.45,1.3,.05,.03]
    hi[n:]=[1.80,1.8,4.0,-.6,1.7,1.8,4.,.7,.5]
    z=least_squares(res,s0,bounds=(lo,hi),x_scale='jac',loss='soft_l1',max_nfev=450);s=z.x;cs,ps=projection(s)
    def plain(v):return v.tolist() if isinstance(v,np.ndarray)else v
    residual=res(s,True)
    return {'x_azimuth_deg':s[0],'origin_wgs':(origin+s[1:3]/conv).tolist(),'axes':'Origin on outside ground under midpoint of right rectangular window; X right in Fayhoo 2015-04-04, Y inward, Z up.','parameters':s[n:].tolist(),'points':ps,'cameras':{k:{f:plain(v)for f,v in rec.items()}for k,rec in cs.items()},'residual_xy_px':residual,'median_residual_px':{k:float(np.median(np.linalg.norm(list(v.values()),axis=1)))for k,v in residual.items()}}
if __name__=='__main__':
    p=HERE/'wing-camera-observations.json';o=solve(json.loads(p.read_bytes()));(HERE/'wing-cameras.json').write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n');print(o['origin_wgs'],o['x_azimuth_deg'],o['parameters']);print(o['median_residual_px']);print([(k,np.round(v['eye'],2))for k,v in o['cameras'].items()])
