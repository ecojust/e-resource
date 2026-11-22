"""Refit the photographed tower using four street stations and the published original-pixel pairs."""
from pathlib import Path
import argparse
import json
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

HERE=Path(__file__).resolve().parent
STATIONS=('confirmed-march15','confirmed-dec15','confirmed-n20','far-nw15')
WGS_ORIGIN=np.array([121.44281781,31.22851456])
METRES_PER_DEGREE=np.array([111320*np.cos(np.deg2rad(WGS_ORIGIN[1])),110900])

def local_geometry(pixels,parameters,plane):
    u=pixels[:,0]-478.5
    upper=plane=='upper'
    reference_v=146.5 if upper else 373.
    px_per_metre=(2.855 if upper else 2.890)/.065
    x=u/(px_per_metre*parameters[4])+parameters[5]*(pixels[:,1]-reference_v)/44.4+upper*parameters[8]
    z=(parameters[3]+(373.-reference_v)/(2.875/.065)
       +(reference_v-pixels[:,1])/px_per_metre+parameters[6]*u/44.4+upper*parameters[9])
    return np.column_stack((x,np.full(len(x),parameters[7] if upper else 0.),z,np.ones(len(x))))

def projection(key,records,parameters):
    camera=records['images'][key]
    k=10+3*STATIONS.index(key)
    az,pitch,field=camera['projection']
    az,pitch,roll=np.deg2rad([az+parameters[k],pitch+parameters[k+1],parameters[k+2]])
    right=np.array([np.cos(az),-np.sin(az),0])
    forward=np.array([np.sin(az)*np.cos(pitch),np.cos(az)*np.cos(pitch),np.sin(pitch)])
    up=np.cross(right,forward)
    rotation=Rotation.from_rotvec([0,0,roll]).as_matrix()@np.array([right,-up,forward])
    width,height=camera['native_width_height']
    focal=width/(2*np.tan(np.deg2rad(field/2)))
    K=np.array([[focal,0,width/2],[0,focal,height/2],[0,0,1.]])
    heading=np.deg2rad(parameters[2])
    axes=np.array([[np.sin(heading),-np.cos(heading),0],
                   [np.cos(heading),np.sin(heading),0],[0,0,1.]])
    # All four camera records identify the lens as 2.32 m above its local road.
    eye_enu=np.r_[(camera['station_wgs']-WGS_ORIGIN)*METRES_PER_DEGREE,2.32]
    return K@np.column_stack((rotation@axes,rotation@(np.r_[parameters[:2],0]-eye_enu)))

def fit(records,common_plane=False):
    def residual(p,return_held=False):
        objective=[];held={}
        for key in STATIONS:
            camera=projection(key,records,p)
            for tier in ('lower','upper'):
                pairs=np.array(records['source_control_points'][key][tier])
                training=np.arange(len(pairs))%4!=2
                expected=local_geometry(pairs[:,:2],p,tier)@camera.T
                differences=expected[:,:2]/expected[:,2:]-pairs[:,2:]
                objective.extend((differences[training]/1.45).ravel())
                held[key+' / '+tier]=np.linalg.norm(differences[~training],axis=1).tolist()
        if return_held:return held
        objective.extend([p[0]/10,p[1]/10,(p[2]-160.59)/14,(p[3]-10)/10,
                          (p[4]-1)/.025,p[5]/.014,p[6]/.014,(p[7]-.38)/.9,p[8]/.25,p[9]/.35])
        objective.extend(p[10:]/np.tile([2.25,1.,.71],len(STATIONS)))
        if common_plane:objective.append(p[7]/.006)
        return objective
    seed=np.r_[0,0,160.59,10.,1.,0.,0.,.45,0.,0.,np.zeros(3*len(STATIONS))]
    free=least_squares(residual,seed,x_scale='jac',max_nfev=180,loss='soft_l1',f_scale=1.5 if common_plane else 1.4)
    p=free.x
    return dict(x_axis_bearing_deg=float(p[2]),middle_sill_reference_z_m=float(p[3]),
                upper_tier_relative_y_m=float(p[7]),mean_scale_coefficient=float(p[4]),
                holdout_px=residual(p,True),
                stations={k:projection(k,records,p).tolist() for k in STATIONS})

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path);args=ap.parse_args()
    inputs=json.loads((HERE/'tower-front-cameras.json').read_text())
    args.output.write_text(json.dumps({'independent_depth':fit(inputs),'common_face':fit(inputs,True)},indent=1)+'\n')
