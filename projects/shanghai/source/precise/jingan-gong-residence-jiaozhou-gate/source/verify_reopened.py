"""Check the saved, reopened cameras, actual nameplate UVs and packed photograph-derived image."""

from pathlib import Path
import hashlib, json, sys
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

src = Path(__file__).resolve().parent
sys.path.insert(0, str(src))
from native_layout import MAIN, CAMERAS, MATERIALS, UV_NAME, uv

blend, raw, output = map(Path, sys.argv[sys.argv.index("--") + 1 :])
scene = bpy.context.scene
assert Path(bpy.data.filepath).resolve() == blend.resolve()
r = json.loads(output.read_bytes())
assert r["match_raw"] and scene.camera.name == MAIN
expected = hashlib.sha256((src / "entrance-plaques.png").read_bytes()).hexdigest()
packed = {}
for name in MATERIALS:
    graph = bpy.data.materials[name].node_tree
    node = graph.nodes["2015 plaque photograph"]
    packed[name] = hashlib.sha256(bytes(node.image.packed_file.data)).hexdigest()
    assert packed[name] == expected and tuple(node.image.size) == (384, 96)
    assert any(x.from_node == node and x.to_socket.name == "Base Color" for x in graph.links)
panes = 0
for obj in scene.objects:
    if obj.type != "MESH":
        continue
    for face in obj.data.polygons:
        mat = obj.data.materials[face.material_index].name
        if mat not in MATERIALS:
            continue
        layer = obj.data.uv_layers[UV_NAME]
        panes += 1
        for k in face.loop_indices:
            assert (
                Vector(uv(mat, obj.data.loops[k].vertex_index)) - layer.data[k].uv
            ).length < 1e-6
assert panes == 6
views = {}
for name, (eye, target, width) in CAMERAS.items():
    obj = bpy.data.objects[name]
    assert obj.data.type == "ORTHO" and (obj.location - Vector(eye)).length < 1e-4
    assert abs(obj.data.ortho_scale - width) < 1e-4
    t = world_to_camera_view(scene, obj, Vector(target))
    assert abs(t.x - 0.5) < 1e-3 and abs(t.y - 0.5) < 1e-3
    views[name] = dict(eye=list(obj.location), focus=list(target), width_m=width)
assert "CC BY-SA 4.0" in scene["photograph_credit"]
r["gong_residence_gate"] = dict(
    packed_image_sha256=packed,
    camera_count=len(views),
    views=views,
    plaque_triangles_with_checked_uv=panes,
)
output.write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n")
