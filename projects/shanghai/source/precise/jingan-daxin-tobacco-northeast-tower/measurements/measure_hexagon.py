"""Fit the six-sided east tower to two July 2018 photographs and a later corner view."""
from pathlib import Path
import argparse
import json
from math import cos, pi, sin
import numpy as np
from scipy.optimize import least_squares

# Clockwise in the photographs. The corner arch is between vertices 0 and 1.
# Each figure is measured on the indicated working image, at its native aspect ratio.
VIEWS = [
    dict(photo='2018-07 上海パンダ，南立面', size=[638,478], azimuth=167, vertices=[4,5,0,1],
         cornice=[[484,91],[519,70],[577,61],[616,71]],
         sill=[[486,180],[519,166],[579,158],[620,165]],
         belt=[[487,291],[519,281],[583,278],[624,282]],
         parapet=[[488,65],[518,46],[573,37],[611,47]]),
    dict(photo='2018-07 上海パンダ，东端墙', size=[638,478], azimuth=282, vertices=[0,1,2,3],
         cornice=[[133,88],[164,67],[218,76],[256,95]],
         sill=[[135,171],[161,162],[220,166],[257,184]],
         belt=[[135,283],[159,278],[220,282],[257,291]],
         parapet=[[140,58],[180,31],[237,40],[253,63]]),
    dict(photo='2022年刊载的东角斜照', size=[638,381], azimuth=227, vertices=[5,0,1,2],
         cornice=[[315,95],[363,64],[424,65],[461,91]],
         sill=[[315,192],[363,175],[427,177],[465,197]],
         belt=[[316,322],[362,307],[430,310],[469,322]],
         parapet=[[323,65],[362,36],[423,35],[454,62]])]


def xyz(vertex, radius, height, scale):
    angle = (195+60*vertex)*pi/180
    return np.array([radius*scale*cos(angle),radius*scale*sin(angle),height])


def project(point, camera, size):
    azimuth, distance, eye, focal, yaw, pitch, roll = camera
    azimuth, yaw, pitch, roll = np.radians([azimuth,yaw,pitch,roll])
    position = np.array([distance*cos(azimuth),distance*sin(azimuth),eye])
    forward_h = np.array([-cos(azimuth+yaw),-sin(azimuth+yaw),0.])
    right = np.array([forward_h[1],-forward_h[0],0.])
    up = np.array([0.,0.,1.]); forward=cos(pitch)*forward_h+sin(pitch)*up
    vertical=cos(pitch)*up-sin(pitch)*forward_h
    delta=point-position
    x = delta.dot(right*cos(roll)+vertical*sin(roll))
    y = delta.dot(vertical*cos(roll)-right*sin(roll))
    z = max(delta.dot(forward),.1)
    return np.array([size[0]/2+focal*x/z,size[1]/2-focal*y/z])


def parameters(q):
    radius, upper, eave, top = q[:4]
    return radius,{'belt':(4.30,1.035),'sill':(upper,1.060),'cornice':(eave,1.066),'parapet':(top,.936)}


def observations(q):
    radius, levels=parameters(q)
    records=[]
    for j,view in enumerate(VIEWS):
        cam=q[4+7*j:11+7*j]
        for band, (height,scale) in levels.items():
            for vertex,mark in zip(view['vertices'],view[band]):
                point=xyz(vertex,radius,height,scale)
                image=project(point,cam,view['size'])
                records.append((j,band,vertex,np.array(mark),image))
    return records


def residuals(q):
    radius,levels=parameters(q)
    result=[v for _,_,_,point,image in observations(q) for v in (image-point)]
    # The district archive shows the garden face nearly front-on. Its measured
    # 5.94–7.79 m projected tower width sets the absolute scale; a hexagon at
    # the garden angle spans approximately 1.93 circumradii in projection.
    result.append((radius*1.93-6.86)/.22)
    for j,view in enumerate(VIEWS):
        az,dist,eye,focal,yaw,pitch,roll=q[4+7*j:11+7*j]
        result.extend([(eye-1.58)/.33,(focal-550)/180,(az-view['azimuth'])/10,roll/2])
    result.extend([(levels['sill'][0]-9.5)/1.5,(levels['cornice'][0]-15.0)/2.1,(levels['parapet'][0]-levels['cornice'][0]-1.3)/.50])
    return np.array(result)


def fit():
    lo=[3.10,7.4,12.3,13.4]; hi=[4.10,12.2,18.6,20.5]; guess=[3.56,10.0,15.4,16.9]
    for j,view in enumerate(VIEWS):
        angle=view['azimuth'];lo.extend([angle-26,9,1.1,290,-44,-5,-8]);hi.extend([angle+26,52,2.3,1150,44,44,8]);guess.extend([angle,22,1.62,550,[-20,11,-5][j],12,0]);
    optimum=least_squares(residuals,guess,bounds=(lo,hi),loss='soft_l1',f_scale=3,x_scale='jac',max_nfev=550)
    q=optimum.x; radius,levels=parameters(q); rows=[]
    for j,band,vertex,mark,image in observations(q):
        rows.append(dict(photo=j,band=band,vertex=vertex,observed=mark.tolist(),projected=image.round(2).tolist(),error_px=round(float(np.linalg.norm(mark-image)),3)))
    errors=[r['error_px']for r in rows]
    return dict(method='Shared six-sided polygon, floor bands and perspective cameras. The 4.30 m first belt and human camera height are estimates. The independent district archival frontal photograph and its 38.77 m site frontage suggest a projected turret width between 5.94 and 7.79 m. Top corners occluded by housing and utilities are interpreted from the visible cap edges.',local_axes='X increases along the short east end toward the paired windows. Y increases along the south garden frontage into the long wing. The local origin is the centre of the six-sided tower at grade.',hexagon_radius_m=round(radius,4),vertex_zero_angle_degrees=195,levels={k:dict(height_m=round(a,4),radius_factor=b)for k,(a,b)in levels.items()},
                cameras=[dict(source=v['photo'],size=v['size'],position_and_intrinsics=[round(x,6) for x in q[4+7*j:11+7*j]])for j,v in enumerate(VIEWS)],
                district_archive_reference=dict(garden_frontage_m=38.773,projected_width_interval_m=[5.94,7.79],representative_width_m=6.86,representative_width_for_this_hexagon_m=round(1.93*radius,4)),
                observations=rows,rms_px=round(float(np.sqrt(np.mean(np.square(errors)))),3),median_px=round(float(np.median(errors)),3),max_px=max(errors))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path);args=parser.parse_args()
    result=fit();args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result['hexagon_radius_m'],result['levels'],result['rms_px'],result['max_px'],result['district_archive_reference'],flush=True)
