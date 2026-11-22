"""Install the street and detail cameras before saving the editable Blender scene."""
import json
import os
import sys
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from native_layout import ALIASES, CAMERAS, MAIN

@bpy.app.handlers.persistent
def frame_bank(*_):
    scene=bpy.context.scene
    reverse={short:long for long,short in ALIASES.items()}
    for obj in scene.objects:
        if obj.type=='MESH':
            obj['source_component']=reverse.get(obj.name,obj.name)
    stage=bpy.data.collections['Preview lighting and camera']
    for name,(eye,target,scale) in CAMERAS.items():
        camera=scene.camera if name==MAIN else bpy.data.objects.get(name)
        if camera is None:
            camera=bpy.data.objects.new(name,bpy.data.cameras.new(name))
            stage.objects.link(camera)
        camera.name=camera.data.name=name
        camera.location=Vector(eye)
        camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.type='ORTHO'
        camera.data.ortho_scale=scale
        camera.data.clip_start=.05
        camera.data.clip_end=300
        camera['aim_local_m']=target
    scene.render.resolution_x=720
    scene.render.resolution_y=900
    scene.render.resolution_percentage=100
    sun=next(obj for obj in scene.objects if obj.type=='LIGHT' and obj.data.type=='SUN')
    sun.location=Vector((-11,-22,29))
    sun.rotation_euler=(Vector((0,0,9.6))-sun.location).to_track_quat('-Z','Y').to_euler()
    rights=json.loads(os.environ['NANSHI_BANK_RIGHTS_JSON'])
    scene['geometry_license']=rights['geometry_license']
    scene['copyright']=rights['copyright']
    artwork,=rights['third_party_materials']
    scene['relief_source_url']=artwork['url']
    scene['relief_license_url']=artwork['license_url']
    scene['relief_changes']=artwork['modifications']
    scene['modelled_street_state']='Gilt street sign from 2015. Closed ground-floor panels from January 2021.'

bpy.app.handlers.save_pre.append(frame_bank)
