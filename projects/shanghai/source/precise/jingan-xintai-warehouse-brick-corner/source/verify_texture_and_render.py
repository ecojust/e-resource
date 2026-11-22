import bpy,json,os,hashlib
from pathlib import Path
s=json.loads(Path(os.environ['PAGE_NATIVE_SOURCE']).read_bytes());count=0;images={}
for name,g in s['groups'].items():
 obj=bpy.data.objects[name].data
 if g['uv'] is None:continue
 layer=obj.uv_layers.active;assert layer
 for loop in obj.loops:
  a,b=layer.data[loop.index].uv;u,v=g['uv'][loop.vertex_index];assert abs(a-u)<2e-6 and abs(1-v-b)<2e-6;count+=1
for name,v in s['palette'].items():
 if not v.get('texture')or name not in bpy.data.materials:continue
 image=next(n for n in bpy.data.materials[name].node_tree.nodes if n.type=='TEX_IMAGE').image
 sha=lambda b:hashlib.sha256(b).hexdigest();x=sha(image.packed_file.data);assert x==sha(Path(v['texture']).read_bytes());images[image.name]=x
assert count>0 and images
Path(os.environ['PAGE_NATIVE_UV']).write_text(json.dumps(dict(passed=True,uv_loops=count,packed_images=images),indent=2)+'\n')

scene=bpy.context.scene
assert scene.camera and 'Recessed steel sash' in bpy.data.objects
scene.render.filepath=os.environ['XINTAI_RENDER']
bpy.ops.render.render(write_still=True)
