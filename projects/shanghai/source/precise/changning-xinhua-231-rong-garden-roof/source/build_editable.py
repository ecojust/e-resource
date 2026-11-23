"""Write the editable project, verify a fresh open, or round-trip an exchange role."""
import argparse
import base64
import collections
import hashlib
import json
import math
from pathlib import Path
import sys
import bpy
from mathutils import Vector

def digest(blob):
    return hashlib.sha256(blob).hexdigest()

def mesh_objects():
    return [o for o in bpy.context.scene.objects if o.type == 'MESH']

def geometry_signature(objects):
    triangles = []
    for obj in objects:
        mesh = obj.data
        mesh.calc_loop_triangles()
        points = [tuple(round(x,4) + 0. for x in obj.matrix_world @ v.co) for v in mesh.vertices]
        for tri in mesh.loop_triangles:
            c = tuple(points[i] for i in tri.vertices)
            triangles.append(min(c, c[1:]+c[:1], c[2:]+c[:2]))
    data = json.dumps(sorted(triangles), separators=(',',':')).encode()
    return dict(triangles=len(triangles), oriented_positions_sha256=digest(data))

def write_scene(package, blend_path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    model = bpy.data.collections.new('Residence exterior')
    bpy.context.scene.collection.children.link(model)
    materials = {}
    for name, spec in package['materials'].items():
        mat = bpy.data.materials.new(name)
        mat.diffuse_color = (*spec['color'],1.)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get('Principled BSDF')
        bsdf.inputs['Base Color'].default_value = (*spec['color'],1.)
        bsdf.inputs['Roughness'].default_value = spec['roughness']
        if texname:=spec.get('texture'):
            p = blend_path.parent/texname
            content = base64.b64decode(package['textures'][texname])
            p.write_bytes(content)
            img = bpy.data.images.load(str(p)); img.name=texname
            img.pack()
            img.filepath = '//'+texname
            node=mat.node_tree.nodes.new('ShaderNodeTexImage')
            node.image=img; node.extension='REPEAT'
            mat.node_tree.links.new(node.outputs['Color'],bsdf.inputs['Base Color'])
        materials[name]=mat
    for i,part in enumerate(package['parts']):
        name=f"{i+1:03d} {part['label']}"
        mesh=bpy.data.meshes.new(name)
        mesh.from_pydata(part['vertices'],[],part['triangles']);mesh.update()
        obj=bpy.data.objects.new(name,mesh);model.objects.link(obj)
        obj['architectural_label']=part['label']
        obj['index_in_source']=i
        mesh.materials.append(materials[part['material']])
        if uvs:=part.get('texcoords'):
            layer=mesh.uv_layers.new(name='Building UV')
            for loop, item in zip(mesh.loops,layer.data):
                u,v=uvs[loop.vertex_index]
                item.uv=(u,1.-v)
    for view in package['metadata']['camera_views']:
        camera=bpy.data.cameras.new(view['name'])
        obj=bpy.data.objects.new(view['label'],camera);bpy.context.scene.collection.objects.link(obj)
        obj.location=view['eye'];obj.rotation_euler=(Vector(view['target'])-obj.location).to_track_quat('-Z','Y').to_euler()
        camera.angle=math.radians(view['fov'])
        if not bpy.context.scene.camera:bpy.context.scene.camera=obj
    bpy.context.scene['model_id']=package['metadata']['id']
    bpy.context.scene['reference_sha256']=package['reference_sha256']
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path),compress=True)

def verify_scene(package):
    objects = mesh_objects()
    expected=package['parts']
    assert len(objects)==len(expected) and {o['index_in_source'] for o in objects}==set(range(len(expected)))
    uv_corners=0
    for obj in objects:
        part=expected[obj['index_in_source']]
        assert obj['architectural_label']==part['label']
        mesh=obj.data
        assert len(mesh.vertices)==len(part['vertices']) and len(mesh.polygons)==len(part['triangles'])
        assert mesh.materials[0].name==part['material']
        for vertex,p in zip(mesh.vertices,part['vertices']):
            assert max(abs(a-b) for a,b in zip(vertex.co,p))<2e-5
        for face,p in zip(mesh.polygons,part['triangles']):
            assert list(face.vertices)==list(p)
        if uvs:=part.get('texcoords'):
            for loop, item in zip(mesh.loops,mesh.uv_layers.active.data):
                u,v=uvs[loop.vertex_index]
                assert abs(item.uv.x-u)<2e-5 and abs(item.uv.y-(1.-v))<2e-5
                uv_corners+=1
    textures={im.name:digest(bytes(im.packed_file.data)) for im in bpy.data.images if im.packed_file}
    assert textures=={name:digest(base64.b64decode(data)) for name,data in package['textures'].items()}
    views=package['metadata']['camera_views']
    cams={o.name:o for o in bpy.context.scene.objects if o.type=='CAMERA'}
    assert list(sorted(cams))==sorted(v['label'] for v in views)
    for v in views:
        c=cams[v['label']]
        assert (c.location-Vector(v['eye'])).length<1e-5
        assert abs(c.data.angle-math.radians(v['fov']))<1e-5
        axis=(c.matrix_world.to_quaternion()@Vector([0,0,-1])).normalized()
        assert axis.dot((Vector(v['target'])-c.location).normalized())>.99999
    return dict(parts=len(objects),cameras=len(cams),textures=textures,uv_corners=uv_corners,**geometry_signature(objects))

def exchange(path,role):
    obj=mesh_objects()
    for o in bpy.context.scene.objects:o.select_set(o in obj)
    if role=='fbx':
        bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH'},path_mode='COPY',embed_textures=True,add_leaf_bones=False)
    elif role=='obj':
        bpy.ops.wm.obj_export(filepath=str(path),export_selected_objects=True,export_materials=True,export_uv=True,path_mode='COPY')
    else:bpy.ops.wm.stl_export(filepath=str(path),export_selected_objects=True)
    expected=geometry_signature(obj)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if role=='fbx':bpy.ops.import_scene.fbx(filepath=str(path))
    elif role=='obj':bpy.ops.wm.obj_import(filepath=str(path))
    else:bpy.ops.wm.stl_import(filepath=str(path))
    result=geometry_signature(mesh_objects())
    assert result==expected,(role, result, expected)
    return dict(role=role,bytes=path.stat().st_size,sha256=digest(path.read_bytes()),reimported_objects=len(mesh_objects()),**result)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('phase',choices=['make','verify','fbx','obj','stl'])
    p.add_argument('components',type=Path);p.add_argument('output',type=Path);p.add_argument('report',type=Path)
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.output.parent.mkdir(exist_ok=True,parents=True)
    package=json.loads(a.components.read_bytes())
    if a.phase=='make':
        write_scene(package,a.output);result=verify_scene(package)
    elif a.phase=='verify':
        result=verify_scene(package)
    else:
        result=exchange(a.output,a.phase)
    a.report.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
if __name__=='__main__':main()
