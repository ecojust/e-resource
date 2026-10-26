#!/usr/bin/env python3
"""Apply the frozen 2025 camera to an ENU Blender scene; no Blender is run here.

Normal Python: python photo_camera.py --check --report output/camera-check.json
Root renderer: blender -b bund07.blend --python photo_camera.py -- \
  --render photo-camera.png --width 1500 --save-blend photo-camera.blend

A normal invocation never launches Blender or rendering. Applying only changes
camera/render settings in the already loaded scene. The camera is not re-aimed
at the building center, and no geometry or source image is modified.
"""
from pathlib import Path
import argparse,hashlib,json,sys
import numpy as np
HERE=Path(__file__).resolve().parent

def audit():
    data=json.loads((HERE/'photo-camera-parameters.json').read_text());cal=json.loads((HERE/'calibration-independent.json').read_text())
    assert hashlib.sha256((HERE/'calibration-independent.json').read_bytes()).hexdigest()==data['calibration_sha256']
    assert hashlib.sha256((HERE/'geometry-input.json').read_bytes()).hexdigest()==data['geometry_sha256']
    M=np.array(data['camera_matrix_world_blender_enu_row_major']);W=np.array(data['facade_to_enu_basis_columns_u_z_outward_d']);O=np.array(data['facade_origin_enu']);K=np.array(data['intrinsics']);P=np.array(cal['facade_u_z_d_to_oriented_pixel_projection_3x4'])
    pts=np.array([[-14,0,0],[-7,19,0],[0,22.5,-3],[6,22.25,-3],[10.5,24,-2.39],[14,19,0],[0,4.8,.62]])
    expected=np.c_[pts,np.ones(len(pts))]@P.T;expected=expected[:,:2]/expected[:,2,None]
    enu=pts@W.T+O;bc=np.c_[enu,np.ones(len(pts))]@np.linalg.inv(M).T;cv=bc[:,:3]*[1,-1,-1];actual=cv@K.T;actual=actual[:,:2]/actual[:,2,None]
    err=float(np.max(np.linalg.norm(expected-actual,axis=1)));assert err<1e-8
    return data,{'schema':'bund07-photo-camera-entry-check-v1','passed':True,'maximum_projection_error_px':err,'point_count':len(pts),'camera_matrix_world_blender_enu':M.tolist(),'calibration_sha256':data['calibration_sha256'],'no_blender_executed':True,'scope':'Numerical camera transform only. Rendered photographic shape still requires root review.'}

def main():
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--report',type=Path);p.add_argument('--width',type=int,default=1500);p.add_argument('--render',type=Path);p.add_argument('--save-blend',type=Path);a=p.parse_args(args)
    data,report=audit()
    if a.report:a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n')
    if a.check:print(json.dumps(report,indent=2));return
    if not a.render and not a.save_blend:p.error('Use --check, or inside Blender explicitly select --render/--save-blend')
    import bpy
    from mathutils import Matrix
    scene=bpy.context.scene
    if scene.camera is None:
        bpy.ops.object.camera_add();scene.camera=bpy.context.object
    cam=scene.camera;cam.matrix_world=Matrix(data['camera_matrix_world_blender_enu_row_major']);cam.data.type='PERSP';cam.data.lens=data['focal_mm'];cam.data.sensor_fit='HORIZONTAL';cam.data.sensor_width=data['sensor_evidence_mm'][0];cam.data.clip_start=.05;cam.data.clip_end=500
    w,h=data['source_pixels'];K=data['intrinsics'];ratio=K[0][0]/K[1][1]
    scene.render.resolution_x=a.width;scene.render.resolution_y=round(a.width*h/w);scene.render.resolution_percentage=100;scene.render.pixel_aspect_x=1;scene.render.pixel_aspect_y=ratio
    cam.data.shift_x=(w/2-K[0][2])/w;cam.data.shift_y=(K[1][2]-h/2)*ratio/w
    cam['photo_calibration_sha256']=data['calibration_sha256'];cam['photo_view']='Suicasmo 2025-05-01 original EXIF1, same lens/pose estimated from facade lines; distortion uncalibrated'
    if a.save_blend:a.save_blend.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(a.save_blend.resolve()))
    if a.render:a.render.parent.mkdir(parents=True,exist_ok=True);scene.render.filepath=str(a.render.resolve());bpy.ops.render.render(write_still=True)
if __name__=='__main__':main()
