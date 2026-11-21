"""Frame the off-centre curved elevation in the saved scene and native rendering."""
import bpy
from mathutils import Vector


@bpy.app.handlers.persistent
def frame_street_elevation(*_):
    scene = bpy.context.scene
    camera = scene.camera
    if camera is None:
        return
    buildings = [ob for ob in scene.objects if ob.type == 'MESH']
    bounds = [ob.matrix_world @ Vector(corner) for ob in buildings for corner in ob.bound_box]
    target = Vector(tuple((min(p[i] for p in bounds) + max(p[i] for p in bounds)) / 2
                          for i in range(3)))
    camera.name = "Huaihai Road elevation and east bend"
    direction = Vector((-.25, -1, .12)).normalized()
    camera.location = target + direction * 205
    camera.rotation_euler = (-direction).to_track_quat('-Z', 'Y').to_euler()
    basis = camera.rotation_euler.to_matrix().transposed()
    projected = [basis @ (point-target) for point in bounds]
    ratio = scene.render.resolution_x / scene.render.resolution_y
    camera.data.ortho_scale = max(max(p.x for p in projected)-min(p.x for p in projected),
                                  (max(p.y for p in projected)-min(p.y for p in projected))*ratio) * 1.10


bpy.app.handlers.save_pre.append(frame_street_elevation)
