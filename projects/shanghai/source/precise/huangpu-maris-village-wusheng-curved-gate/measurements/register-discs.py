"""Register the four physical circles across three dated spherical street cameras."""
import argparse
import json
import sys
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

STATIONS={
    '2017':dict(origin=[-512,1154],north=176.95,gps=[121.46675531126961,31.22952741881757],id='09000300121710141031291991A'),
    '2020':dict(origin=[7351,1154],north=176.98,gps=[121.46671774011405,31.229533318995816],id='09000300122002221044155365O'),
    '2021':dict(origin=[7460,1694],north=176.04,gps=[121.46673477710402,31.22953083261715],id='09000300122101081146116647I')}
LEVEL=-.025
def observations(ellipses,mounted):
    output={}
    for date,station in STATIONS.items():
        if date=='2021':
            points=[np.array(d['observed_rim_pixels']) for d in mounted]
        else:
            points=[np.array(d['edge_points'])for d in ellipses[date]['plates']]
        rows=[]
        for p in points:
            if date=='2021':p=(p+.5)*[1280/893,760/530]
            full=p+station['origin']
            azimuth=full[:,0]*(2*np.pi/8192)-np.deg2rad(station['north'])
            elevation=np.pi/2-full[:,1]*(2*np.pi/8192)
            rows.append((azimuth,np.tan(elevation)))
        output[date]=rows
    return output
def intersection(az, slope, camera, axes):
    cx,cy,cz,yaw=camera
    unit=np.stack((np.sin(az+yaw),np.cos(az+yaw),slope),axis=-1)
    dx=unit@axes[0];dy=unit@axes[1];dz=unit@axes[2]
    travel=(LEVEL-cy)/dy
    return cx+dx*travel,cz+dz*travel
def optimize(axes,eye,ellipses,mounted):
    data=observations(ellipses,mounted)
    discs=np.array([[*s['centre_xz_m'],s['radius_m']]for s in mounted])
    ref=np.array(STATIONS['2021']['gps'])
    start={d:np.array(eye)for d in STATIONS}
    for key in ('2017','2020'):
        delta=(np.asarray(STATIONS[key]['gps'])-ref)*[111319.5*np.cos(np.deg2rad(ref[1])),111132.]
        start[key]=np.r_[eye+np.asarray(axes)@np.r_[delta,0.],0.]
    def decode(p):
        circles=p[:12].reshape((4,3))
        cameras=dict(zip(('2017','2020'),p[12:].reshape((2,4))))
        cameras['2021']=np.r_[eye,0.]
        return circles,cameras
    def evaluate(p,groups=False):
        circles,cameras=decode(p);parts=[]
        for key,stations in data.items():
            for (ux,uz,r),(a,t)in zip(circles,stations):
                x,z=intersection(a,t,cameras[key],axes)
                parts.append(np.hypot(x-ux,z-uz)-r)
        if groups:return parts
        # The independently geocoded cameras initialize the fit. A small
        # heading prior stabilizes the weak translation/heading coupling.
        heading=np.array([cameras[k][3]*.35 for k in ['2017','2020']])
        return np.concatenate([*parts,heading])
    initial=np.r_[discs.ravel(),start['2017'],start['2020']]
    solved=least_squares(evaluate,initial,loss='soft_l1',f_scale=.010,max_nfev=150)
    circles,cameras=decode(solved.x)
    residuals=evaluate(solved.x,True)
    return {'plane_y_m':LEVEL,'stations':{date:{**STATIONS[date],'camera_xyz_yaw':np.round(cam,7).tolist()}for date,cam in cameras.items()},
            'letters':[dict(character=label,centre_xz_m=np.round(pos[:2],6).tolist(),radius_m=round(pos[2],6))for label,pos in zip('重新小区',circles)],
            'rim_residuals':{k:[{'points':len(x),'median_m':round(float(np.median(np.abs(x))),6),'p90_m':round(float(np.percentile(np.abs(x),90)),6)} for x in residuals[i*4:(i+1)*4]] for i,k in enumerate(data)}}
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for field in ('source','ellipses','mounted','output'):ap.add_argument('--'+field,required=True,type=Path)
    a=ap.parse_args();sys.path.insert(0,str(a.source))
    from photo_plane import axes,eye
    result=optimize(axes,eye,json.loads(a.ellipses.read_bytes()),json.loads(a.mounted.read_bytes()))
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['letters'],result['rim_residuals'])
