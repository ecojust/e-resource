"""Read the final .blend and verify its packed brick shader and active loop UVs."""
import hashlib
import json
from pathlib import Path
import sys
import bpy

here=Path(__file__).resolve().parent
source=here.parents[2]/'source/precise/huangpu-zili-waterworks-office-front/source/grey-bond.png'
file=Path(bpy.data.filepath)
material=bpy.data.materials['grey fired brick']
image_node=material.node_tree.nodes['Zili fired brick']
shader=material.node_tree.nodes['Principled BSDF']
assert any(link.from_node==image_node for link in shader.inputs['Base Color'].links)
texture=image_node.image
assert list(texture.size)==[384,128]
assert texture.packed_file and bytes(texture.packed_file.data)==source.read_bytes()
rows=[]
for obj in bpy.context.scene.objects:
    if obj.type!='MESH' or material.name not in obj.data.materials:continue
    mesh=obj.data
    uv=mesh.uv_layers.active
    assert uv.name=='Brick courses'
    slots={i for i,m in enumerate(mesh.materials) if m==material}
    loops=0
    maximum=0.
    for face in mesh.polygons:
        if face.material_index not in slots:continue
        for i in face.loop_indices:
            x,y,z=mesh.vertices[mesh.loops[i].vertex_index].co
            u,v=uv.data[i].uv
            maximum=max(maximum,abs(u-(x+.74*y)/2.08),abs(v-(1+z/.576)))
            loops+=1
    assert loops>0 and maximum<.000015,(obj.name,loops,maximum)
    rows.append({'object':obj.name,'loops':loops,'max_abs_uv_error':maximum})
assert rows
Path(sys.argv[sys.argv.index('--')+1]).write_text(json.dumps({
    'native_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'texture_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'image_node':image_node.name,'uv_layer':'Brick courses','loop_checks':sum(r['loops']for r in rows),'objects':rows},indent=2)+'\n')
