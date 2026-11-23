"""Restore auditorium photographic camera rolls and check native image coordinates after reopening."""
import importlib.util
import json
import os
from pathlib import Path
import sys

SOURCE=Path(__file__).absolute().parent
PROJECT=next(p for p in SOURCE.parents if (p/'tools/verify_editable_model.py').is_file())
spec=importlib.util.spec_from_file_location('shanghai_glass_native',PROJECT/'source/precise/xuhui-qixia-village-wuyuan-372/source/build_blender_source.py')
courts=importlib.util.module_from_spec(spec)
original_paths=sys.path.copy()
# The older garden adapter uses its own module of the same name for the list
# of source images. Keep that import local to loading its original adapter.
garden_module=sys.modules.pop('garden_finishes',None)
try:
    spec.loader.exec_module(courts)
finally:
    sys.path[:]=original_paths
    sys.modules.pop('garden_finishes',None)
    if garden_module is not None:
        sys.modules['garden_finishes']=garden_module
courts.SOURCE=SOURCE
io=courts.io
io.SOURCE=io.native.SOURCE=io.helpers.SOURCE=SOURCE
helpers=io.helpers
helpers.MODEL_ID=SOURCE.parent.name
helpers.UV='Auditorium exterior surface UV'
io.native.NODE='Auditorium architectural colour'
io.NORMAL_NAME='Auditorium surface normal'
io.TANGENT_NAME='Auditorium surface relief'
digest,used_textures,texture_bindings,attribution=io.digest,io.used_textures,io.texture_bindings,io.attribution

def calibrated_nodes(scene,create,raw):
    import bpy
    from mathutils import Matrix,Vector
    from bpy_extras.object_utils import world_to_camera_view
    views=helpers.raw_document(raw)['extras']['camera_views']
    if len(views)!=9 or len({view['name'] for view in views})!=9:
        raise ValueError('Expected nine distinct auditorium viewpoints')
    stage=bpy.data.collections['Preview lighting and camera']
    for i,view in enumerate(views):
        title=view['label']
        cam=scene.camera if create and i==0 else bpy.data.objects.get(title)
        eye=Vector(view['eye'])
        target=Vector(view['target'])
        direction=(target-eye).normalized()
        if create:
            if cam is None:
                cam=bpy.data.objects.new(title,bpy.data.cameras.new(title))
                stage.objects.link(cam)
            cam.name=cam.data.name=title
            cam.location=eye
            if 'world_up' in view:
                up=Vector(view['world_up']).normalized()
                right=direction.cross(up).normalized()
                cam.rotation_euler=Matrix([right,up,-direction]).transposed().to_euler()
            else:
                cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
            cam.data.type='PERSP'
            cam.data.sensor_fit='HORIZONTAL'
            cam.data.lens=cam.data.sensor_width*(target-eye).length/view['width_m']
            cam.data.clip_start=.005
            cam.data.clip_end=max(100.,2*(target-eye).length+view['width_m'])
            cam.data.shift_x=view.get('shift_x',0.)
            cam.data.shift_y=view.get('shift_y',0.)
            cam.data['width_px'],cam.data['height_px']=view['width'],view['height']
        bpy.context.view_layer.update()
        if (cam.location-eye).length>1e-4 or cam.data.sensor_fit!='HORIZONTAL':
            raise ValueError('Editable camera eye or sensor fit changed: '+title)
        if abs((target-eye).length*cam.data.sensor_width/cam.data.lens-view['width_m'])>.0001:
            raise ValueError('Editable camera field width changed: '+title)
        if (cam.matrix_world.to_quaternion()@Vector((0,0,-1))-direction).length>.00001:
            raise ValueError('Editable camera direction changed: '+title)
        if 'world_up' in view:
            if (cam.matrix_world.to_quaternion()@Vector((0,1,0))-Vector(view['world_up'])).length>.00001:
                raise ValueError('Editable camera roll changed: '+title)
        else:
            xy=world_to_camera_view(scene,cam,target)
            if max(abs(xy.x-.5),abs(xy.y-.5))>.001 or xy.z<=0:
                raise ValueError('Central graphic view misses its model target: '+title)
    return views

io.native.cameras=calibrated_nodes

def prepare(scene):
    courts.prepare(scene)


def verify(blend,raw,out):
    import bpy
    import numpy as np
    from mathutils import Vector
    from bpy_extras.object_utils import world_to_camera_view
    io.verify(blend,raw,out)
    data=json.loads(out.read_bytes())
    proof=data['architectural_source']
    proof['transparent_materials']=courts.glazing(raw)
    recorded=json.loads((SOURCE.parent/'measurements/court-cameras.json').read_bytes())['views']
    scene=bpy.context.scene
    render=scene.render
    old_size=render.resolution_x,render.resolution_y
    old_aspect=render.pixel_aspect_x,render.pixel_aspect_y
    for view in proof['cameras']:
        if 'world_up' not in view:
            continue
        source_key=view['reference'].split()[-1]
        entry=recorded[source_key]
        cam=bpy.data.objects[view['label']]
        if cam.data.sensor_fit!='HORIZONTAL':
            raise ValueError('Registered photographic camera lost horizontal sensor fit')
        actual_up=list(cam.matrix_world.to_quaternion()@Vector((0,1,0)))
        k=np.asarray(entry['K']);r=np.asarray(entry['R']);c=np.asarray(entry['C'])
        render.resolution_x,render.resolution_y=entry['size']
        # Blender pixel aspect values are constrained to >= 1.
        aspect=float(view.get('pixel_aspect_y',1))
        render.pixel_aspect_x,render.pixel_aspect_y=max(1.,1./aspect),max(1.,aspect)
        check=[]
        for dx in (-1.2,0,1.2):
            for dz in (-.7,0,.7):
                point=np.asarray(view['target'])+[dx,0,dz]
                uv=k@r@(point-c);expected=uv[:2]/uv[2]
                camera_view=world_to_camera_view(scene,cam,Vector(point))
                observed=[camera_view.x*render.resolution_x,(1-camera_view.y)*render.resolution_y]
                check.append(float(np.linalg.norm(expected-observed)))
        if max(check)>.001:
            raise ValueError('Reopened auditorium camera does not project to the registered photograph')
        proof.setdefault('photographic_up_axes',{})[view['name']]=dict(reference=view['reference'],
            sensor_fit=cam.data.sensor_fit,expected=view['world_up'],reopened=actual_up,image_dimensions=entry['size'],
            reprojected_samples=len(check),max_projection_error_px=max(check))
    render.resolution_x,render.resolution_y=old_size
    render.pixel_aspect_x,render.pixel_aspect_y=old_aspect
    out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    stage=os.environ['ARCHITECTURAL_NATIVE_STAGE']
    if stage=='make':
        import bpy
        bpy.app.handlers.save_pre.append(bpy.app.handlers.persistent(prepare))
    elif stage=='reopen':
        verify(*map(Path,sys.argv[sys.argv.index('--')+1:]))
    else:
        raise ValueError(stage)
