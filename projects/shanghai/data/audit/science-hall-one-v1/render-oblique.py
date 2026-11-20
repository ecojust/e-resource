"""Render a second view of the saved native model from the garden, west of its central axis."""
import argparse
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import bpy
from mathutils import Vector

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('output', type=Path)
parser.add_argument('--oidn', default='oidnDenoise')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
scene = bpy.context.scene
camera = scene.camera
target = Vector((0, 7.45, 7.7))
camera.location = target + Vector((-56, -116, 26))
camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 102
scene.render.resolution_percentage = 100
scene.render.resolution_x = 1120
scene.render.resolution_y = 430
scene.cycles.samples = 12
scene.cycles.use_denoising = False
scene.render.image_settings.file_format = 'PNG'
with TemporaryDirectory() as temp:
    work = Path(temp)
    raw = work/'render.png'
    scene.render.filepath = str(raw)
    bpy.ops.render.render(write_still=True)
    subprocess.run(['magick', raw, '-colorspace', 'sRGB', '-endian', 'LSB', work/'rgb.pfm'], check=True)
    subprocess.run([args.oidn, '-d', 'cpu', '--threads', '1', '--ldr', work/'rgb.pfm', '--srgb',
                    '-o', work/'denoised.pfm'], check=True)
    subprocess.run(['magick', work/'denoised.pfm', '-set', 'colorspace', 'sRGB', '-depth', '8', args.output], check=True)
