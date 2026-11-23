"""Render chosen build-time cameras; run in Blender with -- EDITABLE.blend cameras.json output."""
import bpy,json,sys
from pathlib import Path
file,definitions,output=map(Path,sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.open_mainfile(filepath=str(file.resolve()),load_ui=False)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=4;scene.cycles.use_denoising=False
scene.cycles.device='CPU';scene.render.threads_mode='FIXED';scene.render.threads=1
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';output.mkdir(exist_ok=True,parents=True)
for row in json.loads(definitions.read_bytes()):
    scene.camera=scene.objects[row['name']]
    w,h=row['width'],row['height']; scale=520/max(w,h)
    scene.render.resolution_x=round(w*scale);scene.render.resolution_y=round(h*scale);scene.render.resolution_percentage=100
    scene.render.filepath=str((output/(row['name']+'.png')).resolve())
    bpy.ops.render.render(write_still=True)
