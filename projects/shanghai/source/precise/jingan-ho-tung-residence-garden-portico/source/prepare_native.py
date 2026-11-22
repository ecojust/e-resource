"""Install the garden cameras and save the fanlight material with its transparency."""

from pathlib import Path
import sys
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from native_cameras import MAIN, CAMERAS


@bpy.app.handlers.persistent
def finish_portico(_):
    scene = bpy.context.scene
    for name, (eye, target, span) in CAMERAS.items():
        camera = scene.camera if name == MAIN else bpy.data.objects.get(name)
        if camera is None:
            camera = bpy.data.objects.new(name, bpy.data.cameras.new(name))
            bpy.data.collections["Preview lighting and camera"].objects.link(camera)
        camera.name = camera.data.name = name
        camera.location = eye
        direction = Vector(target) - camera.location
        camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        camera.data.type = "PERSP"
        camera.data.sensor_fit = "HORIZONTAL"
        camera.data.lens = camera.data.sensor_width * direction.length / span
        camera.data.clip_start = 0.05
        camera.data.clip_end = 250
        camera["target_local_m"] = target
    scene.render.resolution_x = 900
    scene.render.resolution_y = 790
    scene.render.resolution_percentage = 100
    mat = bpy.data.materials["Clear garden transom glass"]
    mat.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.25
    mat.diffuse_color = (*mat.diffuse_color[:3], 0.25)
    scene["garden_door_configuration"] = (
        "Central pair open 70 degrees. Recessed upper and outer pairs closed."
    )
    scene["photographic_material"] = "Procedural colours. Garden photos informed the geometry."
    bpy.context.view_layer.update()


bpy.app.handlers.save_pre.append(finish_portico)
