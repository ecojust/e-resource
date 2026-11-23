"""Reopen and verify the editable gate, four name characters and the eight camera targets."""

from pathlib import Path
import json, sys
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

blend, raw, output = map(Path, sys.argv[sys.argv.index("--") + 1 :])
scene = bpy.context.scene
report = json.loads(output.read_bytes())
assert report["match_raw"] and Path(bpy.data.filepath).resolve() == blend.resolve()
views = json.loads(Path(__file__).with_name("cameras.json").read_bytes())
assert scene.camera.name == views[0]["label"] and scene["name_relief"] == "康綏公寓"
for view in views:
    cam = bpy.data.objects[view["label"]]
    delta = Vector(view["target"]) - cam.location
    xy = world_to_camera_view(scene, cam, Vector(view["target"]))
    assert (cam.location - Vector(view["eye"])).length < 1e-4
    assert abs(xy.x - 0.5) < 0.001 and abs(xy.y - 0.5) < 0.001
    assert abs(cam.data.sensor_width * delta.length / cam.data.lens - view["width_m"]) < 1e-3
materials = {m.name for o in scene.objects if o.type == "MESH" for m in o.data.materials}
assert {
    "Oxide red name characters",
    "Grey-green inset inscription field",
    "Weathered red face brick",
    "Blackened iron gate",
    "Grey concrete walking surface",
} <= materials
report["cozy_lane_portal"] = {
    "cameras": views,
    "name": scene["name_relief"],
    "used_materials": sorted(materials),
    "gate_configuration": scene["street_gate_configuration"],
}
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
