#!/usr/bin/env python3
"""Calibrated single-plane metric rectification for photo proportion checks.

Input lines/points use EXIF-oriented pixel centers. Source JPEG bytes are never
changed. This estimates one facade plane, not a surveyed building or a 3-D scan.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation


def homogeneous(point):
    return np.array([*point,1.],float)


def project(matrix, points):
    values=np.asarray(points,float)
    single=values.ndim==1
    values=values.reshape(-1,2)
    mapped=np.c_[values,np.ones(len(values))]@np.asarray(matrix).T
    result=mapped[:,:2]/mapped[:,2,None]
    return result[0] if single else result


def line(a,b):
    result=np.cross(homogeneous(a),homogeneous(b))
    return result/np.linalg.norm(result[:2])


def intersection(a,b):
    point=np.cross(a,b)
    if abs(point[2])<1e-12:raise ValueError('Control lines have no finite intersection')
    return point[:2]/point[2]


def intrinsics(raw_size, sensor_mm, focal_mm, orientation=6, principal_delta=(0,0)):
    width,height=raw_size;sw,sh=sensor_mm
    raw=np.array([[focal_mm*width/sw,0,(width-1)/2],[0,focal_mm*height/sh,(height-1)/2],[0,0,1.]])
    if orientation==6:
        # Discrete pixel-center rotation: stored (x,y) -> (height-1-y,x).
        orient=np.array([[0,-1,height-1],[1,0,0],[0,0,1.]])
        camera=np.array([[raw[1,1],0,(height-1)/2],[0,raw[0,0],(width-1)/2],[0,0,1.]])
        oriented_size=[height,width]
    elif orientation==1:
        orient=np.eye(3);camera=raw.copy();oriented_size=[width,height]
    else:raise ValueError('This audited helper supports EXIF orientations 1 and 6')
    camera[:2,2]+=principal_delta
    return {'raw':raw,'oriented':camera,'stored_to_oriented':orient,'oriented_to_stored':np.linalg.inv(orient),'oriented_size':oriented_size}


def fit_pose(camera, groups):
    normals=[];weights=[]
    for group in groups:
        row=[];weight=[]
        for segment in group:
            a,b=np.asarray(segment['points'],float)
            normal=camera.T@line(a,b);normal/=np.linalg.norm(normal)
            row.append(normal);weight.append(np.linalg.norm(a-b))
        normals.append(np.asarray(row));weights.append(np.asarray(weight)/max(weight))
    estimates=[np.linalg.svd(n)[2][-1] for n in normals]
    if estimates[0][0]<0:estimates[0]*=-1
    if estimates[1][1]>0:estimates[1]*=-1
    basis=np.column_stack([*estimates,np.cross(*estimates)])
    left,_,right=np.linalg.svd(basis);basis=left@right
    if np.linalg.det(basis)<0:basis[:,2]*=-1
    def residual(vector):
        matrix=Rotation.from_rotvec(vector).as_matrix()
        return np.concatenate([(normals[i]@matrix[:,i])*weights[i] for i in range(2)])
    solution=least_squares(residual,Rotation.from_matrix(basis).as_rotvec(),loss='soft_l1',f_scale=.003,xtol=1e-12,ftol=1e-12,gtol=1e-12)
    matrix=Rotation.from_rotvec(solution.x).as_matrix();horizontal=matrix[:,0];vertical=matrix[:,1]
    if horizontal[0]<0:horizontal=-horizontal
    if vertical[1]>0:vertical=-vertical
    forward=-np.cross(horizontal,vertical)
    if forward[2]<0:raise ValueError('Pose does not face the image camera')
    errors=[]
    for group,direction in zip(groups,[horizontal,vertical]):
        vanish=camera@direction
        for segment in group:
            points=np.asarray(segment['points']);midpoint=homogeneous(points.mean(0))
            predicted=np.cross(midpoint,vanish);predicted/=np.linalg.norm(predicted[:2])
            distances=np.abs(np.c_[points,np.ones(2)]@predicted)
            errors.append({'label':segment['label'],'endpoint_residual_px':distances.tolist()})
    return horizontal,vertical,forward,errors


def calibrate(controls, focal_scale=1., principal_delta=(0,0), noise=None):
    data=json.loads(json.dumps(controls));rng=noise
    if rng is not None:
        sigma=data['uncertainty']['line_endpoint_sigma_px']
        for key in ('horizontal_lines','vertical_lines'):
            for segment in data[key]:segment['points']=(np.array(segment['points'])+rng.normal(0,sigma,(2,2))).tolist()
        for edge in data['width_edge_lines']:
            edge['points']=(np.array(edge['points'])+rng.normal(0,data['uncertainty']['corner_edge_sigma_px'],(2,2))).tolist()
        data['ground_reference']['point']=(np.array(data['ground_reference']['point'])+rng.normal(0,data['uncertainty']['ground_sigma_px'],2)).tolist()
        for point in data['height_points']:
            point['point']=(np.array(point['point'])+rng.normal(0,data['uncertainty']['height_point_sigma_px'],2)).tolist()
    camera=intrinsics(data['raw_size'],data['sensor_mm'],data['focal_mm']*focal_scale,data['exif_orientation'],principal_delta)
    K=camera['oriented'];u,z,forward,errors=fit_pose(K,[data['horizontal_lines'],data['vertical_lines']])
    rectifier=np.vstack([u,z,forward])@np.linalg.inv(K)
    vanishing_h=K@u;vanishing_v=K@z
    ground_line=np.cross(homogeneous(data['ground_reference']['point']),vanishing_h)
    ground_corners=[intersection(line(*edge['points']),ground_line) for edge in data['width_edge_lines']]
    q=project(rectifier,ground_corners)
    measured=q[1,0]-q[0,0]
    if measured<=0:raise ValueError('Width corners are not ordered left-to-right')
    width=data['front_width_m']
    if rng is not None:width+=rng.normal(0,data['uncertainty']['width_sigma_m'])
    scale=width/measured;origin=q.mean(0)
    metric=np.array([[scale,0,-scale*origin[0]],[0,scale,-scale*origin[1]],[0,0,1.]])@rectifier
    metric/=metric[2,2]
    translation=scale*(forward+origin[0]*u+origin[1]*z)
    # Facade d is outward toward the camera, hence -forward.
    projection=K@np.column_stack([u,z,-forward,translation])
    values=[]
    for p in data['height_points']:
        uz=project(metric,p['point']);ray=np.linalg.inv(K)@homogeneous(p['point']);ray/=np.linalg.norm(ray)
        interval=p.get('depth_range_m',[-p.get('depth_uncertainty_m',0),p.get('depth_uncertainty_m',0)])
        qz=(uz[1]+scale*origin[1])/scale
        heights=sorted(float(uz[1]-d*qz) for d in interval)
        values.append({'label':p['label'],'oriented_pixel':p['point'],'facade_u_z_m':uz.tolist(),
             'height_over_front_width':float(uz[1]/width),
             'normalized_camera_ray':ray.tolist(),'plane_status':p['plane_status'],
             'assumed_depth_interval_m':interval,'conditional_depth_height_interval_m':heights,
             'height_change_per_outward_m':-float(qz)})
    def finite_vp(v):return {'homogeneous':v.tolist(),'pixel':(v[:2]/v[2]).tolist() if abs(v[2])>1e-10 else None}
    return {'oriented_pixel_to_facade_u_z':metric.tolist(),'facade_u_z_to_oriented_pixel':np.linalg.inv(metric).tolist(),
        'facade_u_z_d_to_oriented_pixel_projection_3x4':projection.tolist(),
        'stored_pixel_to_facade_u_z':(metric@camera['stored_to_oriented']).tolist(),
        'camera_intrinsics_oriented':K.tolist(),'camera_intrinsics_stored':camera['raw'].tolist(),
        'stored_to_oriented_pixel':camera['stored_to_oriented'].tolist(),'oriented_to_stored_pixel':camera['oriented_to_stored'].tolist(),
        'directions_camera':{'facade_u':u.tolist(),'world_up':z.tolist(),'facade_outward_d':(-forward).tolist()},
        'camera_position_facade_u_z_d_m':[-scale*origin[0],-scale*origin[1],scale],
        'vanishing_points':{'horizontal':finite_vp(vanishing_h),'vertical':finite_vp(vanishing_v)},
        'ground_corners_oriented_px':[p.tolist() for p in ground_corners],
        'ground_corners_are_extrapolated':True,'front_width_m':width,'line_fit':errors,
        'line_endpoint_rms_px':float(np.sqrt(np.mean([d*d for e in errors for d in e['endpoint_residual_px']]))),
        'height_points':values}


def make_figure(controls,result,image_path,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    image=ImageOps.exif_transpose(Image.open(image_path)).convert('RGB')
    proxy=image.copy();proxy.thumbnail((1280,1920))
    ratio=image.width/proxy.width
    fig,axes=plt.subplots(1,2,figsize=(15,11),dpi=120)
    ax=axes[0];ax.imshow(proxy)
    for key,color in [('horizontal_lines','#00e5ff'),('vertical_lines','#ffab40'),('width_edge_lines','#ff44ff')]:
        for segment in controls[key]:
            p=np.array(segment['points'])/ratio;ax.plot(p[:,0],p[:,1],color=color,linewidth=1.15)
    for number,point in enumerate(result['height_points'],1):
        x,y=np.array(point['oriented_pixel'])/ratio
        ax.scatter(x,y,s=16,color='yellow',edgecolors='black',linewidths=.35)
        ax.text(x+6,y,str(number),fontsize=7,color='black',bbox={'facecolor':'white','alpha':.7,'pad':.4})
    ground=np.array(controls['ground_reference']['point'])/ratio;ax.scatter(*ground,color='red',marker='+',s=80)
    ax.set_title('Original orientation + selected controls\ncyan: horizontal; orange: vertical; magenta: width boundaries',fontsize=10)
    ax.set_xlabel('1280-pixel inspection proxy (source remains 3456 x 5184 oriented)')
    width=controls['front_width_m'];xmin,xmax=-width/2,width/2
    zmax=max(p['facade_u_z_m'][1] for p in result['height_points'])+1
    pixels_per_m=24;w=int(math.ceil(width*pixels_per_m));h=int(math.ceil(zmax*pixels_per_m))
    target_to_metric=np.array([[(xmax-xmin)/w,0,xmin],[0,-zmax/h,zmax],[0,0,1.]])
    sample=np.asarray(result['facade_u_z_to_oriented_pixel'])@target_to_metric;sample/=sample[2,2]
    rectified=image.transform((w,h),Image.Transform.PERSPECTIVE,tuple(sample.flat)[:8],resample=Image.Resampling.BICUBIC)
    ax=axes[1];ax.imshow(rectified,extent=[xmin,xmax,0,zmax]);ax.set_aspect('equal')
    for number,point in enumerate(result['height_points'],1):
        u,z=point['facade_u_z_m'];ax.scatter(u,z,s=16,color='yellow',edgecolors='black',linewidths=.35)
        ax.text(u+.15,z,str(number),fontsize=7,color='black',bbox={'facecolor':'white','alpha':.7,'pad':.4})
    ax.set_ylim(0,zmax);ax.set_xlim(xmin,xmax);ax.set_xlabel('nominal facade u (m)');ax.set_ylabel('nominal plane z (m)')
    ax.set_title('Analysis rectification of the nominated front plane\nroof offsets / projecting bays are NOT corrected',fontsize=10)
    ax.grid(alpha=.25)
    fig.suptitle('Single-photo proportion check — approximate controls and intrinsics; not a survey',fontsize=12)
    fig.text(.5,.015,'Photo: Suicasmo, CC0-1.0. Analysis derivative only; original JPEG bytes unchanged. Flagpoles excluded.',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.035,1,.95]);fig.savefig(output);plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('controls',type=Path);parser.add_argument('--samples',type=int,default=256)
    args=parser.parse_args();controls=json.loads(args.controls.read_text());result=calibrate(controls)
    generator=np.random.default_rng(20261026);samples=[]
    for _ in range(args.samples):
        sampled=calibrate(controls,focal_scale=1+generator.normal(0,controls['uncertainty']['focal_scale_sigma']),
            principal_delta=generator.normal(0,controls['uncertainty']['principal_point_sigma_px'],2),noise=generator)
        samples.append([p['facade_u_z_m'][1] for p in sampled['height_points']])
    values=np.array(samples)
    for i,item in enumerate(result['height_points']):
        item['sensitivity_5_95_percentile_m']=np.percentile(values[:,i],[5,95]).tolist()
        correction=np.asarray(item['conditional_depth_height_interval_m'])-item['facade_u_z_m'][1]
        item['sensitivity_plus_assumed_depth_envelope_m']=(np.percentile(values[:,i],[5,95])+correction).tolist()
    image_path=(args.controls.parent/controls['image']).resolve()
    image=Image.open(image_path);exif=image.getexif();details=exif.get_ifd(34665)
    assert image.size==tuple(controls['raw_size']) and exif.get(274)==controls['exif_orientation']
    assert abs(float(details[37386])-controls['focal_mm'])<1e-9
    derived_sensor=[image.width*25.4/float(details[41486]),image.height*25.4/float(details[41487])]
    result.update({'schema':'single-plane-photo-proportion-check-v1',
        'status':'independent approximate single-photo geometry; not a survey or calibrated photogrammetric reconstruction',
        'source_image':{'file':controls['image'],'sha256':hashlib.sha256(image_path.read_bytes()).hexdigest(),'stored_size':list(image.size),'exif_orientation':image.getexif().get(274)},
        'controls_file':args.controls.name,'controls_sha256':hashlib.sha256(args.controls.read_bytes()).hexdigest(),
        'controls':controls,'sensitivity_samples':args.samples,'uncertainty_note':'Percentiles propagate the stated point/focal/principal/width assumptions only; they are not a statistical measurement confidence interval and do not include unidentified plane offsets/lens editing.',
        'sensitivity_random_seed':20261026,
        'camera_evidence':{'make':exif.get(271),'model':exif.get(272),'focal_length_mm':float(details[37386]),
            'sensor_mm_used':controls['sensor_mm'],'official_source':controls['sensor_source'],'official_quote':controls['sensor_source_quote'],
            'exif_focal_plane_implied_sensor_mm':derived_sensor,
            'intrinsic_limitations':'Canon calls the sensor size approximate. EXIF focal-plane resolution implies ~22.71 x 15.16 mm, about 1.8% larger; the sensitivity run varies focal scale by 2% sigma. Principal point is assumed at image center; distortion and any undocumented edits were not calibrated.'},
        'mapping_contract':{'pixel_coordinate_origin':'top-left pixel center (0,0), oriented image 3456x5184',
            'facade_origin':'midpoint of the two extrapolated mapped front-edge base corners at the nominated ground line',
            'u':'left to right as seen in this source photo; corresponds to frozen CCW front-edge tangent after identity review',
            'z':'world up in metres','d':'outward from the facade plane toward camera; positive values project with the explicit 3x4 matrix',
            'domain':'One nominated facade plane only. Side returns, projecting bays, recessed glass, cornice faces and roof setbacks require their actual d or separate calibration. No entire-image wall projection is authorized.'},
        'tool_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    result['window_quad_checks']=[]
    for window in controls.get('window_quads',[]):
        q=project(result['oriented_pixel_to_facade_u_z'],window['points'])
        result['window_quad_checks'].append({'label':window['label'],'oriented_pixels':window['points'],'facade_u_z_m':q.tolist(),
            'width_m':float(np.mean([q[1,0]-q[0,0],q[2,0]-q[3,0]])),
            'height_m':float(np.mean([q[0,1]-q[3,1],q[1,1]-q[2,1]])),
            'center_u_m':float(q[:,0].mean()),'bottom_z_m':float(q[2:,1].mean()),'status':window['status']})
    result['source_image'].update(controls.get('source_license',{}))
    result['texture_registration_status']='Initialization only. Horizontal origin/plane correspondence remains approximate, especially Bund05 asymmetrical mapped corner steps (~0.4 m possible offset). Register actual aperture corners before publication; never project lamps, people, foliage or side/roof pixels onto the wall.'
    result['landmark_summary']=controls.get('landmark_summary',{})
    make_figure(controls,result,image_path,args.controls.with_name('calibration-independent-comparison.png'))
    output=args.controls.with_name('calibration-independent.json');output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'file':str(output),'rms_px':result['line_endpoint_rms_px'],'camera':result['camera_position_facade_u_z_d_m'],'heights':result['height_points']},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
