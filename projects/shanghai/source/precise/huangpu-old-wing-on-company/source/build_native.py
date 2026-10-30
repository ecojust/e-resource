"""Save the original Old Wing On Company candidate and render actual Cycles previews."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view


SCOPE = (
    'Old Wing On Company (老永安公司), 635 East Nanjing Road: historic '
    'main-building exterior and Qiyun Pavilion (绮云阁) candidate. The official '
    'gazetteer also writes the pavilion name as Yiyun Pavilion (倚云阁). '
    'New Wing On Company at 627 East Nanjing Road is a separate building and '
    'is excluded, together with the former connecting bridges. This is not '
    'Sincere Company or its Moxing Tower. The official old-building description '
    'is six storeys with a local seventh storey and a two-storey roof pavilion; '
    'these descriptions are not surveyed datum levels. All model plan and '
    'tower dimensions, facade bay widths, curves, ornamental profiles, '
    'rear elevations and roof junctions are author estimates. The thin mast is '
    'based on modern photos and is not asserted to be historically original. '
    'The frozen map '
    'footprint is a coarse coverage reference, not a surveyed historic plan. '
    'Modern advertisements, interiors, neighboring buildings and an unverified '
    'courtyard are excluded. Reference photograph pixels are not embedded. '
    'Not geographically registered or approved for map replacement. '
    'Original MIT geometry.'
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
assert len(model) == 1, 'One Old Wing On main-building and Qiyun Pavilion model mesh expected'
source_sha256 = hashlib.sha256(args.raw.read_bytes()).hexdigest()
for obj in model:
    obj['source_raw_sha256'] = source_sha256
    obj['scope'] = SCOPE
    obj.data = obj.data.copy()

raw_bytes = args.raw.read_bytes()
json_size = struct.unpack_from('<I', raw_bytes, 12)[0]
raw_doc = json.loads(raw_bytes[20:20 + json_size])
assert raw_doc['extras']['id'] == 'huangpu-old-wing-on-company', 'Unexpected candidate identity'
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


target = Vector((0, 0, 24))
bpy.ops.mesh.primitive_plane_add(size=350, location=(0, 0, -.1))
ground = bpy.context.object
ground.name = 'Preview only — not surveyed ground'
stage(ground)
mat = bpy.data.materials.new('Preview neutral ground')
mat.diffuse_color = (.22, .25, .22, 1)
ground.data.materials.append(mat)
bpy.ops.object.light_add(type='AREA', location=(75, 105, 140))
key = bpy.context.object
key.data.energy = 12000
key.data.shape = 'DISK'
key.data.size = 8
key.rotation_euler = (target - key.location).to_track_quat('-Z', 'Y').to_euler()
stage(key)
bpy.ops.object.light_add(type='SUN', location=(0, 0, 20))
sun = bpy.context.object
sun.data.energy = 2.2
sun.rotation_euler = (-.55, .35, -.35)
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
    'native-front': (0, 200, 46),
    'native-oblique': (150, 185, 64),
    'native-rear': (-150, -185, 105),
    'native-corner': (100, 135, 48),
}
bpy.context.view_layer.update()
world_bbox_corners = [obj.matrix_world @ Vector(corner)
                     for obj in model for corner in obj.bound_box]
mast_xy = raw_doc['extras']['tower_location_photo_guided_xy_unmeasured']
mast_tip = Vector((*mast_xy, raw_doc['extras']['tower_modern_mast_top_design_m']))
preview_records = []
for name, position in views.items():
    camera.location = position
    view_target = Vector((8, 42, 30)) if name == 'native-corner' else target
    camera.data.type = 'ORTHO' if name == 'native-corner' else 'PERSP'
    camera.data.ortho_scale = 105
    camera.rotation_euler = (view_target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    # Frame the actual imported model in the current camera. The corner detail
    # may crop the long side horizontally, but all eight conservative world
    # bounding-box corners and the mast must retain 3% top/bottom margins.
    for frame_step in range(30):
        bpy.context.view_layer.update()
        projected = [world_to_camera_view(scene, camera, point)
                     for point in [*world_bbox_corners, mast_tip]]
        ndc_min = [min(point[axis] for point in projected) for axis in range(3)]
        ndc_max = [max(point[axis] for point in projected) for axis in range(3)]
        vertical_ok = ndc_min[1] >= .03 and ndc_max[1] <= .97
        horizontal_ok = name == 'native-corner' or (ndc_min[0] >= .03 and ndc_max[0] <= .97)
        if vertical_ok and horizontal_ok and ndc_min[2] > 0:
            break
        if camera.data.type == 'ORTHO':
            camera.data.ortho_scale *= 1.08
        else:
            camera.location = view_target + (camera.location - view_target) * 1.08
    else:
        raise AssertionError(f'Unable to frame actual model and mast in {name}')
    scene.render.filepath = str((args.previews / (name + '.png')).resolve())
    bpy.ops.render.render(write_still=True)
    preview_path = args.previews / (name + '.png')
    preview_records.append({
        'file': preview_path.name,
        'bytes': preview_path.stat().st_size,
        'sha256': hashlib.sha256(preview_path.read_bytes()).hexdigest(),
        'camera_location_enu_m': list(camera.location),
        'camera_target_enu_m': list(view_target),
        'camera_type': camera.data.type,
        'ortho_scale_m': camera.data.ortho_scale if camera.data.type == 'ORTHO' else None,
        'framing_adjustment_steps': frame_step,
        'actual_model_world_bbox8_and_mast_ndc_min': ndc_min,
        'actual_model_world_bbox8_and_mast_ndc_max': ndc_max,
        'mast_tip_enu_m': list(mast_tip),
        'mast_tip_ndc': list(projected[-1]),
        'vertical_frame_margin_at_least_3_percent': True,
        'long_side_horizontal_crop_allowed': name == 'native-corner',
    })

camera.location = next(r['camera_location_enu_m'] for r in preview_records if r['file'] == 'native-oblique.png')
camera.data.type = 'PERSP'
camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
scene['model_mesh_names'] = [obj.name for obj in model]
scene['candidate_id'] = raw_doc['extras']['id']
scene['status'] = 'Standalone exterior candidate; not geographically registered or accepted as a complete reconstruction.'
scene['scope'] = SCOPE
scene['candidate_metadata_json'] = json.dumps(raw_doc.get('extras', {}), ensure_ascii=False)
scene['preview_stage_excluded_from_model'] = True
bpy.ops.wm.save_as_mainfile(filepath=str(args.out.resolve()), compress=True)
assert 0 < args.out.stat().st_size < 100_000_000
bpy.ops.wm.open_mainfile(filepath=str(args.out.resolve()))
reopened = [bpy.data.objects[name] for name in bpy.context.scene['model_mesh_names']]
assert len(reopened) == 1
assert bpy.context.scene['candidate_id'] == 'huangpu-old-wing-on-company'
assert all(obj['source_raw_sha256'] == source_sha256 for obj in reopened)
assert geometry_hash(reopened) == before_hash
assert sum(len(obj.data.polygons) for obj in reopened) == count
assert json.loads(bpy.context.scene['candidate_metadata_json']) == raw_doc.get('extras', {})
report = {
    'id': 'huangpu-old-wing-on-company',
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
    'preview_images': preview_records,
}
(args.previews / 'native.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
