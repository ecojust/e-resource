"""Install editable inspection cameras looking into the passage and back towards the street."""

from pathlib import Path
import json
import bpy
from mathutils import Vector

VIEWS = json.loads((Path(__file__).with_name("cameras.json")).read_bytes())


@bpy.app.handlers.persistent
def install_lane_cameras(_):
    scene = bpy.context.scene
    for i, view in enumerate(VIEWS):
        name = view["label"]
        camera = scene.camera if i == 0 else bpy.data.objects.get(name)
        if camera is None:
            camera = bpy.data.objects.new(name, bpy.data.cameras.new(name))
            bpy.data.collections["Preview lighting and camera"].objects.link(camera)
        camera.name = camera.data.name = name
        camera.location = view["eye"]
        delta = Vector(view["target"]) - camera.location
        camera.rotation_euler = delta.to_track_quat("-Z", "Y").to_euler()
        camera.data.type = "PERSP"
        camera.data.sensor_fit = "HORIZONTAL"
        camera.data.lens = camera.data.sensor_width * delta.length / view["width_m"]
        camera.data.clip_start = 0.025
        camera.data.clip_end = 180
        camera["target_local_m"] = view["target"]
    scene.render.resolution_x = VIEWS[0]["width"]
    scene.render.resolution_y = VIEWS[0]["height"]
    scene.render.resolution_percentage = 100
    scene["street_gate_configuration"] = (
        "Two separate iron leaves turn into the passage, approximating the 2022 district photograph."
    )
    scene["name_relief"] = "康綏公寓"
    bpy.context.view_layer.update()


bpy.app.handlers.save_pre.append(install_lane_cameras)
