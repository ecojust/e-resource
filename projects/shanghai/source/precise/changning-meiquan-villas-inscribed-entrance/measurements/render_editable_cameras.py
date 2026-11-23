"""Render all nine editable cameras of the Meiquan Villas entrance."""
import hashlib
import json
from pathlib import Path
import sys

def render(out):
    import bpy
    scene=bpy.context.scene
    views=json.loads((Path(__file__).absolute().parent.parent/'source/cameras.json').read_bytes())
    out.mkdir(parents=True,exist_ok=True)
    scene.render.engine='CYCLES'
    scene.cycles.device='CPU'
    scene.cycles.samples=6
    scene.cycles.use_denoising=False
    scene.render.threads_mode='FIXED';scene.render.threads=1
    scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=False
    scene.render.resolution_percentage=100
    report=[]
    for item in views:
        camera=bpy.data.objects[item['label']]
        if camera.type!='CAMERA':raise ValueError(item['label'])
        scene.camera=camera
        scene.render.pixel_aspect_x=float(item.get('blender_pixel_aspect_x',1.))
        scene.render.pixel_aspect_y=float(item.get('blender_pixel_aspect_y',1.))
        ratio=min(510/item['width'],420/item['height'])
        scene.render.resolution_x=round(item['width']*ratio);scene.render.resolution_y=round(item['height']*ratio)
        output=out/(item['name']+'.png');scene.render.filepath=str(output)
        bpy.ops.render.render(write_still=True)
        report.append({'view':item['name'],'camera':camera.name,'width':scene.render.resolution_x,
                       'height':scene.render.resolution_y,'file':output.name,'bytes':output.stat().st_size,
                       'sha256':hashlib.sha256(output.read_bytes()).hexdigest()})
    (out/'nine-cameras.json').write_text(json.dumps({'engine':scene.render.engine,'samples':scene.cycles.samples,
        'registered_photo_cameras':[item['name'] for item in views if item.get('reference')],
        'editable_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'views':report},
        ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':render(Path(sys.argv[sys.argv.index('--')+1]))
