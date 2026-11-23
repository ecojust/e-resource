"""Restore Huxi Villas east row gable photographic camera rolls and check native image coordinates after reopening."""
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
helpers.UV='Huxi Villas east row gable exterior surface UV'
io.native.NODE='Huxi Villas east row gable architectural colour'
io.NORMAL_NAME='Huxi Villas east row gable surface normal'
io.TANGENT_NAME='Huxi Villas east row gable surface relief'
digest,used_textures,texture_bindings,attribution=io.digest,io.used_textures,io.texture_bindings,io.attribution

def attribution(raw):
    meta=helpers.raw_document(raw)['extras']
    if (meta.get('id')!=helpers.MODEL_ID or meta.get('model_id', meta.get('id'))!=helpers.MODEL_ID or meta.get('geometry_license')!='MIT'
            or meta.get('texture_license')!='MIT' or meta.get('photos_embedded') is not False):
        raise ValueError('Expected attributed Huxi Villas east row gable model with procedural textures')
    return {k:v for k,v in meta.items() if k != 'model_id' and isinstance(v,(str,bool,int,float))}

io.attribution=io.native.attribution=attribution

def calibrated_nodes(scene,create,raw):
    import bpy
    from mathutils import Matrix,Vector
    from bpy_extras.object_utils import world_to_camera_view
    views=helpers.raw_document(raw)['extras']['camera_views']
    if len(views)!=9 or len({view['name'] for view in views})!=9:
        raise ValueError('Expected nine distinct Huxi Villas east row gable viewpoints')
    stage=bpy.data.collections['Preview lighting and camera']
    # The registered target sets the viewing direction and can be much closer
    # than the building. Use mesh bounds to place the clipping planes.
    stage_mesh_objects = [obj for obj in scene.objects if obj.type == 'MESH']
    model_corners = [obj.matrix_world @ Vector(corner) for obj in stage_mesh_objects for corner in obj.bound_box]
    if not model_corners:
        raise ValueError('The editable scene contains no model geometry')
    for i,view in enumerate(views):
        title=view['label']
        cam=scene.camera if create and i==0 else bpy.data.objects.get(title)
        eye=Vector(view['eye'])
        target=Vector(view['target'])
        direction=(target-eye).normalized()
        farthest_depth = max((corner - eye).dot(direction) for corner in model_corners)
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
            cam.data.clip_end=max(100., 1.05 * farthest_depth + 1.)
            cam.data.shift_x=view.get('shift_x',0.)
            cam.data.shift_y=view.get('shift_y',0.)
            cam.data['width_px'],cam.data['height_px']=view['width'],view['height']
        bpy.context.view_layer.update()
        if cam.data.clip_end <= farthest_depth:
            raise ValueError(('Model lies beyond the camera far plane',title,farthest_depth,cam.data.clip_end))
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

def prepare(_filepath):
    import bpy
    scene=bpy.context.scene
    courts.prepare(scene)
    # Retain the source camera dimensions on the objects, and use a separate
    # studio-sized verification render when the scene is first made.
    scene.render.resolution_x,scene.render.resolution_y=480,308
    scene.render.resolution_percentage=100
    scene.cycles.use_auto_tile=True
    scene.cycles.tile_size=64
    scene.cycles.samples=6
    scene.render.threads_mode='FIXED'
    scene.render.threads=1


def verify(blend,raw,out):
    import bpy
    import numpy as np
    from mathutils import Vector
    from bpy_extras.object_utils import world_to_camera_view
    io.verify(blend,raw,out)
    data=json.loads(out.read_bytes())
    proof=data['architectural_source']
    proof['transparent_materials']=courts.glazing(raw)
    authored = {m['name'] for m in helpers.raw_document(raw)['materials'] if m.get('alphaMode')=='BLEND'}
    if set(proof['transparent_materials'])!=authored:
        raise ValueError(('Reopened glazing differs from the authored edition', authored, proof['transparent_materials']))
    scene=bpy.context.scene
    render=scene.render
    old_size=render.resolution_x,render.resolution_y
    old_aspect=render.pixel_aspect_x,render.pixel_aspect_y
    stations = json.loads((SOURCE.parent / 'measurements/gable-photo-stations.json').read_bytes())['stations']
    for view in proof['cameras']:
        if 'world_up' not in view:
            continue
        cam=bpy.data.objects[view['label']]
        if cam.data.sensor_fit!='HORIZONTAL':
            raise ValueError('Registered photographic camera lost horizontal sensor fit')
        actual_up=list(cam.matrix_world.to_quaternion()@Vector((0,1,0)))
        p=np.asarray(view['projection_world_to_photo_pixel_centres'])
        render.resolution_x,render.resolution_y=view['width'],view['height']
        # Blender pixel aspect values are constrained to >= 1.
        render.pixel_aspect_x=float(view.get('blender_pixel_aspect_x',1.))
        render.pixel_aspect_y=float(view.get('blender_pixel_aspect_y',1.))
        station = stations[view['reference']]
        original_K = np.asarray(station['K'])
        original_R = np.asarray(station['R'])
        camera_centre = np.asarray(station['C'])
        crop_origin = np.asarray(view['source_crop'][:2])
        check=[]
        for dx in (-1.2,0,1.2):
            for dz in (-.7,0,.7):
                point=np.asarray(view['target'])+[dx,0,dz]
                uv=p@np.r_[point,1.]
                expected = uv[:2] / uv[2] + .5
                uncropped = original_K @ original_R @ (point - camera_centre)
                reference = uncropped[:2] / uncropped[2] + .5 - crop_origin
                if np.linalg.norm(reference - expected) > 1.e-7:
                    raise ValueError(('Source image crop differs from photograph calibration', view['name']))
                camera_view=world_to_camera_view(scene,cam,Vector(point))
                observed=[camera_view.x*render.resolution_x,(1-camera_view.y)*render.resolution_y]
                check.append(float(np.linalg.norm(expected-observed)))
        # Recover vertical focal length and skew from the actual registered
        # camera matrix, using the photographed upward axis in world space.
        down=-np.asarray(view['world_up'])
        fy=abs(float(np.dot(p[1,:3],down)))/np.linalg.norm(p[2,:3])
        skew=float(np.dot(p[0,:3],down))/np.linalg.norm(p[2,:3])
        skew_budget=abs(skew)*max(view['principal_point_edge_px'][1],
            view['height']-view['principal_point_edge_px'][1])/fy+.003
        if max(check)>skew_budget:
            raise ValueError('Reopened Huxi Villas east row gable camera does not project to the registered photograph')
        proof.setdefault('photographic_up_axes',{})[view['name']]=dict(reference=view['reference'],
            sensor_fit=cam.data.sensor_fit,expected=view['world_up'],reopened=actual_up,image_dimensions=[view['width'],view['height']],pixel_aspect=[render.pixel_aspect_x,render.pixel_aspect_y],
            far_plane_m=cam.data.clip_end,reprojected_samples=len(check),max_projection_error_px=max(check),maximum_whole_field_skew_px=skew_budget-.003)
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
