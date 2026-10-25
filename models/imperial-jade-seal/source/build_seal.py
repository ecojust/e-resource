"""Reconstruct the cover-photo silhouette of the user-specified Sohu article.

Reference: https://www.sohu.com/a/1091255651_122157668
The photograph, not its unrelated accompanying illustrations, controls the form.
Hidden surfaces and underside inscription are explicitly interpretive additions.
"""
import bpy
import math
import os
import sys
from pathlib import Path
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
OUT = Path(os.environ.get('SEAL_OUTPUT_DIR', str(HERE / 'output' / 'imperial_jade_seal')))
OUT.mkdir(parents=True, exist_ok=True)
MODE = os.environ.get('SEAL_RENDER', 'final')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials):
    bpy.data.materials.remove(m)


def material(name, color, roughness=.27, metallic=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Metallic'].default_value = metallic
    return m


jade = material('青白玉 · ivory and celadon nephrite', (.52, .61, .48), .235)
n = jade.node_tree.nodes
l = jade.node_tree.links
p = n.get('Principled BSDF')
p.inputs['Subsurface Weight'].default_value = .10
p.inputs['Subsurface Radius'].default_value = (.48, .70, .32)
p.inputs['Coat Weight'].default_value = .30
p.inputs['Coat Roughness'].default_value = .19
p.inputs['Transmission Weight'].default_value = .04
p.inputs['IOR'].default_value = 1.48
geo = n.new('ShaderNodeNewGeometry')
cloud = n.new('ShaderNodeTexNoise')
cloud.inputs['Scale'].default_value = 1.10
cloud.inputs['Detail'].default_value = 4
cloud.inputs['Roughness'].default_value = .68
l.new(geo.outputs['Position'], cloud.inputs['Vector'])
ramp = n.new('ShaderNodeValToRGB')
ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
for i, (pos, color) in enumerate([
        (.20, (.19, .31, .25, 1)),
        (.40, (.40, .53, .43, 1)),
        (.62, (.68, .73, .59, 1)),
        (.82, (.86, .85, .70, 1))]):
    e = ramp.color_ramp.elements[0] if i == 0 else ramp.color_ramp.elements.new(pos)
    e.position, e.color = pos, color
l.new(cloud.outputs['Fac'], ramp.inputs['Fac'])
# Faint warm weathering at the base foot; the knob remains clean pale jade.
xyz = n.new('ShaderNodeSeparateXYZ')
l.new(geo.outputs['Position'], xyz.inputs[0])
height = n.new('ShaderNodeMapRange')
height.inputs['From Min'].default_value = 0
height.inputs['From Max'].default_value = .22
height.inputs['To Min'].default_value = .48
height.inputs['To Max'].default_value = 1
height.clamp = True
l.new(xyz.outputs['Z'], height.inputs['Value'])
mix = n.new('ShaderNodeMixRGB')
mix.inputs[1].default_value = (.31, .22, .11, 1)
l.new(height.outputs['Result'], mix.inputs[0])
l.new(ramp.outputs['Color'], mix.inputs[2])
l.new(mix.outputs['Color'], p.inputs['Base Color'])
fine = n.new('ShaderNodeTexNoise')
fine.inputs['Scale'].default_value = 48
fine.inputs['Detail'].default_value = 2
l.new(geo.outputs['Position'], fine.inputs['Vector'])
bump = n.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = .055
bump.inputs['Distance'].default_value = .012
l.new(fine.outputs['Fac'], bump.inputs['Height'])
l.new(bump.outputs['Normal'], p.inputs['Normal'])
recess = material('玉雕暗部 · shadowed jade', (.17, .24, .13), .30)
gold = material('上角补金 · hammered repair gold', (.73, .42, .09), .30, .92)
gn = gold.node_tree.nodes
gl = gold.node_tree.links
gp = gn.get('Principled BSDF')
gtex = gn.new('ShaderNodeTexNoise')
gtex.inputs['Scale'].default_value = 18
gtex.inputs['Detail'].default_value = 2
geometry = gn.new('ShaderNodeNewGeometry')
gl.new(geometry.outputs['Position'], gtex.inputs['Vector'])
gb = gn.new('ShaderNodeBump')
gb.inputs['Strength'].default_value = .26
gb.inputs['Distance'].default_value = .035
gl.new(gtex.outputs['Fac'], gb.inputs['Height'])
gl.new(gb.outputs['Normal'], gp.inputs['Normal'])


def assign(obj, mat, smooth=True):
    obj.data.materials.append(mat)
    if obj.type == 'MESH':
        for poly in obj.data.polygons:
            poly.use_smooth = smooth
    return obj


def cube(name, loc, dims, mat, bevel=.06):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(o, mat)
    if bevel:
        m = o.modifiers.new('Softly polished edges', 'BEVEL')
        m.width, m.segments = bevel, 5
        o.modifiers.new('Weighted surface normals', 'WEIGHTED_NORMAL')
    return o


base_jade = jade.copy()
base_jade.name = '印体青玉 · cool gray celadon'
base_ramp = next(n for n in base_jade.node_tree.nodes if n.type == 'VALTORGB')
for element in base_ramp.color_ramp.elements:
    r, g, b, a = element.color
    element.color = (r*.87, g*.96, min(1, b*1.08), a)
base = cube('素面方印 · plain tall seal block', (0, 0, 1.725), (6.4, 6.4, 3.45), base_jade, .075)
bpy.context.view_layer.objects.active = base
for mod in list(base.modifiers):
    bpy.ops.object.modifier_apply(modifier=mod.name)
# An irregular inverted triangle wraps the UPPER visible front-left corner.
# Distances along each adjacent face narrow toward the lower tip, matching cover.
levels = [
    (3.444, 1.02, 1.18), (3.33, .98, 1.12),
    (3.19, .86, 1.04), (3.04, .88, .90),
    (2.89, .71, .88), (2.71, .70, .76),
    (2.53, .53, .64), (2.37, .50, .50),
    (2.20, .34, .41), (2.05, .31, .27),
    (1.89, .17, .20), (1.72, .09, .08), (1.61, .025, .020)]
verts, faces = [], []
# Four columns follow the base's small rounded corner, not an oversized wrapper.
for z, left, right in levels:
    left *= 1.50
    right *= 1.50
    c = min(.049, left*.45, right*.45)
    verts.extend([(3.20-left, -3.210, z), (3.20-c, -3.210, z),
                  (3.210, -3.20+c, z), (3.210, -3.20+right, z)])
for row in range(len(levels)-1):
    for col in range(3):
        a = row*4+col
        faces.append((a, a+4, a+5, a+1))
# A small top lip follows the broken upper edge.
verts.extend([(1.67, -3.11, 3.455), (3.11, -3.11, 3.455), (3.11, -1.43, 3.455)])
faces.extend([(0, 1, 53, 52), (1, 2, 53), (2, 3, 54, 53)])
mesh = bpy.data.meshes.new('Irregular triangular repair')
verts = [(-x, y, z) for x, y, z in verts]
faces = [tuple(reversed(face)) for face in faces]
mesh.from_pydata(verts, [], faces)
mesh.update()
patch = bpy.data.objects.new('金补上角 · irregular upper-corner repair', mesh)
bpy.context.collection.objects.link(patch)
assign(patch, gold, smooth=False)
solid = patch.modifiers.new('Thin worked metal', 'SOLIDIFY')
solid.thickness = .022
bevel = patch.modifiers.new('Soft gold edges', 'BEVEL')
bevel.width, bevel.segments = .013, 2

from reference_beast import build_reference_beast
build_reference_beast(jade, recess)
from seal_inscription import add_inscription
add_inscription(base, jade)
base['Reference qualification'] = 'Underside is not visible in cover photo; inscription is an interpretive addition.'
base.modifiers.new('Engraved face normals', 'WEIGHTED_NORMAL')
bpy.ops.object.select_all(action='SELECT')
bpy.context.view_layer.objects.active = base
bpy.ops.object.convert(target='MESH')
artifact = bpy.data.collections.new('01 · 玉玺 / ARTIFACT')
bpy.context.scene.collection.children.link(artifact)
for obj in list(bpy.context.scene.objects):
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    artifact.objects.link(obj)
studio = bpy.data.collections.new('02 · 摄影布景 / STUDIO')
bpy.context.scene.collection.children.link(studio)


def studio_obj(obj):
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    studio.objects.link(obj)
    return obj


floor = studio_obj(cube('Dark photographic ground', (0, 0, -.12), (200, 200, .24),
                        material('Charcoal fabric background', (.025, .029, .026), .53), 0))


def area(name, loc, power, color, size, target=(0, 0, 3)):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.color, data.size = power, color, size
    data.shape = 'DISK'
    o = bpy.data.objects.new(name, data)
    studio.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(target)-o.location).to_track_quat('-Z', 'Y').to_euler()
    return o


