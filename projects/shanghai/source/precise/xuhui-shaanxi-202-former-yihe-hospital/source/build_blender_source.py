"""Restore the courtyard and entrance camera rolls and verify their source pixels after reopening the blend."""
import importlib.util
import json
import os
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
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
helpers.UV='Yihe courtyard architectural surface UV'
io.native.NODE='Yihe architectural colour'
io.NORMAL_NAME='Yihe surface normal'
io.TANGENT_NAME='Yihe surface relief'
digest,used_textures,texture_bindings,attribution=io.digest,io.used_textures,io.texture_bindings,io.attribution

def pendant_light(raw,install):
    import bpy
    mat_name='Yihe | illuminated vestibule globe'
    document=helpers.raw_document(raw)
    gltf=next(m for m in document['materials'] if m['name']==mat_name)
    expected=gltf['emissiveFactor']
    mat=bpy.data.materials[mat_name]
    shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    color=shader.inputs.get('Emission Color') or shader.inputs['Emission']
    strength=shader.inputs['Emission Strength']
    if install:
        color.default_value=(*expected,1.)
        strength.default_value=1.
    actual=list(color.default_value)[:3]
    if max(abs(a-b) for a,b in zip(expected,actual))>1.e-6 or abs(strength.default_value-1.)>1.e-6:
        raise ValueError('The two vestibule lamp globes have lost their source emission')
    return dict(material=mat_name,source=expected,reopened=actual,strength=float(strength.default_value))

def prepare(scene):
    courts.prepare(scene)
    pendant_light(Path(os.environ['ARCHITECTURAL_NATIVE_RAW']),True)

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
    recorded['06']=json.loads((SOURCE.parent/'measurements/entrance-cameras.json').read_bytes())['close_view']
    proof['pendant_globes']=pendant_light(raw,False)
    scene=bpy.context.scene
    render=scene.render
    old_size=render.resolution_x,render.resolution_y
    for view in proof['cameras']:
        if 'world_up' not in view:
            continue
        source_key=view['reference'].split()[-1]
        entry=recorded[source_key]
        cam=bpy.data.objects[view['label']]
        actual_up=list(cam.matrix_world.to_quaternion()@Vector((0,1,0)))
        k=np.asarray(entry['K']);r=np.asarray(entry['R']);c=np.asarray(entry['C'])
        render.resolution_x,render.resolution_y=entry['size']
        check=[]
        for dx in (-1.2,0,1.2):
            for dz in (-.7,0,.7):
                point=np.asarray(view['target'])+[dx,0,dz]
                uv=k@r@(point-c);expected=uv[:2]/uv[2]
                camera_view=world_to_camera_view(scene,cam,Vector(point))
                observed=[camera_view.x*render.resolution_x,(1-camera_view.y)*render.resolution_y]
                check.append(float(np.linalg.norm(expected-observed)))
        if max(check)>.001:
            raise ValueError('Reopened courtyard camera does not project to the registered photograph')
        proof.setdefault('photographic_up_axes',{})[view['name']]=dict(reference=view['reference'],
            expected=view['world_up'],reopened=actual_up,image_dimensions=entry['size'],
            reprojected_samples=len(check),max_projection_error_px=max(check))
    render.resolution_x,render.resolution_y=old_size
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
