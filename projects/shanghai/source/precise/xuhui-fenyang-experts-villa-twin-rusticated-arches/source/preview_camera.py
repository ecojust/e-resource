"""Fit the paired arcade in a garden-side view before saving the editable model."""
import bpy
from mathutils import Vector

@bpy.app.handlers.persistent
def set_preview(_):
    scene = bpy.context.scene
    camera = scene.camera
    focus = Vector((0, 0.10, 1.89))
    camera.name = 'Garden side of paired arches'
    camera.location = focus + Vector((2.2, -10.8, 0.92))
    camera.rotation_euler = (focus - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = 6.72
    scene.render.resolution_x = 880
    scene.render.resolution_y = 680
    scene['source_view'] = 'Two open masonry arches and their shared pier facing the garden.'

bpy.app.handlers.save_pre.append(set_preview)
