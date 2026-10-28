"""blender --background --python source/surfaces/save_native.py"""
import hashlib
import json
import struct
from pathlib import Path
import bpy
from mathutils import Vector, Quaternion

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'assets/surfaces'
manifest = json.loads((ASSETS / 'manifest.json').read_bytes())
def geometry_hash(meshes):
    h = hashlib.sha256()
    for obj in sorted(meshes, key=lambda obj: obj.name):
        h.update(obj.name.encode())
        for vertex in obj.data.vertices:
            h.update(struct.pack('<3f', *vertex.co))
        for polygon in obj.data.polygons:
            h.update(struct.pack('<3I', *polygon.vertices))
    return h.hexdigest()

results = []
for record in manifest['districts']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.import_scene.gltf(filepath=str(ASSETS / record['file']))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    assert len(meshes) == 2
    assert sum(len(obj.data.polygons) for obj in meshes) == record['triangles']
    for obj in meshes:
        obj['source_glb_sha256'] = record['sha256']
        obj['elevation_status'] = 'Unknown; this is a flat display surface, not a DEM or river bed.'
        obj['license'] = 'ODbL-1.0'
    bpy.context.scene['origin_wgs84'] = record['origin_wgs84']
    bpy.context.scene['attribution'] = manifest['attribution']
    bpy.context.scene['source_template'] = manifest['source_template']
    bpy.context.scene.unit_settings.system = 'METRIC'
    points = [obj.matrix_world @ Vector(p) for obj in meshes for p in obj.bound_box]
    center = (Vector(tuple(min(p[i] for p in points) for i in range(3))) + Vector(tuple(max(p[i] for p in points) for i in range(3)))) / 2
    span = max(max(p[i] for p in points)-min(p[i] for p in points) for i in range(3))
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.clip_end = 1000000
                area.spaces.active.region_3d.view_location = center
                area.spaces.active.region_3d.view_distance = span * 1.1
                area.spaces.active.region_3d.view_rotation = Quaternion((1,0,0,0))
    filename = f"{record['id']}.blend"
    path = ASSETS / filename
    before_hash = geometry_hash(meshes)
    bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=True)
    data = path.read_bytes()
    assert len(data) < 100_000_000
    # Reopen actual saved native file, not just the in-memory import.
    bpy.ops.wm.open_mainfile(filepath=str(path))
    reopened = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    assert sum(len(obj.data.polygons) for obj in reopened) == record['triangles']
    assert geometry_hash(reopened) == before_hash
    record.update(native_file=filename, native_bytes=len(data), native_sha256=hashlib.sha256(data).hexdigest())
    results.append({'id': record['id'], 'reopened_meshes': len(reopened), 'triangles': record['triangles'],
                    'geometry_sha256_before_and_after': before_hash, 'bytes': len(data), 'sha256': record['native_sha256']})
(ASSETS / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
(ROOT / 'data/audit/surfaces-v1/native.json').write_text(json.dumps({'blender': bpy.app.version_string, 'results': results}, ensure_ascii=False, indent=2) + '\n')
