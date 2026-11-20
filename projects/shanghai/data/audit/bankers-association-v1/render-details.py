"""Render source-comparable close views from the opened, final editable file."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json
import sys
import bpy
from mathutils import Vector

parser=ArgumentParser(description=__doc__)
parser.add_argument('--out',required=True,type=Path)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
args.out.mkdir(exist_ok=True,parents=True)
scene=bpy.context.scene
cam=scene.camera
scene.render.resolution_x=720
scene.render.resolution_y=600
scene.render.resolution_percentage=100
scene.cycles.samples=16
scene.cycles.use_denoising=False
data={'native_sha256':sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'blender':bpy.app.version_string,'views':[]}
for name,target,offset,scale in [
    ('column-capital',(-1.47,.64,7.87),(-.55,-5.1,-.58),2.30),
    ('central-entrance',(0,2.68,2.65),(.05,-6.1,.08),4.78)]:
    aim=Vector(target)
    cam.location=aim+Vector(offset)
    cam.rotation_euler=(aim-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=scale
    filename=args.out/(name+'.png')
    scene.render.filepath=str(filename.resolve())
    bpy.ops.render.render(write_still=True)
    data['views'].append(dict(file=filename.name,sha256=sha256(filename.read_bytes()).hexdigest(),
                              pixels=[720,600],target_m=target,offset_m=offset,ortho_m=scale))
(args.out/'detail-renders.json').write_text(json.dumps(data,indent=2)+'\n')
