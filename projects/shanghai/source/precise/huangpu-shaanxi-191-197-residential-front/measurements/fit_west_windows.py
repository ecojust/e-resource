"""Metric estimate from the 2018 WQL photograph and independent public street panoramas."""
import json
import math
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

HERE=Path(__file__).resolve().parent
REFERENCE=[121.45637232691024,31.21529491689353]
ORIGINAL='2018_commons'
def read():
    return json.loads((HERE/'west-upper-window-observations.json').read_text())
def camera(yaw,pitch,roll,f,width,height,eye):
    a,p,r=np.radians([yaw,pitch,roll]);sa,ca,sp,cp=np.sin(a),np.cos(a),np.sin(p),np.cos(p)
    forward=np.array([sa*cp,ca*cp,sp]);right=np.array([ca,-sa,0]);up=np.cross(right,forward)
    rot=np.array([right*np.cos(r)+up*np.sin(r),right*np.sin(r)-up*np.cos(r),forward])
    K=np.array([[f,0,width/2],[0,f,height/2],[0,0,1.]])
    return K@rot@np.column_stack((np.eye(3),-np.asarray(eye)))
def build(params,j,stations):
    e,n,az,d,width,h,bottom=params[:7]
    a=np.radians(az);X=np.array([np.sin(a),np.cos(a),0]);Y=np.array([-np.cos(a),np.sin(a),0]);Z=np.array([0.,0.,1.])
    basis=np.eye(4);basis[:3,:3]=np.array([X,Y,Z]).T;basis[:3,3]=[e,n,0.]
    cameras={};start=7
    for t in stations:
        s=j['panoramas'][t];lon,lat=s['station']['position']
        eye=[(lon-REFERENCE[0])*111320*np.cos(np.radians(REFERENCE[1])),(lat-REFERENCE[1])*110870,s['station']['height']]
        da,dp,dr=params[start:start+3];start+=3
        f=.5*s['width']/np.tan(np.radians(s['hfov']/2))
        cameras[t]=camera(s['az']+da,s['pitch']+dp,dr,f,s['width'],s['height'],eye)@basis
    sx,sy,sz,yaw,pitch,roll=params[start:start+6]
    f=28/np.hypot(36,24)*np.hypot(4160,3120)
    cameras[ORIGINAL]=camera(yaw,pitch,roll,f,4160,3120,[sx,sy,sz])
    xyz={}
    for bay,sign in [('N',-1),('S',1)]:
        for v,z in [('T',bottom+h),('B',bottom)]:
            for side,half in [('L',-width/2),('R',width/2)]:
                xyz[bay+v+side]=[sign*d/2+half,0,z,1]
    return xyz,cameras
def fit(j,stations):
    params=[-5,-7.0,157,4.50,1.66,1.31,5.85]+[0]*len(stations)*3+[.2,-18,1.65,0,5,0]
    def residual(v):
        xyz,cam=build(v,j,stations);r=[]
        for t,M in cam.items():
            for k,uv in j['corners'][t].items():
                p=M@xyz[k];r.extend((p[:2]/p[2]-uv)/j['pixel_uncertainty'][t])
        for a,p,roll in np.reshape(v[7:7+3*len(stations)],(-1,3)):
            r.extend((a/1.2,p/1.7,roll/1.0))
        r.extend(((v[-4]-1.65)/.45,(v[2]-161)/10.))
        return r
    result=least_squares(residual,params,x_scale='jac',loss='soft_l1',f_scale=1.7,max_nfev=200)
    return result.x
def main():
    j=read();stations=list(j['panoramas']);v=fit(j,stations);xyz,cameras=build(v,j,stations)
    errors={}
    for view,M in cameras.items():
        errors[view]={}
        for k,uv in j['corners'][view].items():
            pred=M@xyz[k];errors[view][k]=list(np.round(pred[:2]/pred[2]-uv,2))
    sensitivities={}
    for excluded in stations:
        subset=[s for s in stations if s!=excluded];sensitivities[excluded]=np.round(fit(j,subset)[2:7],4).tolist()
    out={'coordinates':'X right/south, Y inside/east, Z above approximate public street grade. X=0 halfway between upper windows; Y=0 on observed upper-frame exterior face. Wall/outer faces lie within the unmeasured frame setback.','registration':'Public station positions, head heights, bearing, separation and field of view set the metric scale. The 2018 camera uses 28mm equivalent EXIF and a 1.65 +/- 0.45m eye-height prior. A shared rectangular aperture size is fitted to the two observed window assemblies, with separate residuals for each corner. Station vertical and heading adjustments are penalized.','metric_measured':{'approx_x_bearing_deg':v[2],'axis_spacing_m':v[3],'opening_width_m':v[4],'opening_height_m':v[5],'frame_bottom_above_grade_m':v[6]},'leave_one_station_out_bearing_spacing_width_height_bottom':sensitivities,'corners':{k:x[:3] for k,x in xyz.items()},'photographic_cameras':{s:M.tolist() for s,M in cameras.items()},'station_bearing_pitch_roll_corrections_deg':dict(zip(stations,v[7:7+3*len(stations)].reshape(-1,3).tolist())),'primary_camera':{'local_eye':v[-6:-3].tolist(),'yaw_pitch_roll_deg':v[-3:].tolist()},'residuals_original_pixels':errors}
    (HERE/'west-upper-window-calibration.json').write_text(json.dumps(out,indent=2)+'\n')
    print(out['metric_measured'],out['primary_camera']);print(sensitivities);print(errors)
if __name__=='__main__':
    main()
