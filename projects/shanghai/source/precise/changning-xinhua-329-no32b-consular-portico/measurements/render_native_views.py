"""Render the ten named cameras by reopening the downloadable Blender courtyard project."""
import hashlib
import json
from pathlib import Path
import sys
import bpy

out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(parents=True,exist_ok=True)
source=Path(bpy.data.filepath)
def sha(p):
    with p.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()
scene=bpy.context.scene
names=json.loads((Path(__file__).absolute().parent/'courtyard-cameras.json').read_bytes())
cams={obj['camera_id']:obj for obj in scene.objects if obj.type=='CAMERA'}
assert len(cams)==len(names)==10
scene.render.engine='CYCLES'
scene.cycles.device='CPU'
scene.cycles.samples=4
scene.cycles.use_denoising=False
scene.render.threads_mode='FIXED';scene.render.threads=1
scene.render.resolution_x=384;scene.render.resolution_y=300;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.render.use_persistent_data=False
scene.cycles.use_auto_tile=True;scene.cycles.tile_size=64
source_sha=sha(source)
rows=[]
for i,view in enumerate(names):
    name=view['name'];obj=cams[name];scene.camera=obj
    image=out/f'camera-{i+1:02d}.png';ticket=image.with_suffix('.json')
    if ticket.exists():
        old=json.loads(ticket.read_bytes())
        if old['editable_sha256']==source_sha and sha(image)==old['image_sha256']:
            rows.append(old);continue
    scene.render.filepath=str(image);bpy.ops.render.render(write_still=True)
    scan=bpy.data.images.load(str(image),check_existing=False)
    assert list(scan.size)==[384,300]
    values=[]
    for y in range(3,300,7):
        for x in range(3,384,7):
            k=4*(y*384+x)
            values.append(sum(scan.pixels[k+c] for c in range(3))/3)
    bpy.data.images.remove(scan)
    values.sort();contrast=values[-20]-values[19]
    assert contrast>.018,(name,contrast)
    report=dict(view=name,camera=obj.name,editable_sha256=source_sha,image_sha256=sha(image),file=image.name,
                width=384,height=300,contrast=round(contrast,5),engine='CYCLES',samples=4)
    ticket.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');rows.append(report)
(out/'native-cameras.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
