"""Check embedded artwork, actual editable loop UVs and the reopened native file."""
import json
import sys
from pathlib import Path
from hashlib import sha256
import bpy
source=Path(__file__).resolve().parent
sys.path.insert(0,str(source))
from stone_finish import CARVED as MATERIAL, IMAGE, uv

blend,raw,report=map(Path,sys.argv[sys.argv.index('--')+1:])
assert Path(bpy.data.filepath).resolve()==blend.resolve()
material=bpy.data.materials[MATERIAL]
texture=material.node_tree.nodes['Original limewashed street facing']
image=texture.image
assert image.packed_file and list(image.size)==[960,768]
checksum=sha256(bytes(image.packed_file.data)).hexdigest()
assert checksum==sha256(IMAGE.read_bytes()).hexdigest()
count=0
for obj in bpy.context.scene.objects:
    if obj.type!='MESH' or material.name not in obj.data.materials:
        continue
    mesh=obj.data
    layer=mesh.uv_layers['Jinling plaster']
    for face in mesh.polygons:
        if mesh.materials[face.material_index]!=material:
            continue
        for index in face.loop_indices:
            world=obj.matrix_world@mesh.vertices[mesh.loops[index].vertex_index].co
            u,v=uv(world)
            actual=layer.data[index].uv
            assert abs(actual.x-u)<1e-5 and abs(actual.y-(1-v))<1e-5
            count+=1
assert count>0
doc=json.loads(report.read_bytes())
assert doc['match_raw']
doc['packed_jinling_masonry']={'image':IMAGE.name,'sha256':checksum,'corner_uvs':count,'size':list(image.size)}
report.write_text(json.dumps(doc,indent=2)+'\n')
