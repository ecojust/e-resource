"""Check the camera stored in the delivered Blender project, after opening the project."""
from hashlib import sha256
import json
from pathlib import Path
import sys
import bpy

args = sys.argv[sys.argv.index('--') + 1:]
source = Path(bpy.data.filepath).resolve()
camera = bpy.context.scene.camera
assert camera.name == '吉祥里西弄门 · 山东北路正面'
assert camera.data.name == '吉祥里西弄门正面正交相机'
assert camera.data.type == 'ORTHO'
assert not any('grace church' in obj.name.lower() for obj in bpy.data.objects)
result = {
    'blend': source.name,
    'sha256': sha256(source.read_bytes()).hexdigest(),
    'blender': bpy.app.version_string,
    'active_camera': camera.name,
    'camera_data': camera.data.name,
    'projection': camera.data.type,
    'scale': camera.data.ortho_scale,
    'mesh_count': sum(obj.type == 'MESH' for obj in bpy.context.scene.objects),
    'passed': True,
}
Path(args[0]).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
