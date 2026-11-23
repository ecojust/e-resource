"""Frame the Fuxing Lane inscribed balcony."""
import bpy
from pathlib import Path
from mathutils import Vector

@bpy.app.handlers.persistent
def frame_house_entrance(_):
    scene=bpy.context.scene
    scene['Inscription source'] = 'Fu-Xing Fang Shanghai.JPG, Livelikerw, 27 January 2015.'
    scene['Inscription adaptation'] = 'Three painted characters. Perspective-corrected photo traces. CC BY-SA 4.0.'
    scene['Source URL'] = 'https://commons.wikimedia.org/wiki/File:Fu-Xing_Fang_Shanghai.JPG'
    scene['Inscription licence URL'] = 'https://creativecommons.org/licenses/by-sa/4.0/'
    camera=scene.camera
    if not camera:return
    direction=Vector((4.8,-19.5,1.80)).normalized()
    rotation=(-direction).to_track_quat('-Z','Y')
    corners=[rotation.inverted() @ (obj.matrix_world @ Vector(coord))
             for obj in scene.objects if obj.type=='MESH' for coord in obj.bound_box]
    if not corners:return
    lower=Vector([min(corner[i] for corner in corners) for i in range(3)])
    upper=Vector([max(corner[i] for corner in corners) for i in range(3)])
    center=rotation @ ((lower+upper)/2)
    camera.location=center+direction*130
    camera.rotation_euler=rotation.to_euler()
    for light in scene.objects:
        if light.type=='LIGHT' and light.data.type=='SUN':
            light.location=Vector((35,-25,42))
            light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
    camera.name='Fuxing inscribed balcony and louvered bay'
    scene.render.resolution_x=560
    scene.render.resolution_y=680
    camera.data.ortho_scale=1
    frame=camera.data.view_frame(scene=scene)
    unit_width=max(v.x for v in frame)-min(v.x for v in frame)
    unit_height=max(v.y for v in frame)-min(v.y for v in frame)
    camera.data.ortho_scale=1.13*max((upper.x-lower.x)/unit_width,(upper.y-lower.y)/unit_height)
    bpy.context.view_layer.update()
    print('Framed the Fuxing inscribed balcony and louvered bay',scene.render.resolution_x,scene.render.resolution_y,camera.data.ortho_scale)

bpy.app.handlers.save_pre.append(frame_house_entrance)
