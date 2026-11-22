"""Register both visible walls and their cornice to the oriented 2014 photograph."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares

HERE=Path(__file__).absolute().parent
# Coordinates are pixels in the upright crop. The original's EXIF orientation is 6.
centre=np.array([1224-738,1632-672],float)
def camera(params):
    yaw,pitch,roll,focal,distance,u0,v0=params[:7]
    right=np.array([np.cos(yaw),np.sin(yaw),0.])
    forward=np.array([-np.sin(yaw)*np.cos(pitch),np.cos(yaw)*np.cos(pitch),np.sin(pitch)])
    down=np.cross(forward,right)
    rotation=np.array([np.cos(roll)*right+np.sin(roll)*down,-np.sin(roll)*right+np.cos(roll)*down,forward])
    offset=np.r_[(np.array([u0,v0])-centre)/focal,1]*distance
    K=np.array([[focal,0,centre[0]],[0,focal,centre[1]],[0,0,1.]])
    return K@np.column_stack([rotation,offset]),-rotation.T@offset

def geometry(p):
    left,width,height,span,depth,band,y0,y1,z0,z1=p[7:]
    xyz=np.array([
        [left,0,1.55],[left+width,0,1.55],[left+width,0,0],[left,0,0],
        [-span,0,height],[0,0,height],[0,depth,height],
        [-span,0,height-band],[0,0,height-band],[0,depth,height-band],
        [0,y0,z1],[0,y1,z1],[0,y1,z0],[0,y0,z0]])
    # The lower trim disappears behind the neighbouring tile roof before the upper trim.
    # Its terminal pixel therefore has its own depth on the return wall.
    proj,_=camera(p);u=1311
    bx=proj[:,2]*(height-band)+proj[:,3]
    xyz[9,1]=(u*bx[2]-bx[0])/(proj[0,1]-u*proj[2,1])
    return xyz

points=np.array([[568,297],[745,264],[748,538],[571,569],
                 [153,267],[863,132],[1334,350],[156,323],[860,194],[1311,382],
                 [931,293],[1005,322],[1009,493],[934,465]])
weights=np.array([2.4]*4+[3,3,6,3,3,8,4,4,4,5])
def project(P,X):
    q=np.c_[X,np.ones(len(X))]@P.T
    return q[:,:2]/q[:,2,None]
def residual(p):
    prediction=project(camera(p)[0],geometry(p))
    return np.r_[((prediction-points)/weights[:,None]).ravel(),
                 (p[3]-2650)/380,p[2]/.045]
seed=[.52,.25,0,2650,17.,864,519,-1.9,1.22,2.22,4.8,6.2,.31,.55,1.6,.12,1.11]
lower=[.05,-.08,-.12,1650,5,820,470,-4,.55,1.65,3,2,.17,.15,.8,-.45,.66]
upper=[1.26,.75,.12,3750,34,900,576,-.9,2.5,3.1,8.2,11,.55,1.8,3.6,.60,1.65]
if __name__=='__main__':
    solutions=[least_squares(residual,[q,*seed[1:]],bounds=(lower,upper),max_nfev=1800) for q in [.26,.54,.9]]
    fit=min(solutions,key=lambda s:s.cost);p=fit.x;P,eye=camera(p);q=project(P,geometry(p));d=p[7:]
    print('residuals',np.round(q-points,2),'parameters',np.round(p,5),'eye',eye,flush=True)
    f=HERE/'photographic-source.json';r=json.loads(f.read_bytes())
    names=['front_window_left','front_window_width','roof_level','front_width','return_depth','cornice_height',
           'return_window_near','return_window_far','return_window_bottom','return_window_top']
    dimensions={k:float(v)for k,v in zip(names,d)}
    dimensions['front_window_bottom']=0.;dimensions['front_window_top']=1.55
    labels=['front opening top left','front opening top right','front opening bottom right','front opening bottom left',
            'top front left','top corner','top side far','bottom front left','bottom corner','bottom side at adjoining roof',
            'return sash top near','return sash top far','return sash bottom far','return sash bottom near']
    data=dict(photo_sha256=r['sha256'],source_crop_sha256=r['crop_sha256'],upright_crop_origin_px=[738,672],assumed_front_window_height_m=1.55,
      focal_prior_px={'centre':2650,'standard_deviation':380,'role':'broad estimate for this camera, with original EXIF focal length 3.7 mm'},
      return_extent_note='The cropped termination of the rear wall and the concealed roof top use estimated limits. The lower cornice meets the foreground tiled roof before the upper cornice.',fitted_focal_px=p[3],camera_eye_enu_m=eye.tolist(),world_to_crop=P.tolist(),
      controls=[dict(name=n,actual_px=xy.tolist(),predicted_px=pp.tolist(),residual_px=(pp-xy).tolist(),local_xyz=x.tolist())for n,xy,pp,x in zip(labels,points,q,geometry(p))],
      photographed_dimensions=dimensions,weighted_cost=fit.cost,model_scale='All dimensions conditional on estimated 1.55 m height of the front steel window.')
    (HERE/'roof-room-camera.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    (HERE.parent/'source/dimensions.json').write_text(json.dumps(dimensions,ensure_ascii=False,indent=2)+'\n')
