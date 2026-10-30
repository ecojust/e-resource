"""Save the original Grand Theatre candidate and render actual Cycles previews."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

import bpy
from mathutils import Vector


SCOPE = (
    'Grand Theatre cinema at 216 Nanjing West Road: bounded street entrance/light tower and adjacent curved '
    'return exterior candidate only. The chosen 30.5 m design height is one '
    'interpretation of secondary references; the alternate 16 m statement is '
    'unresolved and height endpoints are unverified. Width approximately 23.85 m '
    'and depth approximately 9.32 m including the canopy are design estimates. '
    'Rear auditorium, full roof and the whole shop strip are excluded. References mix a '
    '2010 photograph with undated historic and repaired night views; this is '
    'not a single-period reconstruction. Not geographically registered or '
    'approved for map replacement. Original MIT geometry; no reference images embedded.'
)


def geometry_hash(objects):
    digest = hashlib.sha256()
    for obj in sorted(objects, key=lambda item: item.name):
        digest.update(obj.name.encode())
        for row in obj.matrix_world:
            digest.update(struct.pack('<4f', *row))
        for vertex in obj.data.vertices:
            digest.update(struct.pack('<3f', *vertex.co))
        for polygon in obj.data.polygons:
            assert len(polygon.vertices) == 3, 'Original mesh must remain triangulated'
            digest.update(struct.pack('<3I', *polygon.vertices))
    return digest.hexdigest()


parser = argparse.ArgumentParser()
parser.add_argument('--raw', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
parser.add_argument('--previews', type=Path, required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.import_scene.gltf(filepath=str(args.raw.resolve()))
model = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
assert len(model) == 1, 'One entrance/light-tower and curved-return model mesh expected'
source_sha256 = hashlib.sha256(args.raw.read_bytes()).hexdigest()
for obj in model:
    obj['source_raw_sha256'] = source_sha256
    obj['scope'] = SCOPE
    obj.data = obj.data.copy()

raw_bytes = args.raw.read_bytes()
json_size = struct.unpack_from('<I', raw_bytes, 12)[0]
raw_doc = json.loads(raw_bytes[20:20 + json_size])
expected = sum(
    raw_doc['accessors'][primitive['indices']]['count'] // 3
    for mesh in raw_doc['meshes'] for primitive in mesh['primitives']
)
count = sum(len(obj.data.polygons) for obj in model)
assert count == expected, f'Blender import changed face count: {count} vs {expected}'
before_hash = geometry_hash(model)

scene = bpy.context.scene
collection = bpy.data.collections.new('Preview stage — not part of the building')
scene.collection.children.link(collection)


def stage(obj):
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    collection.objects.link(obj)


target = Vector((0, 1, 14))
bpy.ops.mesh.primitive_plane_add(size=180, location=(0, 0, -.1))
ground = bpy.context.object
ground.name = 'Preview only — not surveyed ground'
stage(ground)
mat = bpy.data.materials.new('Preview neutral ground')
mat.diffuse_color = (.22, .25, .22, 1)
ground.data.materials.append(mat)
bpy.ops.object.light_add(type='AREA', location=(-35, -45, 65))
key = bpy.context.object
key.data.energy = 7000
key.data.shape = 'DISK'
key.data.size = 8
key.rotation_euler = (target - key.location).to_track_quat('-Z', 'Y').to_euler()
stage(key)
bpy.ops.object.light_add(type='SUN', location=(0, 0, 20))
sun = bpy.context.object
sun.data.energy = 2.2
sun.rotation_euler = (.45, -.45, -.5)
stage(sun)
bpy.ops.object.camera_add()
camera = bpy.context.object
camera.name = 'Preview camera'
camera.data.lens = 48
stage(camera)
scene.camera = camera
scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
scene.cycles.use_denoising = False
scene.render.resolution_x = 1000
scene.render.resolution_y = 700
scene.render.resolution_percentage = 100
scene.world = bpy.data.worlds.new('Preview world')
scene.world.color = (.25, .25, .25)
scene.view_settings.view_transform = 'AgX'
scene.render.image_settings.file_format = 'PNG'
scene.unit_settings.system = 'METRIC'
args.previews.mkdir(parents=True, exist_ok=True)
args.out.parent.mkdir(parents=True, exist_ok=True)
views = {
    'native-front': (0, -70, 35),
    'native-oblique': (-48, -65, 42),
    'native-rear': (48, 65, 42),
}
for name, position in views.items():
    camera.location = position
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str((args.previews / (name + '.png')).resolve())
    bpy.ops.render.render(write_still=True)

camera.location = views['native-oblique']
camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
scene['model_mesh_names'] = [obj.name for obj in model]
scene['status'] = 'Standalone exterior candidate; not geographically registered or accepted as a complete reconstruction.'
scene['scope'] = SCOPE
scene['candidate_metadata_json'] = json.dumps(raw_doc.get('extras', {}), ensure_ascii=False)
scene['preview_stage_excluded_from_model'] = True
bpy.ops.wm.save_as_mainfile(filepath=str(args.out.resolve()), compress=True)
assert 0 < args.out.stat().st_size < 100_000_000
bpy.ops.wm.open_mainfile(filepath=str(args.out.resolve()))
reopened = [bpy.data.objects[name] for name in bpy.context.scene['model_mesh_names']]
assert len(reopened) == 1
assert geometry_hash(reopened) == before_hash
assert sum(len(obj.data.polygons) for obj in reopened) == count
assert json.loads(bpy.context.scene['candidate_metadata_json']) == raw_doc.get('extras', {})
report = {
    'source_raw_sha256': source_sha256,
    'blender': bpy.app.version_string,
    'model_triangles': count,
    'model_meshes': len(reopened),
    'geometry_hash_before_and_after_reopen': before_hash,
    'bytes': args.out.stat().st_size,
    'sha256': hashlib.sha256(args.out.read_bytes()).hexdigest(),
    'stage_excluded_from_geometry_hash': True,
    'candidate_metadata_preserved_after_reopen': True,
    'independent_editable_components_after_reopen': 1,
    'previews': list(views),
}
(args.previews / 'native.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
