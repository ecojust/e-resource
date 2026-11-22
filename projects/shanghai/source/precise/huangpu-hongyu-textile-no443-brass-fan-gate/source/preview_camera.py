"""Frame the actual editable asset from the measured garden-side approach."""
from pathlib import Path
import json
import bpy
from mathutils import Vector

settings = json.loads(Path(__file__).with_name("preview-camera.json").read_bytes())

@bpy.app.handlers.persistent
def frame_component(_):
    scene = bpy.context.scene
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from ornament_rights import CREDIT, PHOTO, LICENSE, GEOMETRY
    scene['geometry_license'] = GEOMETRY
    scene['reference_photo_credit'] = CREDIT
    scene['reference_photo_source'] = PHOTO
    scene['brass_ornament_license'] = LICENSE
    camera = scene.camera
    if camera is None:
        return
    direction = Vector(settings["direction"]).normalized()
    orientation = (-direction).to_track_quat("-Z", "Y")
    projected = [orientation.inverted() @ (obj.matrix_world @ Vector(corner))
                 for obj in scene.objects if obj.type == "MESH" for corner in obj.bound_box]
    if not projected:
        return
    low = Vector([min(point[i] for point in projected) for i in range(3)])
    high = Vector([max(point[i] for point in projected) for i in range(3)])
    center = orientation @ ((low + high) / 2)
    camera.location = center + direction * 40
    camera.rotation_euler = orientation.to_euler()
    camera.name = settings["name"]
    scene.render.resolution_x,scene.render.resolution_y = settings["pixels"]
    for obj in scene.objects:
        if obj.type == "LIGHT" and obj.data.type == "SUN":
            obj.location = Vector((29,-31,49))
            obj.rotation_euler = (-obj.location).to_track_quat("-Z","Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 1
    frustum = camera.data.view_frame(scene=scene)
    width = max(v.x for v in frustum)-min(v.x for v in frustum)
    height = max(v.y for v in frustum)-min(v.y for v in frustum)
    camera.data.ortho_scale = 1.15*max((high.x-low.x)/width,(high.y-low.y)/height)
    bpy.context.view_layer.update()
    print("Framed",camera.name,scene.render.resolution_x,scene.render.resolution_y,camera.data.ortho_scale)

bpy.app.handlers.save_pre.append(frame_component)
