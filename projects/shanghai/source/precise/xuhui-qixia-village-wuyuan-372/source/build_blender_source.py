"""Install No. 6/7/9 glazing, tilted photo cameras and packed surface relief in the editable scene."""
import importlib.util
import json
import os
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
PROJECT=next(p for p in SOURCE.parents if (p/'tools/verify_editable_model.py').is_file())
script=PROJECT/'source/precise/xuhui-shaanxi-222-no20-residence-gate/source/build_blender_source.py'
spec=importlib.util.spec_from_file_location('shanghai_textured_native_io',script)
io=importlib.util.module_from_spec(spec)
paths=sys.path.copy()
try:
    spec.loader.exec_module(io)
finally:
    sys.path[:]=paths
io.SOURCE=io.native.SOURCE=io.helpers.SOURCE=SOURCE
io.helpers.MODEL_ID=SOURCE.parent.name
io.helpers.UV='Qixia architectural surface UV'
io.native.NODE='Qixia original surface colour'
io.NORMAL_NAME='Qixia surface normal'
io.TANGENT_NAME='Qixia surface relief'
helpers,digest=io.helpers,io.digest
texture_bindings,used_textures,attribution=io.texture_bindings,io.used_textures,io.attribution
base_cameras=io.native.cameras


def rolled_cameras(scene, create, raw):
    import bpy
    from mathutils import Matrix, Vector
    views=base_cameras(scene,create,raw)
    for view in views:
        cam=bpy.data.objects[view['label']]
        if create:
            cam.data['width_px']=int(view['width']);cam.data['height_px']=int(view['height'])
            if 'photo_id' in view:cam.data['source_photo_id']=view['photo_id']
        if (cam.data.get('width_px'),cam.data.get('height_px'))!=(view['width'],view['height']):
            raise ValueError(f'Native camera dimensions changed: {view["name"]}')
        if 'world_up' not in view:
            continue
        forward=(Vector(view['target'])-Vector(view['eye'])).normalized()
        up=Vector(view['world_up']).normalized()
        if abs(forward.dot(up))>1.e-6:
            raise ValueError(f'Photo up axis is not orthogonal to the optical axis: {view["name"]}')
        if create:
            right=forward.cross(up).normalized()
            basis=Matrix([right,up,-forward]).transposed()
            cam.rotation_euler=basis.to_euler()
        q=cam.rotation_euler.to_quaternion()
        if (q@Vector((0,1,0))-up).length>1.e-5 or (q@Vector((0,0,-1))-forward).length>1.e-5:
            raise ValueError(f'Photograph roll or optical direction changed: {view["name"]}')
    return views


io.native.cameras=rolled_cameras


def glazing(raw,install=False):
    import bpy
    doc=helpers.raw_document(raw)
    report={}
    for original in doc['materials']:
        if original.get('alphaMode','OPAQUE')!='BLEND':
            continue
        name=original['name'];mat=bpy.data.materials[name]
        alpha=original['pbrMetallicRoughness']['baseColorFactor'][3]
        shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        if install:
            shader.inputs['Alpha'].default_value=alpha
            rgba=list(shader.inputs['Base Color'].default_value)
            rgba[3]=alpha;shader.inputs['Base Color'].default_value=rgba
            mat.diffuse_color=rgba
            if hasattr(mat,'surface_render_method'):
                mat.surface_render_method='DITHERED'
            else:
                mat.blend_method='BLEND'
        actual=float(shader.inputs['Alpha'].default_value)
        if abs(actual-alpha)>1.e-6 or shader.inputs['Alpha'].is_linked:
            raise ValueError(f'Native alpha does not match architectural glazing: {name}')
        report[name]={'raw_alpha_mode':'BLEND','expected_alpha':alpha,'principled_alpha':actual,
                      'surface_method':str(mat.surface_render_method if hasattr(mat,'surface_render_method') else mat.blend_method)}
    return report


def prepare(scene):
    io.prepare(scene)
    glazing(Path(os.environ['ARCHITECTURAL_NATIVE_RAW']),True)


def verify(blend,raw,out):
    import bpy
    import numpy as np
    from mathutils import Vector
    from bpy_extras.object_utils import world_to_camera_view
    io.verify(blend,raw,out)
    data=json.loads(out.read_bytes());proof=data['architectural_source']
    proof['transparent_materials']=glazing(raw)
    registered=json.loads((SOURCE.parent/'measurements/court-cameras.json').read_bytes())['views']
    scene=bpy.context.scene;r=scene.render
    normal_size=(r.resolution_x,r.resolution_y)
    for view in proof['cameras']:
        if 'world_up' not in view:
            continue
        cam=bpy.data.objects[view['label']]
        up=list(cam.matrix_world.to_quaternion()@Vector((0,1,0)))
        source_camera=registered[str(int(view['photo_id'])%100)]
        K=np.asarray(source_camera['intrinsic']);R=np.asarray(source_camera['rotation']);C=np.asarray(source_camera['centre'])
        r.resolution_x,r.resolution_y=cam.data['width_px'],cam.data['height_px']
        check=[]
        for x in (-1.2,0.,1.2):
            for z in (-.7,0.,.7):
                point=np.asarray(view['target'])+[x,0,z]
                uv=K@R@(point-C);expected=uv[:2]/uv[2]
                xy=world_to_camera_view(scene,cam,Vector(point))
                observed=np.array([xy.x*r.resolution_x,(1-xy.y)*r.resolution_y])
                check.append(float(np.linalg.norm(expected-observed)))
        if max(check)>.001:
            raise ValueError(f'Reopened photo camera reprojects onto the wrong pixels: {view["name"]}')
        proof.setdefault('photographic_up_axes',{})[view['name']]={'expected':view['world_up'],'reopened':up,
            'photo_id':view['photo_id'],'image_dimensions':[r.resolution_x,r.resolution_y],
            'reprojected_samples':len(check),'max_projection_error_px':max(check)}
    r.resolution_x,r.resolution_y=normal_size
    out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    phase=os.environ['ARCHITECTURAL_NATIVE_STAGE']
    if phase=='make':
        import bpy
        bpy.app.handlers.save_pre.append(bpy.app.handlers.persistent(prepare))
    elif phase=='reopen':
        verify(*map(Path,sys.argv[sys.argv.index('--')+1:]))
    else:
        raise ValueError(phase)
