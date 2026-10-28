"""Additional fixed-eye perspective view; does not rewrite the native file."""
from pathlib import Path
import hashlib,json
import bpy
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parent.parent
D=json.loads((ROOT/'source/design-input.json').read_text());f=D['frame'];x=f['architecture_X_EN'];y=f['architecture_Y_EN']
R=Matrix(((x[0],y[0],0),(x[1],y[1],0),(0,0,1)))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'review/native/jinshanwei-gatehouse.blend'))
scene=bpy.context.scene
location=(0.,-80.,3.5);aim=(0.,-16.,9.)
bpy.ops.object.camera_add(location=R@Vector(location));cam=bpy.context.object;cam.name='Ground front comparison only'
cam.rotation_euler=(R@Vector(aim)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='PERSP';cam.data.lens=50;cam.data.sensor_width=36;cam.data.clip_end=400
scene.camera=cam;scene.render.resolution_x=1000;scene.render.resolution_y=706;scene.render.resolution_percentage=100
path=ROOT/'review/previews/ground-front-perspective.png';scene.render.filepath=str(path)
bpy.ops.render.render(write_still=True)
report={'schema':'jinshanwei-ground-front-comparison-v1','file':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'camera_architecture_xyz':location,'aim_architecture_xyz':aim,'camera_ENU':list(cam.location),'perspective':True,'lens_mm':50,'sensor_width_mm':36,'dimensions_px':[1000,706],
        'photo_calibrated':False,'purpose':'Low eye-height comparison to front.jpg; not an exact photogrammetric camera solve.','native_rewritten':False,'geometry_modified':False,'author':'agent'}
(ROOT/'review/ground-front-perspective.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('GROUND_FRONT_READY',path,flush=True)
