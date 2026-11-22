"""Read the final .blend and verify its packed clay roof shader and active loop UVs."""
import hashlib
import json
from pathlib import Path
import sys
import bpy

here=Path(__file__).resolve().parent
source=here.parents[2]/'source/precise/jingan-kangding-garden-central-portico/source/tiles.png'
sys.path.insert(0,str(source.parent))
from roof_tiles import roof_uv
file=Path(bpy.data.filepath)
material=bpy.data.materials['Terracotta roof tiles']
image_node=material.node_tree.nodes['Kangding roof tiles']
shader=material.node_tree.nodes['Principled BSDF']
assert any(link.from_node==image_node for link in shader.inputs['Base Color'].links)
texture=image_node.image
assert list(texture.size)==[120,120]
assert texture.packed_file and bytes(texture.packed_file.data)==source.read_bytes()
rows=[]
for obj in bpy.context.scene.objects:
    if obj.type!='MESH' or material.name not in obj.data.materials:continue
    mesh=obj.data
    uv=mesh.uv_layers.active
    assert uv.name=='Clay roof tile courses'
    slots={i for i,m in enumerate(mesh.materials) if m==material}
    loops=0
    maximum=0.
    for face in mesh.polygons:
        if face.material_index not in slots:continue
        for i in face.loop_indices:
            x,y,z=mesh.vertices[mesh.loops[i].vertex_index].co
            u,v=uv.data[i].uv
            expected_u,expected_v=roof_uv(x,y,z)
            maximum=max(maximum,abs(u-expected_u),abs(v-(1-expected_v)))
            loops+=1
    assert loops>0 and maximum<.000015,(obj.name,loops,maximum)
    rows.append({'object':obj.name,'loops':loops,'max_abs_uv_error':maximum})
assert rows
Path(sys.argv[sys.argv.index('--')+1]).write_text(json.dumps({
    'native_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'texture_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'image_node':image_node.name,'uv_layer':'Clay roof tile courses','loop_checks':sum(r['loops']for r in rows),'objects':rows},indent=2)+'\n')
