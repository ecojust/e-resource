"""Restore Xinhua Road, No. 200 garden residence photographic camera rolls and check native image coordinates after reopening."""
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
helpers.UV='Xinhua Road, No. 200 garden residence exterior surface UV'
io.native.NODE='Xinhua Road, No. 200 garden residence architectural colour'
io.NORMAL_NAME='Xinhua Road, No. 200 garden residence surface normal'
io.TANGENT_NAME='Xinhua Road, No. 200 garden residence surface relief'
digest,used_textures,texture_bindings,attribution=io.digest,io.used_textures,io.texture_bindings,io.attribution

def attribution(raw):
    meta=helpers.raw_document(raw)['extras']
    if (meta.get('id')!=helpers.MODEL_ID or meta.get('geometry_license')!='MIT'
            or meta.get('photos_embedded') is not False):
        raise ValueError('Expected attributed Xinhua Road, No. 200 garden residence model with procedural textures')
    return {k:v for k,v in meta.items() if isinstance(v,(str,bool,int,float))}

io.attribution=io.native.attribution=attribution

def calibrated_nodes(scene,create,raw):
    import bpy
    from mathutils import Matrix,Vector
    from bpy_extras.object_utils import world_to_camera_view
    views=helpers.raw_document(raw)['extras']['camera_views']
    if len(views)!=10 or len({view['name'] for view in views})!=10:
        raise ValueError('Expected ten distinct Xinhua Road, No. 200 garden residence viewpoints')
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
        if (cam.data.get('width_px'), cam.data.get('height_px')) != (view['width'], view['height']):
            raise ValueError('Reopened camera dimensions changed: ' + title)
        if max(abs(cam.data.shift_x - view.get('shift_x', 0.0)),
               abs(cam.data.shift_y - view.get('shift_y', 0.0))) > 1e-6:
            raise ValueError('Reopened camera principal point changed: ' + title)
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
    scene.render.resolution_x,scene.render.resolution_y=600,376
    scene.render.resolution_percentage=100
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
    expected_glass = set(json.loads((SOURCE/'material-contract.json').read_bytes())['transparent_materials'])
    if set(proof['transparent_materials']) != expected_glass:
        raise ValueError(('Unexpected transparent materials',proof['transparent_materials']))
    scene=bpy.context.scene
    render=scene.render
    old_size=render.resolution_x,render.resolution_y
    old_aspect=render.pixel_aspect_x,render.pixel_aspect_y
    stations=json.loads((SOURCE.parent/'measurements/two-stations.json').read_bytes())
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
        crop_origin=np.asarray(view['source_crop'][:2])
        lookup = next((key for key in (view.get('reference'), view['name']) if key in stations), None)
        if lookup is None:
            raise ValueError(('Camera missing from photographic fits', view['name']))
        station = stations[lookup]
        source_projection = np.asarray(station['P'])
        check=[]
        for dx in (-1.2,0,1.2):
            for dz in (-.7,0,.7):
                point=np.asarray(view['target'])+[dx,0,dz]
                source_pixel = source_projection @ np.r_[point, 1.]
                original = source_pixel[:2] / source_pixel[2] + .5
                expected = original - crop_origin
                model_pixel = p @ np.r_[point, 1.]
                projected = model_pixel[:2] / model_pixel[2] + .5
                if min(np.linalg.norm(projected - original), np.linalg.norm(projected - expected)) > 1e-6:
                    raise ValueError(('Model camera differs from the original photograph', view['name']))
                if not cam.data.clip_start < (point - np.asarray(cam.location)) @ np.asarray((cam.matrix_world.to_quaternion() @ Vector((0,0,-1)))) < cam.data.clip_end:
                    raise ValueError(('Camera clips its projected model samples', view['name']))
                camera_view=world_to_camera_view(scene,cam,Vector(point))
                observed=[camera_view.x*render.resolution_x,(1-camera_view.y)*render.resolution_y]
                check.append(float(np.linalg.norm(expected-observed)))
        # Recover vertical focal length and skew from the actual registered
        # camera matrix, using the photographed upward axis in world space.
        down=-np.asarray(view['world_up'])
        fy=abs(float(np.dot(p[1,:3],down)))/np.linalg.norm(p[2,:3])
        skew=float(np.dot(p[0,:3],down))/np.linalg.norm(p[2,:3])
        skew_budget=abs(skew)*max(view.get('principal_point_edge_px',[view['width']/2,view['height']/2])[1],
            view['height']-view.get('principal_point_edge_px',[view['width']/2,view['height']/2])[1])/fy+.003
        if max(check)>skew_budget:
            raise ValueError((view['name'], max(check), skew_budget, 'projection error on the cropped frame'))
        proof.setdefault('photographic_up_axes',{})[view['name']]=dict(reference=view['reference'],
            fit_type=station.get('conditional',station.get('scope','Photographic fit')),far_plane_m=cam.data.clip_end,sensor_fit=cam.data.sensor_fit,expected=view['world_up'],reopened=actual_up,image_dimensions=[view['width'],view['height']],pixel_aspect=[render.pixel_aspect_x,render.pixel_aspect_y],
            reprojected_samples=len(check),max_projection_error_px=max(check),maximum_whole_field_skew_px=skew_budget-.003)
    if len(proof.get('photographic_up_axes', {})) < 2:
        raise ValueError('Expected entries for both the independently registered garden photographs')
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
