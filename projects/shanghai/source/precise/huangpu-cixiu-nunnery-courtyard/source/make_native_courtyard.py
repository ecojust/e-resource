"""Supply an accurate transparent courtyard cover and south-to-north viewing angle in Blender."""
from pathlib import Path
import json,os,runpy
import bpy
from bpy.app.handlers import persistent
from mathutils import Vector

GLASS='later translucent courtyard glazing'

@persistent
def prepare_courtyard(*_):
    scene=bpy.context.scene
    material=bpy.data.materials.get(GLASS)
    if material is None:return
    shader=material.node_tree.nodes['Principled BSDF']
    shader.inputs['Alpha'].default_value=.20
    rgb=material.diffuse_color[:3];material.diffuse_color=(*rgb,.20)
    cam=scene.camera
    target=Vector((-.10,-2.02,3.32))
    cam.name='View of north hall and both galleries'
    cam.location=target+Vector((1.45,-21.5,12.30))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=20.4
    scene.render.resolution_x=880;scene.render.resolution_y=730
    scene.cycles.transparent_max_bounces=12

@persistent
def assert_reopened(*_):
    material=bpy.data.materials.get(GLASS)
    if material is None:return
    shader=material.node_tree.nodes['Principled BSDF'];alpha=shader.inputs['Alpha'].default_value
    assert abs(alpha-.20)<1e-5 and abs(material.diffuse_color[3]-.20)<1e-5
    objects=[o.name for o in bpy.context.scene.objects if o.type=='MESH']
    assert all(any(o.startswith(name)for o in objects)for name in ('North hall','East gallery','West gallery','Court/','Later canopy/'))
    report=dict(blender=bpy.app.version_string,reopened_principled_alpha=alpha,reopened_material_rgba=list(material.diffuse_color),
                editable_glazing_objects=[o for o in objects if o.startswith('Later canopy/glazing')],
                camera=bpy.context.scene.camera.name,visible_groups_checked=['North hall','East gallery','West gallery','Court/','Later canopy/'])
    assert report['editable_glazing_objects']
    Path(os.environ['CIXIU_GLAZING_AUDIT']).write_text(json.dumps(report,indent=2)+'\n')

bpy.app.handlers.save_pre.append(prepare_courtyard)
bpy.app.handlers.load_post.append(assert_reopened)
runpy.run_path(os.environ['CIXIU_BASE_NATIVE'],run_name='__main__')
