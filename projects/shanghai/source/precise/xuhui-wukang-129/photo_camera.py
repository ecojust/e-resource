#!/usr/bin/env python3
"""Apply the locked129 photo camera to an already loaded ENU native scene.

Normal Python (never starts Blender):
  python photo_camera.py --check --report output/photo-camera-check.json

In the parent's single Blender queue, after blender_finish.py:
  blender -b output/xuhui-wukang-129-raw.blend --python photo_camera.py -- \
    --render output/photo-camera.png --width 1500 \
    --save-blend output/photo-camera.blend --report output/photo-camera-run.json

A loaded native's blender_finish report is verified before camera changes. Geometry,
lighting and material nodes are not modified. No look-at is applied.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

import numpy as np

HERE=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def render_settings(camera, width):
    sw,sh=camera['image_size_px'];height=round(width*sh/sw)
    if width<64 or height<64:
        raise ValueError('Review viewport is too small')
    sx,sy=width/sw,height/sh;K=np.asarray(camera['camera_intrinsics_cv_pixels'])
    fx,fy=K[0,0]*sx,K[1,1]*sy
    # Canonical source coordinates place pixel centers at integers. Blender
    # world_to_camera_view uses image-edge normalized coordinates. Add0.5
    # before scaling, then subtract0.5 when converting back to pixel centers.
    cx_edge,cy_edge=(K[0,2]+.5)*sx,(K[1,2]+.5)*sy
    ratio=fx/fy
    shift_x=(width/2-cx_edge)/width
    shift_y=(cy_edge-height/2)*ratio/width
    actual_fx=camera['lens_mm']*width/camera['sensor_width_mm']
    actual_fy=actual_fx/ratio
    Kactual=np.array([[actual_fx,0,width/2-shift_x*width-.5],
                     [0,actual_fy,height/2+shift_y*width/ratio-.5],[0,0,1.]])
    expected=np.array([[fx,0,cx_edge-.5],[0,fy,cy_edge-.5],[0,0,1.]])
    error=float(np.max(np.abs(Kactual-expected)))
    if error>1e-9:
        raise ValueError('Blender intrinsic settings do not reproduce resized source K')
    # Blender's aspect properties may clamp values below1. Keep their ratio
    # while normalizing both to at least1, as in camera-2026.json.
    return {'width':width,'height':height,'pixel_aspect_x':float(max(1.,1./ratio)),'pixel_aspect_y':float(max(1.,ratio)),
            'shift_x':float(shift_x),'shift_y':float(shift_y),'K_pixel_center':Kactual.tolist(),
            'source_to_render_scale_xy':[sx,sy],'maximum_K_error':error,
            'coordinate_note':'Render pixel center = source pixel center transformed as (p+0.5)*scale-0.5. No extra half-pixel camera shift.'}


def audit(raw_path=None, width=1800):
    locks=read(HERE/'photo-camera-lock.json')
    for key in ['camera','calibration','geometry','source_photo']:
        item=locks[key];path=HERE/item['file']
        if sha(path)!=item['sha256']:
            raise ValueError(f'Locked {key} changed: {path}')
    raw=raw_path.resolve() if raw_path else HERE/locks['raw']['file']
    if raw.stat().st_size!=locks['raw']['bytes'] or sha(raw)!=locks['raw']['sha256']:
        raise ValueError('Raw GLB differs from the locked candidate')
    blob=raw.read_bytes();jslen=struct.unpack_from('<I',blob,12)[0]
    if blob[:4]!=b'glTF' or len(blob)>=100_000_000:
        raise ValueError('Invalid/oversized raw GLB')
    gltf=json.loads(blob[20:20+jslen])
    camera=read(HERE/locks['camera']['file']);cal=read(HERE/locks['calibration']['file']);geo=read(HERE/locks['geometry']['file'])
    assert camera['calibration_sha256']==locks['calibration']['sha256']
    assert gltf['extras']['geometry_input_sha256']==locks['geometry']['sha256']
    assert geo['id']=='xuhui-wukang-129' and geo['replacement']['feature_local_ids']==[3733]
    assert cal['source_image']['sha256']==locks['source_photo']['sha256']
    assert cal['source_image']['orientation']==1 and camera['image_orientation']==1
    assert camera['image_size_px']==[1800,1200]
    assert camera['original_source_anchor']==geo['anchor']
    M=np.asarray(camera['camera_matrix_world_blender_enu'],float)
    assert M.shape==(4,4) and np.isfinite(M).all()
    assert np.max(np.abs(M[3]-[0,0,0,1]))<1e-12
    assert abs(np.linalg.det(M[:3,:3])-1)<1e-12
    assert np.max(np.abs(M[:3,:3].T@M[:3,:3]-np.eye(3)))<1e-12
    X=np.r_[-np.asarray(geo['front_edge']['tangent_east_north']),0.]
    outward=np.r_[geo['front_edge']['outward_normal_east_north'],0.]
    W=np.column_stack((X,[0.,0.,1.],outward))
    O=np.r_[geo['front_edge']['center_local_east_north_m'],0.]
    C=np.asarray(cal['camera_position_facade_u_z_d_m'])
    assert np.max(np.abs(O+W@C-M[:3,3]))<1e-10
    R=np.column_stack([cal['directions_camera'][k] for k in ['facade_u','world_up','facade_outward_d']])
    assert np.max(np.abs(W@R.T@np.diag([1,-1,-1])-M[:3,:3]))<1e-12
    K=np.asarray(camera['camera_intrinsics_cv_pixels']);P=np.asarray(cal['facade_u_z_d_to_oriented_pixel_projection_3x4'])
    points=[[-7.1,0,0],[-4.453,6.516,0],[6.14,7.03,-1.67],[5.5,4.58,-.04],[1.9,2.16,0],[-.5,2.7,0]]
    # Include independently picked real windows from distinct A/B/D planes.
    for window in cal['window_checks']:
        points.extend(window['u_z_d_m'])
    points=np.asarray(points);expected=np.c_[points,np.ones(len(points))]@P.T
    assert np.all(expected[:,2]>0)
    expected=expected[:,:2]/expected[:,2,None]
    enu=points@W.T+O
    bc=np.c_[enu,np.ones(len(enu))]@np.linalg.inv(M).T
    cv=bc[:,:3]*[1,-1,-1]
    actual=cv@K.T;actual=actual[:,:2]/actual[:,2,None]
    error=float(np.max(np.linalg.norm(expected-actual,axis=1)))
    assert error<1e-8
    settings=render_settings(camera,width)
    resized=cv@np.asarray(settings['K_pixel_center']).T;resized=resized[:,:2]/resized[:,2,None]
    transformed=(expected+.5)*settings['source_to_render_scale_xy']-.5
    scaled_error=float(np.max(np.linalg.norm(resized-transformed,axis=1)))
    assert scaled_error<1e-8
    # A wrong glTF-space matrix in a native ENU scene must be detectable.
    wrong=enu[:,[0,2,1]]*[1,1,-1]
    wc=np.c_[wrong,np.ones(len(wrong))]@np.linalg.inv(M).T
    wcv=wc[:,:3]*[1,-1,-1];wp=wcv@K.T;wp=wp[:,:2]/wp[:,2,None]
    negative=float(np.max(np.linalg.norm(wp-expected,axis=1)))
    assert negative>100
    report={'schema':'wukang129-photo-camera-entry-check-v1','passed':True,'bindings':locks,
        'point_count':len(points),'maximum_source_projection_error_px':error,
        'maximum_resized_projection_error_px':scaled_error,
        'wrong_gltf_basis_negative_control_error_px':negative,'render_settings':settings,
        'camera_matrix_world_blender_enu':M.tolist(),'photo_camera_script_sha256':sha(Path(__file__)),
        'no_blender_executed_by_check':True,
        'scope':'Numerical camera and exact source/raw binding only. It does not certify visible model accuracy, unknown facade depth, or surveyed dimensions.'}
    return camera,report,raw


def main():
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check',action='store_true');ap.add_argument('--report',type=Path)
    ap.add_argument('--raw',type=Path);ap.add_argument('--native-report',type=Path)
    ap.add_argument('--width',type=int,default=1800);ap.add_argument('--render',type=Path);ap.add_argument('--save-blend',type=Path)
    args=ap.parse_args(argv)
    camera,report,raw=audit(args.raw,args.width)
    if args.check:
        if args.report:
            args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(report,ensure_ascii=False,indent=2));return
    if not args.render and not args.save_blend:
        ap.error('Use --check, or inside Blender explicitly request --render/--save-blend')
    import bpy
    from mathutils import Matrix,Vector
    native=Path(bpy.data.filepath)
    if not bpy.data.filepath or not native.is_file():
        raise ValueError('Load the native .blend first; this script does not import or build geometry')
    native_report=args.native_report or native.with_name(native.stem+'-blender.json')
    binding=read(native_report)
    assert binding['source_glb_sha256']==report['bindings']['raw']['sha256']
    assert binding['native_file']==native.name and binding['native_sha256']==sha(native)
    collection=bpy.data.collections.get('Photo_reconstructed_architecture')
    if collection is None:
        raise ValueError('Expected unchanged native architecture collection was not found')
    meshes=[obj for obj in collection.all_objects if obj.type=='MESH']
    assert len(meshes)==binding['imported_meshes']
    scene=bpy.context.scene
    if scene.camera is None:
        bpy.ops.object.camera_add();scene.camera=bpy.context.object
    cam=scene.camera
    cam.matrix_world=Matrix(camera['camera_matrix_world_blender_enu'])
    cam.data.type='PERSP';cam.data.lens=camera['lens_mm'];cam.data.sensor_fit='HORIZONTAL'
    cam.data.sensor_width=camera['sensor_width_mm'];cam.data.sensor_height=camera['sensor_height_mm']
    cam.data.clip_start=.03;cam.data.clip_end=250
    s=report['render_settings'];scene.render.resolution_x=s['width'];scene.render.resolution_y=s['height'];scene.render.resolution_percentage=100
    scene.render.pixel_aspect_x=s['pixel_aspect_x'];scene.render.pixel_aspect_y=s['pixel_aspect_y']
    cam.data.shift_x=s['shift_x'];cam.data.shift_y=s['shift_y']
    cam['photo_camera_lock_sha256']=sha(HERE/'photo-camera-lock.json')
    cam['photo_reference']='Windmemories2026-02-09, CC-BY-SA4.0; conditional source scale and multi-plane inference'
    scene.camera=cam;bpy.context.view_layer.update()
    # Actual Blender projection check before saving/rendering. This retains roll.
    from bpy_extras.object_utils import world_to_camera_view
    geo=read(HERE/'geometry-input.json');O=np.r_[geo['front_edge']['center_local_east_north_m'],0.]
    W=np.column_stack((np.r_[-np.asarray(geo['front_edge']['tangent_east_north']),0.],[0,0,1],np.r_[geo['front_edge']['outward_normal_east_north'],0.]))
    cal=read(HERE/'calibration/calibration-independent.json');P=np.asarray(cal['facade_u_z_d_to_oriented_pixel_projection_3x4'])
    errors=[]
    for p in [[-4.453,6.516,0],[6.14,7.03,-1.67],[1.9,2.16,0],[.09,4.35,-5.555]]:
        loc=world_to_camera_view(scene,cam,Vector(O+W@p))
        actual=np.array([loc.x*s['width']-.5,(1-loc.y)*s['height']-.5])
        q=P@np.r_[p,1.];expected=(q[:2]/q[2]+.5)*s['source_to_render_scale_xy']-.5
        errors.append(float(np.linalg.norm(actual-expected)))
    if max(errors)>.02:
        raise ValueError(f'Actual Blender camera projection differs: {errors}')
    report.update({'native_binding_report':native_report.name,'native_input_sha256':binding['native_sha256'],
                   'actual_blender_projection_errors_px':errors,'applied_inside_blender':True,'geometry_changed':False,
                   'blender_version':bpy.app.version_string,'rendered':bool(args.render)})
    if args.save_blend:
        args.save_blend.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(args.save_blend.resolve()))
        assert args.save_blend.stat().st_size<100_000_000
        report['saved_native_sha256']=sha(args.save_blend)
    if args.render:
        args.render.parent.mkdir(parents=True,exist_ok=True);scene.render.image_settings.file_format='PNG';scene.render.filepath=str(args.render.resolve());bpy.ops.render.render(write_still=True)
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
