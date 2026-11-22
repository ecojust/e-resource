"""Verify the two original images and the loop UVs in the independently reopened Blend."""
from hashlib import sha256
from pathlib import Path
import json
import sys

import bpy

source = Path(__file__).resolve().parent
sys.path.insert(0,str(source))
from brickwork import texture_uv
blend,raw,output = [Path(v) for v in sys.argv[sys.argv.index('--')+1:]]
assert Path(bpy.data.filepath).resolve() == blend.resolve()
checks = {}
for name,file in [('charcoal grey face brick','grey-brick.png'),('dull red face brick','red-brick.png')]:
    mat = bpy.data.materials[name]
    image = mat.node_tree.nodes['Hengye running bond'].image
    assert list(image.size) == [1024,1024]
    actual = sha256(bytes(image.packed_file.data)).hexdigest()
    assert actual == sha256((source/file).read_bytes()).hexdigest()
    loops = 0
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH' or name not in obj.data.materials:
            continue
        mesh = obj.data
        layer = mesh.uv_layers['Brick courses']
        for face in mesh.polygons:
            if mesh.materials[face.material_index].name != name:
                continue
            for i in face.loop_indices:
                ref = texture_uv(*mesh.vertices[mesh.loops[i].vertex_index].co)
                assert max(abs(a-b) for a,b in zip(layer.data[i].uv,ref)) < 1e-5
                loops += 1
    assert loops > 0
    checks[name] = {'file':file, 'sha256':actual, 'size':list(image.size), 'checked_corner_uvs':loops}
report = json.loads(output.read_bytes())
assert report['match_raw']
report['packed_images_and_uvs'] = checks
output.write_text(json.dumps(report,indent=2)+'\n')