area('Key softbox', (-4, -6, 11), 1450, (1, .94, .82), 6)
area('Right fill', (7, -2, 7), 700, (.80, .91, 1), 5)
area('Back rim', (-2, 5, 10), 1500, (.93, 1, .93), 5)
area('Front bounce', (1, -9, 4), 250, (1, .95, .84), 5)
area('Gold reflection card', (-8, 6, 6), 600, (1, .92, .75), 6, target=(-3, -3, 2.5))
scene = bpy.context.scene
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.11, .13, .11, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .25
bpy.ops.object.camera_add(location=(-10.5, -16.5, 6.8))
cam = studio_obj(bpy.context.object)
cam.name = 'CAMERA · cover reference view'
cam.rotation_euler = (Vector((0, 0, 3.2))-cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.type, cam.data.ortho_scale = 'ORTHO', 10.6
scene.camera = cam
scene.render.engine = 'CYCLES'
scene.cycles.samples = 48
scene.cycles.use_denoising = False  # Works on Blender builds without OpenImageDenoise.
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = .065
scene.cycles.adaptive_min_samples = 8
scene.cycles.max_bounces = 6
scene.render.resolution_x, scene.render.resolution_y = 1200, 1280
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = .015
scene['Reference URL'] = 'https://www.sohu.com/a/1091255651_122157668'
scene['Reference image'] = 'First cover photo only; mixed later illustrations are not combined.'
scene['说明'] = '依用户指定文章首图进行视觉复原。素面高方印、蹲伏兽形龙钮、上部不规则金补角。非历史原物认证；未显示的背部与印面为补全。'
for screen in bpy.data.screens:
    for area_ in screen.areas:
        if area_.type == 'VIEW_3D':
            area_.spaces.active.region_3d.view_perspective = 'CAMERA'
            area_.spaces.active.shading.type = 'MATERIAL'
bpy.ops.object.select_all(action='DESELECT')
base.select_set(True)
bpy.context.view_layer.objects.active = base
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'imperial_jade_seal.blend'))
bpy.ops.object.select_all(action='DESELECT')
for obj in artifact.objects:
    obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT / 'imperial_jade_seal.glb'), export_format='GLB',
                         use_selection=True, export_apply=True, export_yup=True)
from fix_glb_scale import scale_glb
scale_glb(OUT / 'imperial_jade_seal.glb')
if MODE == 'none':
    print('MODEL_READY', OUT)
else:
    if MODE == 'draft':
        scene.render.resolution_x, scene.render.resolution_y = 720, 768
        scene.cycles.samples = 12
    scene.render.filepath = str(OUT / ('draft.png' if MODE == 'draft' else 'preview.png'))
    bpy.ops.render.render(write_still=True)
    if MODE == 'final':
        for obj in studio.objects:
            if obj.type == 'MESH':
                obj.hide_render = True
        cam.location = (0, 0, -13)
        cam.rotation_euler = (Vector((0, 0, 0))-cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = 7.8
        area('Underside key', (-4, -3, -7), 900, (1, .94, .86), 5, target=(0, 0, 0))
        area('Underside fill', (3, 2, -5), 500, (.82, .95, 1), 4, target=(0, 0, 0))
        scene.cycles.samples = 24
        scene.render.resolution_x, scene.render.resolution_y = 1000, 1000
        scene.render.filepath = str(OUT / 'underside.png')
        bpy.ops.render.render(write_still=True)
    print('COMPLETE', OUT)
