"""Render the seven cameras stored in the editable Li Garden gatehouse blend.

blender gatehouse.blend -b --threads 1 --python render_views.py -- output-directory
"""
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

source = Path(__file__).resolve().parent
output = Path(sys.argv[sys.argv.index('--') + 1]).resolve()
output.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
views = json.loads((source / 'cameras.json').read_bytes())
rendered = []
for view in views:
    camera = scene.objects.get(view['label'])
    if camera is None or camera.type != 'CAMERA':
        raise ValueError(view['label'])
    eye = Vector(view['eye'])
    target = Vector(view['target'])
    assert (camera.location - eye).length < .0001
    assert (Vector(camera['target_local_m']) - target).length < .0001
    assert abs(camera.data.sensor_width * (target-eye).length / camera.data.lens - view['width_m']) < .001
    scene.camera = camera
    scene.render.resolution_x, scene.render.resolution_y = view['width'], view['height']
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    destination = output / (view['name'] + '.png')
    scene.render.filepath = str(destination)
    bpy.ops.render.render(write_still=True)
    content = destination.read_bytes()
    assert content.startswith(b'\x89PNG\r\n\x1a\n')
    rendered.append(dict(view=view['name'], file=destination.name, bytes=len(content),
                         sha256=hashlib.sha256(content).hexdigest()))
report = output / 'rendered-cameras.json'
report.write_text(json.dumps(rendered, ensure_ascii=False, indent=2) + '\n')
