"""Reopen and verify the three ringed windows, balconies, storey limits and nine cameras."""

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
assert scene.camera.name == views[0]["label"] and scene["included_storeys"] == "2, 3, 4"
for view in views:
    cam = bpy.data.objects[view["label"]]
    delta = Vector(view["target"]) - cam.location
    xy = world_to_camera_view(scene, cam, Vector(view["target"]))
    assert (cam.location - Vector(view["eye"])).length < 1e-4
    assert abs(xy.x - 0.5) < 0.001 and abs(xy.y - 0.5) < 0.001
    assert abs(cam.data.sensor_width * delta.length / cam.data.lens - view["width_m"]) < 1e-3
materials = {m.name for o in scene.objects if o.type == "MESH" for m in o.data.materials}
assert {"Buff cast-stone ring", "Deep bronze sash", "Honey buff tile", "Sandy balcony render",
        "Recess glazing", "Dark balcony iron", "Fan vent"} <= materials
for storey in range(2, 5):
    for element in [f"{storey}F street porthole moulded surround", f"{storey}F cantilever solid front parapet",
                    f"{storey}F rear wall glazing", f"{storey}F rear wall opening frame"]:
        assert any(element in obj.name for obj in scene.objects if obj.type == "MESH"), element
report["maoming_three_storey_elevation"] = dict(cameras=views, storeys=[2, 3, 4],
    frontage_axis_degrees=scene["frontage_axis_degrees"], used_materials=sorted(materials))
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
