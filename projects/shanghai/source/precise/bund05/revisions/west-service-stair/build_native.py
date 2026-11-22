"""Build, reopen, and render the editable Bund 5 scene.

Pass the raw GLB, pinned footprint JSON, destination Blend, PNG and JSON report
after Blender's double dash. The production GLBs exclude cameras and the ground.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def sha(path):
    with path.open('rb') as data:
        return hashlib.file_digest(data, 'sha256').hexdigest()


def move_to_collection(obj, collection):
    for parent in list(obj.users_collection):
        parent.objects.unlink(obj)
    collection.objects.link(obj)


def aim(camera, target):
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()


def orthographic_camera(name, location, target, scale, collection):
    bpy.ops.object.camera_add(location=location)
    camera = bpy.context.object
    camera.name = name
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = scale
    aim(camera, target)
    move_to_collection(camera, collection)
    return camera


raw, geometry, native, picture, report = [
    Path(arg).resolve() for arg in sys.argv[sys.argv.index('--') + 1:]
]
ring = json.loads(geometry.read_bytes())['polygon_local_east_north']
north_end, south_end = [Vector((*point, 0)) for point in ring[:2]]
tangent = (south_end - north_end).normalized()
outward = Vector((tangent.y, -tangent.x, 0))


def west_point(station, height, depth):
    point = south_end - tangent * station + outward * depth
    return Vector((point.x, point.y, height))


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(raw))
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 16
scene.cycles.use_denoising = False
scene.render.threads_mode = 'FIXED'
scene.render.threads = 1
scene.render.resolution_x = 940
scene.render.resolution_y = 680
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'

mesh, = [obj for obj in scene.objects if obj.type == 'MESH']
mesh.name = 'Bund 5, Nissin Building with west return'
building = bpy.data.collections.new('Photo_reconstructed_architecture')
scene.collection.children.link(building)
move_to_collection(mesh, building)
stair = mesh.vertex_groups.new(name='West flight, landing and ironwork')
windows = mesh.vertex_groups.new(name='West return, two arched transoms')
stair_vertices, sash_vertices = [], []
for vertex in mesh.data.vertices:
    point = mesh.matrix_world @ vertex.co
    position = point - south_end
    depth = position.dot(outward)
    station = -position.dot(tangent)
    if .38 < station < 5.65 and .075 < depth < 1.89 and -.02 <= point.z < 3.31:
        stair_vertices.append(vertex.index)
    elif .9 < station < 7.0 and -.42 < depth < .42 and 1.15 < point.z < 4.58:
        sash_vertices.append(vertex.index)
stair.add(stair_vertices, 1.0, 'REPLACE')
windows.add(sash_vertices, 1.0, 'REPLACE')

if scene.world is None:
    scene.world = bpy.data.worlds.new('Overcast exterior')
scene.world.use_nodes = True
background = scene.world.node_tree.nodes.get('Background')
background.inputs[0].default_value = (.74, .78, .81, 1)
background.inputs[1].default_value = .75

preview = bpy.data.collections.new('Preview_only')
scene.collection.children.link(preview)
bpy.ops.object.light_add(type='SUN', location=west_point(2, 14, 14))
sun = bpy.context.object
aim(sun, west_point(3, 2, 0))
sun.data.energy = 2.1
sun.data.angle = .17
move_to_collection(sun, preview)

# Keep a second view of the entire building from its historic east front.
bounds = [mesh.matrix_world @ Vector(point) for point in mesh.bound_box]
centre = sum(bounds, Vector((0, 0, 0))) / len(bounds)
extent = max(max(p[i] for p in bounds) - min(p[i] for p in bounds) for i in range(3))
azimuth = math.radians(55.881557895)
east_eye = centre + Vector((math.sin(azimuth), math.cos(azimuth), math.tan(math.radians(8)))) * (2 * extent)
orthographic_camera('East frontage, river approach', east_eye, centre, extent * 1.16, preview)
scene.camera = orthographic_camera(
    'West stair and Guangdong Road return', west_point(-3.6, 3.72, 8.6),
    west_point(3.65, 2.12, .60), 10.4, preview)

bpy.ops.mesh.primitive_plane_add(size=170, location=(0, 0, -.037))
ground = bpy.context.object
ground.name = 'Presentation ground'
material = bpy.data.materials.new('Neutral ground')
material.diffuse_color = (.42, .43, .42, 1)
ground.data.materials.append(material)
move_to_collection(ground, preview)
bpy.ops.object.select_all(action='DESELECT')
mesh.select_set(True)
bpy.context.view_layer.objects.active = mesh

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.file.pack_all()
native.parent.mkdir(exist_ok=True, parents=True)
bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=True)
bpy.ops.wm.open_mainfile(filepath=str(native))
scene = bpy.context.scene
mesh = bpy.data.objects['Bund 5, Nissin Building with west return']
mesh.data.calc_loop_triangles()
images = []
for item in bpy.data.images:
    if item.packed_file:
        body = item.packed_file.data
        images.append({'name': item.name, 'pixels': list(item.size), 'bytes': len(body),
                       'sha256': hashlib.sha256(body).hexdigest()})
photo, = images
assert (photo['bytes'], photo['sha256']) == (
    5675385, '3cff1c24a4762a0c099d8b96d663fc704871421853b8904a95327f5352f574b3')
groups = {group.name: sum(any(membership.group == group.index for membership in vertex.groups)
                          for vertex in mesh.data.vertices) for group in mesh.vertex_groups}
assert len(groups) == 2 and all(count > 80 for count in groups.values())
assert len(mesh.data.loop_triangles) == 154972
scene.render.filepath = str(picture)
picture.parent.mkdir(exist_ok=True, parents=True)
bpy.ops.render.render(write_still=True)
result = {
    'native_sha256': sha(native), 'native_bytes': native.stat().st_size,
    'raw_sha256': sha(raw), 'blender_version': bpy.app.version_string,
    'reopened_architecture_triangles': len(mesh.data.loop_triangles),
    'editable_vertex_groups': groups, 'images': images,
    'preview_sha256': sha(picture), 'preview_bytes': picture.stat().st_size,
    'view': scene.camera.name, 'second_camera': 'East frontage, river approach',
    'preview_only_collection': 'Preview_only',
}
report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
