"""Read the reopened Blender file, including its cameras, thin fanlight glass and editable parts."""

from pathlib import Path
import json, sys
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from native_cameras import MAIN, CAMERAS

blend, raw, output = map(Path, sys.argv[sys.argv.index("--") + 1 :])
scene = bpy.context.scene
assert Path(bpy.data.filepath).resolve() == blend.resolve()
report = json.loads(output.read_bytes())
assert report["match_raw"] and scene.camera.name == MAIN
views = {}
for name, (eye, target, span) in CAMERAS.items():
    camera = bpy.data.objects[name]
    data = camera.data
    assert data.type == "PERSP" and data.sensor_fit == "HORIZONTAL"
    assert (camera.location - Vector(eye)).length < 1e-4
    projected = world_to_camera_view(scene, camera, Vector(target))
    assert abs(projected.x - 0.5) < 0.001 and abs(projected.y - 0.5) < 0.001
    assert (
        abs(data.sensor_width * (Vector(target) - camera.location).length / data.lens - span) < 1e-3
    )
    views[name] = dict(eye=list(eye), target=list(target), span_m=span)
clear = bpy.data.materials["Clear garden transom glass"]
assert abs(clear.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value - 0.25) < 1e-5
used = {m.name for o in scene.objects if o.type == "MESH" for m in o.data.materials}
assert {
    "Clear garden transom glass",
    "Warm grey dressed stone",
    "Oxidised balcony iron",
    "Ivory painted glazing bars",
} <= used
report["ho_tung_garden_portico"] = dict(
    cameras=views,
    fanlight_alpha=0.25,
    used_materials=sorted(used),
    units=scene.unit_settings.system,
    door_configuration=scene["garden_door_configuration"],
)
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
