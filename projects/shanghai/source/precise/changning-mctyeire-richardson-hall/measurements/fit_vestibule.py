"""Recover the northern vestibule wall and the two-storey space from Ctny's courtyard entrance photograph."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
HERE=Path(__file__).resolve().parent;REAR=13.20;HALF=3.78
FRAME=(1600,1067)
def matrix(parameters):
    x,y,z,yaw,tilt,roll,f=parameters[:7];eye=np.array([x,y,z])
    right=np.array([np.cos(yaw),-np.sin(yaw),0]);flat=np.array([np.sin(yaw),np.cos(yaw),0]);up=np.array([0.,0.,1.])
    forward=flat*np.cos(tilt)+up*np.sin(tilt);sky=up*np.cos(tilt)-flat*np.sin(tilt)
    u=right*np.cos(roll)+sky*np.sin(roll);v=right*np.sin(roll)-sky*np.cos(roll)
    def row(a):return np.r_[a,-a@eye]
    return np.stack([FRAME[0]/2*row(forward)+f*row(u),FRAME[1]/2*row(forward)+f*row(v),row(forward)])
def project(m,pt):
    v=m@[*pt,1]
    return v[:2]/v[2]
def fit():
    # Set the three rear doors to 4.65 m across. Their thickness and the outer room depth are conditional.
    def targets(p):
        h,deck,upper=p[7:];return [
            ([-2.325,REAR,.22],[711,994],True),([2.325,REAR,.22],[1162,994],True),
            ([-.83,REAR,.22],[849,993],False),([.9,REAR,.22],[1033,993],False),
            ([-2.32,REAR,h],[710,763],True),([2.32,REAR,h],[1141,753],True),
            ([-2.25,REAR,deck],[722,602],True),([2.16,REAR,deck],[1111,592],True),
            ([1.64,REAR,upper],[1050,403],True),([-1.75,REAR,upper],[765,415],False)]
    def err(p):
        m=matrix(p);a=[]
        for xyz,uv,trained in targets(p):
            if trained:a.extend(project(m,xyz)-uv)
        a.extend([(p[0]+.65)/.6,(p[2]-1.58)/.24,p[5]/.024,(p[6]-(1600*24/36))/34,(p[7]-2.67)/.16])
        return a
    init=[-.82,.64,1.61,-.035,.24,0,1067,2.68,4.2,6.39]
    sol=least_squares(err,init,bounds=([-3.5,.25,.75,-.5,-.05,-.09,360,2.3,3.5,5.2],[3.5,3.80,2.3,.5,.75,.09,1800,3.3,5.5,7.5]),loss='soft_l1',f_scale=3,x_scale='jac',max_nfev=2200)
    m=matrix(sol.x)
    return dict(frame=FRAME,photo='https://commons.wikimedia.org/wiki/File:Shanghai_No._3_Girls%27_High_School,_Five-Four_lecture_building_entrance.jpg',camera=sol.x.tolist(),projection=m.tolist(),rear_wall_y=REAR,assumed_half_width=HALF,
                exif_equivalent_lens_mm=24,frame_width_px=1600,scope='Principal entrance vestibule, facing the first-floor auditorium doors. 4.65 m aggregate rear-door width is a working scale inferred from the lawn entrance; room depth and lamp diameter are approximate.',
                controls=[dict(world=xyz,uv=uv,used_in_fit=train,error_px=float(np.linalg.norm(project(m,xyz)-uv)))for xyz,uv,train in targets(sol.x)])
def plane_point(m,u,v,axis,value):
    inv=np.linalg.inv(m[:,:3]);eye=-inv@m[:,3];ray=inv@[u,v,1]
    return eye+ray*((value-eye[axis])/ray[axis])
if __name__=='__main__':
    d=fit();(HERE/'vestibule-station.json').write_text(json.dumps(d,indent=2)+'\n');print(d['camera'],[(c['uv'],round(c['error_px'],1))for c in d['controls']])
